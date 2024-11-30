import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    RDS_HOSTNAME = os.getenv("RDS_HOSTNAME", "realestatedb-instance.cj7aonteiqdm.us-east-1.rds.amazonaws.com")
    RDS_USERNAME = os.getenv("RDS_USERNAME", "admin")
    RDS_PASSWORD = os.getenv("RDS_PASSWORD", "adminpassword12345")
    RDS_DATABASE = os.getenv("RDS_DATABASE", "realestatedatabase")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")  # Flask session secret key
   
 # Flask session secret key

    AWS_ACCESS_KEY = os.getenv('ASIA3JJSGQGTUNJU')
    AWS_SECRET_ACCESS_KEY = os.getenv('QXdafxRzMRRnT3rrN8zN1W888En3m6wVwu59HMo8')
    AWS_SESSION_TOKEN=("IQoJb3JpZ2luX2VjEOH//////////wEaCXVzLXdlc3QtMiJHMEUCIE5NKty09SUCnhLrdn4jCS2vF9QkG1Bt9oqh68srwQomAiEAy6i2MOvG+KYW+jft8m+z5djpjdAxMEW7jIQ5v1mDibYqvQIIiv//////////ARAAGgw3NzU4ODM3NTE4NDciDA05qIckSkDlfVllJCqRAi7v/R+SV4FK4QmMJ8Bfl8DcL+kSGZYSZPDP0DkpSAvq0/4zhFIS6r1lAdUxOCz4FOH9jEGyqkW2s5tF7LJ8Qe0c5xn7WWGg1rJAUvPRhUp6MdGHkU1+n4a8o8GDsaADV4z1u1njv8yCs/yl3zGq1LWo1Uu/GyPMIed3tRygRJILNWxrDEajrxf6KLUZf6ebV++5d9XLjYnfQvgpoq9EN+0P3HKSHb+yYBu+9LmcPUCVWQEB08/Df26iJJW/ynTsfn6WcaTVtECRdK1Sfq1359iwDyihdHd84g1CX0Q+x5BwWUEa33AtC8ia+ccVs2DNTpyTjscsl0hRY/56vUm60rjAvfPtDmnC4S3mYnQ6owBEjjCcp6u6BjqdAQ1squ5m3X24WANjGEkxkvvKxjpyDiQuVRifFFjHXG5ZR4YaRFD0OcTdY27dhs6RpwMhsGBiTAKhGlj/ysKJFva5jEmTquMAXFgQu9rC/EAgPXvqLS6n6C7dnpDTF0yS54AsuwoaooNwvFDy2DnCuejJ2t3R+HiPwFMwrI5ueaQFupcDP3TEaqZmukEpC2R1nfEcozWgQgIYDHF/zbg=")
    AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME', 'realestate23270152')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1') 
    AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID','775883751847')
 
    # Add RDS instance configuration
    DB_INSTANCE_IDENTIFIER = os.getenv("DB_INSTANCE_IDENTIFIER", "realestatedb-instance")  # Default name if not set
    MASTER_USERNAME = os.getenv("MASTER_USERNAME", "admin")  # Default username if not set
    MASTER_PASSWORD = os.getenv("MASTER_PASSWORD", "adminpassword12345")  # Default password if not set
    
print(os.environ.get('AWS_DEFAULT_REGION'))
# To use in your Flask app
config = Config()
