import os

class Config:
    RDS_HOSTNAME = os.getenv("RDS_HOSTNAME", "realestatedb-instance.cj7aonteiqdm.us-east-1.rds.amazonaws.com")
    RDS_USERNAME = os.getenv("RDS_USERNAME", "admin")
    RDS_PASSWORD = os.getenv("RDS_PASSWORD", "adminpassword12345")
    RDS_DATABASE = os.getenv("RDS_DATABASE", "realestatedatabase")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")  # Flask session secret key
   
 # Flask session secret key

    AWS_ACCESS_KEY = os.getenv('ASIA3JJSGQGT6FDO4SFK')
    AWS_SECRET_KEY = os.getenv('O3KUMmMvKcPpZn/3lhGvvAARskorCrDZWYzSre23')
    AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME', 'realestate23270152')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1') 
    AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID','775883751847')
 
    # Add RDS instance configuration
    DB_INSTANCE_IDENTIFIER = os.getenv("DB_INSTANCE_IDENTIFIER", "realestatedb-instance")  # Default name if not set
    MASTER_USERNAME = os.getenv("MASTER_USERNAME", "admin")  # Default username if not set
    MASTER_PASSWORD = os.getenv("MASTER_PASSWORD", "adminpassword12345")  # Default password if not set
    

# To use in your Flask app
config = Config()
