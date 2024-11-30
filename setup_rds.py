import os
import boto3

def check_rds_instance_exists(db_instance_identifier):
    rds_client = boto3.client('rds', region_name=os.getenv('AWS_REGION'))
    try:
        response = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
        if response['DBInstances']:
            print(f"RDS instance '{db_instance_identifier}' already exists.")
            return True
    except rds_client.exceptions.DBInstanceNotFoundFault:
        return False
    except Exception as e:
        print(f"Error checking RDS instance: {e}")
        return False

def create_rds_instance(db_instance_identifier, master_username, master_password):
    rds_client = boto3.client('rds', region_name=os.getenv('AWS_REGION'))
    
    if check_rds_instance_exists(db_instance_identifier):
        return True  # Skip creation if instance already exists

    try:
        print("Creating RDS instance...")
        response = rds_client.create_db_instance(
            DBName='realestatedatabase',
            DBInstanceIdentifier=db_instance_identifier,
            AllocatedStorage=20,  # Storage in GB
            DBInstanceClass='db.t3.micro',  # Free tier instance type
            Engine='mysql',  # Database engine
            MasterUsername=master_username,
            MasterUserPassword=master_password,
            VpcSecurityGroupIds=['sg-0cf69b0a85db2ffa5'],  # Replace with your security group ID if needed
            BackupRetentionPeriod=7,  # Backup retention in days
            Port=3306,  # Default MySQL port
            PubliclyAccessible=True  # Set to False for private access
        )
        print(f"RDS instance creation response: {response}")
        print("RDS instance creation initiated. Waiting for completion...")

        # Wait until the DB instance is available
        waiter = rds_client.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier=db_instance_identifier)
        print(f"rds_client::{rds_client}")
        # Fetch the instance details
        db_instance = rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
        print(f"db_instance::{db_instance}")
        endpoint = db_instance['DBInstances'][0]['Endpoint']['Address']
        print(f"RDS instance created successfully. Endpoint: {endpoint}")
        
        return endpoint

    except Exception as e:
        print(f"Error creating RDS instance: {e}")
        return None
