import boto3
import zipfile
from config import Config  # Importing config class from config.py
from botocore.exceptions import ClientError
import pymysql

# Initialize Boto3 clients
lambda_client = boto3.client('lambda', aws_access_key_id=Config.AWS_ACCESS_KEY, aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY, region_name=Config.AWS_REGION)
s3_client = boto3.client('s3', aws_access_key_id=Config.AWS_ACCESS_KEY, aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY, region_name=Config.AWS_REGION)
iam_client = boto3.client('iam', aws_access_key_id=Config.AWS_ACCESS_KEY, aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY, region_name=Config.AWS_REGION)
rekognition_client = boto3.client('rekognition', aws_access_key_id=Config.AWS_ACCESS_KEY, aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY, region_name=Config.AWS_REGION)

# Constants
bucket_name = Config.AWS_BUCKET_NAME
s3_prefix = 'properties/1/'
lambda_role = 'LabRole'  # Using the existing LabRole as provided by your college
lambda_function_name = 'ImagePropertyValidator'

# Step 1: Create Lambda function zip file with the code
def create_lambda_zip():
    lambda_code = """
import json
import boto3
from botocore.exceptions import ClientError

rekognition_client = boto3.client('rekognition')
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    try:
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        file_name = event['Records'][0]['s3']['object']['key']
        
        response = rekognition_client.detect_labels(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': file_name}},
            MaxLabels=10,
            MinConfidence=75
        )
        
        labels = response['Labels']
        property_related = False
        
        for label in labels:
            if 'House' in label['Name'] or 'Building' in label['Name']:
                property_related = True
                break
        
        if property_related:
            print(f"Image {file_name} is property-related.")
        else:
            print(f"Image {file_name} is not property-related, deleting it.")
            s3_client.delete_object(Bucket=bucket_name, Key=file_name)
    
    except ClientError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
    """
    
    with open('/tmp/lambda_function.py', 'w') as f:
        f.write(lambda_code)
    
    zipfile_name = '/tmp/lambda_function.zip'
    with zipfile.ZipFile(zipfile_name, 'w') as zipf:
        zipf.write('/tmp/lambda_function.py', 'lambda_function.py')

    return zipfile_name

# Step 2: Create or check Lambda function
def create_lambda_function():
    try:
        lambda_client.get_function(FunctionName=lambda_function_name)
        print(f"Lambda function '{lambda_function_name}' already exists.")
    except lambda_client.exceptions.ResourceNotFoundException:
        zipfile_name = create_lambda_zip()
        with open(zipfile_name, 'rb') as f:
            lambda_client.create_function(
                FunctionName=lambda_function_name,
                Runtime='python3.8',
                Role=f'arn:aws:iam::{Config.AWS_ACCOUNT_ID}:role/{lambda_role}',  # Using the existing LabRole
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': f.read()},
                Timeout=15,
                MemorySize=128,
            )
        print(f"Lambda function '{lambda_function_name}' created successfully.")
        
# Grant S3 permissions to invoke the Lambda function
def add_lambda_permission_for_s3():
    try:
        lambda_client.add_permission(
            FunctionName=lambda_function_name,
            StatementId='S3InvokePermission',  # Unique identifier for the permission
            Action='lambda:InvokeFunction',
            Principal='s3.amazonaws.com',
            SourceArn=f'arn:aws:s3:::{bucket_name}',
            SourceAccount=Config.AWS_ACCOUNT_ID
        )
        print(f"Permission granted for S3 to invoke Lambda function '{lambda_function_name}'.")
    except lambda_client.exceptions.ResourceConflictException:
        print(f"Permission for S3 to invoke Lambda function '{lambda_function_name}' already exists.")


# Step 3: Set or check S3 event notification
def set_s3_event_notification():
    response = s3_client.get_bucket_notification_configuration(Bucket=bucket_name)
    for config in response.get('LambdaFunctionConfigurations', []):
        if config.get('LambdaFunctionArn') == f'arn:aws:lambda:{Config.AWS_REGION}:{Config.AWS_ACCOUNT_ID}:function:{lambda_function_name}':
            print(f"S3 event notification for Lambda function '{lambda_function_name}' already exists.")
            return
    s3_client.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration={
            'LambdaFunctionConfigurations': [
                {
                    'LambdaFunctionArn': f'arn:aws:lambda:{Config.AWS_REGION}:{Config.AWS_ACCOUNT_ID}:function:{lambda_function_name}',
                    'Events': ['s3:ObjectCreated:*'],
                    'Filter': {
                        'Key': {
                            'FilterRules': [
                                {'Name': 'prefix', 'Value': s3_prefix}
                            ]
                        }
                    }
                }
            ]
        }
    )
    print(f"S3 event notification for '{s3_prefix}' created successfully.")

# Database configuration function
def get_db():
    try:
        conn = pymysql.connect(
            host=Config.RDS_HOSTNAME,
            user=Config.RDS_USERNAME,
            password=Config.RDS_PASSWORD,
            database=Config.RDS_DATABASE,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Database connection established.")
        return conn
    except pymysql.MySQLError as e:
        print(f"Database connection error: {e}")
        raise

def lambda_handler(event,context):
    # Extract bucket name and image key from the S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    property_id = key.split('/')[1]  # Assuming key structure 'properties/{property_id}/image.jpg'

    try:
        # Use Rekognition to detect labels in the image
        response = rekognition_client.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            MaxLabels=10,
            MinConfidence=75  # Set a confidence threshold
        )

        labels = response['Labels']
        print(f"Detected labels for {key}: {labels}")

        # Property-related labels to look for
        property_related_labels = ["House", "Building", "Property", "Real Estate"]
        label_names = [label['Name'] for label in labels]

        # Check if any property-related label is detected
        if any(label in label_names for label in property_related_labels):
            print(f"Image {key} is property-related.")
        else:
            # If the image is not property-related, delete it and the associated property data
            print(f"Image {key} is not property-related, deleting it.")

            # Step 1: Delete the image from S3
            s3_client.delete_object(Bucket=bucket, Key=key)

            # Step 2: Delete the property data from RDS (MySQL)
            delete_property_from_db(property_id)

    except ClientError as e:
        print(f"Error processing the image: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

def delete_property_from_db(property_id):
    """
    Deletes the property from the RDS database based on the property_id.
    """
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Delete the property from the database
            cursor.execute('''
                DELETE FROM properties WHERE id = %s
            ''', (property_id,))
            conn.commit()
            print(f"Property with ID {property_id} deleted successfully.")
    except pymysql.MySQLError as e:
        print(f"Error deleting property from database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

