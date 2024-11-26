import boto3
from botocore.exceptions import ClientError
from config import Config

def create_s3_bucket(bucket_name, region=Config.AWS_REGION):
    """
    Function to create an S3 bucket programmatically with public read and write access.
    :param bucket_name: Name of the S3 bucket to create.
    :param region: AWS region in which to create the S3 bucket.
    :return: The URL of the created bucket or an error message.
    """
    try:
        # Create a session using the specified region
        s3_client = boto3.client('s3', region_name=region,
                                 aws_access_key_id=Config.AWS_ACCESS_KEY,
                                 aws_secret_access_key=Config.AWS_SECRET_KEY)
        
        # Check if the bucket already exists
        existing_buckets = s3_client.list_buckets()
        for bucket in existing_buckets['Buckets']:
            if bucket['Name'] == bucket_name:
                print(f"Bucket {bucket_name} already exists.")
                return f"Bucket {bucket_name} already exists."

        # Create the bucket
        if region == "us-east-1":
            s3_client.create_bucket(Bucket=bucket_name)  # Standard region doesn't require location constraint
        else:
            s3_client.create_bucket(Bucket=bucket_name,
                                    CreateBucketConfiguration={'LocationConstraint': region})

        # Disable Block Public Access
        s3_client.put_bucket_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        )

        # Verify Block Public Access is disabled
        response = s3_client.get_bucket_public_access_block(Bucket=bucket_name)
        print(f"Public Access Block Settings: {response['PublicAccessBlockConfiguration']}")

        # Set public-read-write ACL for the bucket
        s3_client.put_bucket_acl(
            Bucket=bucket_name,
            ACL='public-read-write'  # Allow public read and write access
        )

        print(f"Bucket {bucket_name} created successfully in region {region}, with public read-write access.")
        return f"Bucket {bucket_name} created successfully in region {region}, with public read-write access."

    except ClientError as e:
        print(f"Error creating bucket: {e}")
        return f"Error creating bucket: {e}"
