import uuid
import boto3
from botocore.exceptions import NoCredentialsError
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import pymysql
from config import Config
from flask_login import UserMixin

# Database configuration function
def get_db():
    """
    Establishes and returns a database connection.
    """
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
# AWS S3 Configuration
s3_client = boto3.client(
    's3',
    aws_access_key_id=Config.AWS_ACCESS_KEY,
    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
    region_name=Config.AWS_REGION
)

def upload_to_s3(file, user_id):
    """
    Uploads a file to AWS S3 and returns its public URL.
    """
    print("filetype:::", type(file))
    print("file::::", file)
    print(file.filename)
    if not isinstance(file, FileStorage):
        raise ValueError("Invalid file object passed to upload_to_s3. Expected FileStorage.")

    try:
        # Secure the filename and generate a unique key
        filename = secure_filename(file.filename)
        file_key = f'properties/{user_id}/{filename}'

        # Upload the file to S3 with public read and write access
        s3_client.upload_fileobj(
            file,
            Config.AWS_BUCKET_NAME,
            file_key,
            ExtraArgs={
                'ContentType': file.content_type,  # Ensure correct content type
                'ACL': 'public-read-write'  # Ensure public read and write access
            }
        )

        # Generate the public URL for the uploaded file
        file_url = f"https://{Config.AWS_BUCKET_NAME}.s3.{Config.AWS_REGION}.amazonaws.com/{file_key}"
        print(f"File uploaded to S3: {file_url}")
        
        return file_url
    except NoCredentialsError:
        print("AWS credentials not available.")
        raise
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        raise

    
def create_property_in_db(location, price, size, facilities, user_id, photo_url):
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Generate a unique property ID
            property_id = str(uuid.uuid4())[:8]  # Shortened UUID for readability
            cursor.execute('''
                INSERT INTO properties (property_id, location, price, size, facilities, owner_id, photo_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (property_id, location, price, size, ', '.join(facilities), user_id, photo_url))
            conn.commit()
            print(f"Property added successfully: {property_id}, {location}, {price}, {size}, {facilities}, {photo_url}")
    except pymysql.MySQLError as e:
        print(f"Error adding property to database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()






def create_tables():
    """
    Creates necessary database tables if they don't already exist.
    """
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    first_name VARCHAR(255) NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    user_type VARCHAR(50) DEFAULT 'buyer' -- Added user_type field with default 'buyer'
                )
            ''')

            # Create properties table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS properties (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    property_id VARCHAR(255) NOT NULL UNIQUE,
                    location VARCHAR(255),
                    price DECIMAL(10, 2),
                    size VARCHAR(50),
                    facilities TEXT,
                    owner_id INT,
                    photo_url VARCHAR(255),
                    FOREIGN KEY(owner_id) REFERENCES users(id)
                )
            ''')


        conn.commit()
        print("Tables created successfully.")
    except pymysql.MySQLError as e:
        print(f"Error creating tables: {e}")
    finally:
        conn.close()

class User(UserMixin):
    """
    User model for Flask-Login integration.
    """
    def __init__(self, id, email, first_name, password, user_type='buyer'):
        self.id = id
        self.email = email
        self.first_name = first_name
        self.password = password
        self.user_type = user_type

    @classmethod
    def get(cls, user_id):
        """
        Retrieves a user by ID.
        """
        conn = get_db()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
                user_data = cursor.fetchone()
                if user_data:
                    return cls(user_data['id'], user_data['email'], user_data['first_name'],
                               user_data['password'], user_data['user_type'])
                return None
        except pymysql.MySQLError as e:
            print(f"Error fetching user: {e}")
            return None
        finally:
            conn.close()

def query_user_by_id(user_id):
    """
    Fetches a user by their ID.
    """
    return User.get(user_id)
