from flask import Flask, render_template, redirect, url_for, request, flash, session
from models import get_db, User, create_tables, create_property_in_db, upload_to_s3
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from setup_rds import create_rds_instance
from flask_cors import CORS
from setup_s3 import create_s3_bucket
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from setup_lambda import create_lambda_function, set_s3_event_notification,add_lambda_permission_for_s3
from property_ranker_lib import filter_by_location, rank_by_price
from setup_sns import create_sns_topic, subscribe_to_topic, send_interest_notification
import logging

from dotenv import load_dotenv

load_dotenv()
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')




app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for development environment
CORS(app, resources={r"/*": {"origins": "*"}})

app.secret_key = Config.SECRET_KEY  # Use secret key from config.py

# Initialize RDS instance on app startup
@app.before_request
def initialize_rds_on_startup():
    endpoint = create_rds_instance(Config.DB_INSTANCE_IDENTIFIER, Config.MASTER_USERNAME, Config.MASTER_PASSWORD)
    create_tables()
    if endpoint:
        print(f"RDS instance available at: {endpoint}")
    else:
        print("Failed to create or connect to RDS instance.")
        
    

# Create the S3 bucket if it doesn't exist
@app.before_request
def initialize_s3_on_startup():
    bucket_name = Config.AWS_BUCKET_NAME
    print(f"Creating S3 bucket: {bucket_name}")
    result = create_s3_bucket(bucket_name)
    print(result)
    # Set up Lambda, S3 event notification, and Rekognition permissions
    create_lambda_function()
    add_lambda_permission_for_s3()
    set_s3_event_notification()
    sns_topic_arn = create_sns_topic("PropertyInterestTopic")  
    # Store the topic ARN for later use in publishing/subscribing
    session['sns_topic_arn'] = sns_topic_arn

# Setup Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Index route
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return render_template('index.html')

  # Import the query_properties function

# Home route for Buyers
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    user_type = current_user.user_type
    selected_location = request.args.get('location', '')

    if user_type == 'buyer' and request.method == 'GET':
        conn = get_db()
        try:
            with conn.cursor() as cursor:
                # Fetch all properties
                cursor.execute("SELECT * FROM properties")
                properties = cursor.fetchall()

                # Filter properties by selected location using the library function
                properties = filter_by_location(properties, selected_location)

                # Sort properties by price using the library function
                properties = rank_by_price(properties)

                # Get unique locations for the filter dropdown
                cursor.execute("SELECT DISTINCT location FROM properties")
                unique_locations = [row['location'] for row in cursor.fetchall()]
        except Exception as e:
            flash(f"Error fetching properties: {e}", category='error')
            properties = []
            unique_locations = []

        return render_template(
            'property_list.html',
            properties=properties,
            unique_locations=unique_locations,
            selected_location=selected_location
        )
    return render_template('home.html', user_type=user_type)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
                user_data = cursor.fetchone()

                if user_data:
                    user = User(user_data['id'], user_data['email'], user_data['first_name'], user_data['password'], user_data['user_type'])
                    if check_password_hash(user.password, password):
                        login_user(user)
                        return redirect(url_for('home'))
                    else:
                        flash('Invalid password.', category='error')
                else:
                    flash('Email not found.', category='error')
        except Exception as e:
            flash(f"An error occurred: {e}", category='error')
        finally:
            conn.close()
    return render_template('login.html')

# Signup route
@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        user_type = request.form.get('user_type')

        if password1 != password2:
            flash('Passwords do not match.', category='error')
            return render_template('sign_up.html')

        conn = get_db()
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
                if cursor.fetchone():
                    flash('Email already exists.', category='error')
                else:
                    hashed_password = generate_password_hash(password1, method='pbkdf2:sha256')
                    cursor.execute('INSERT INTO users (email, first_name, password, user_type) VALUES (%s, %s, %s, %s)',
                                   (email, first_name, hashed_password, user_type))
                    conn.commit()
                    flash('Account created successfully!', category='success')
                    return redirect(url_for('login'))
        except Exception as e:
            flash(f"An error occurred: {e}", category='error')
        finally:
            conn.close()
    return render_template('sign_up.html')

@app.route('/add_property', methods=['GET', 'POST'])
@login_required
def add_property():
    print("User type:", current_user.user_type)
    if current_user.user_type != 'seller':
        flash('Only sellers can add properties.', category='error')
        return redirect(url_for('home'))

    if request.method == 'POST':
        location = request.form.get('location')
        price = request.form.get('price')
        size = request.form.get('size')
        facilities = request.form.getlist('facilities')
        photo = request.files.get('photo')

        print("Received data:")
        print("Location:", location)
        print("Price:", price)
        print("Size:", size)
        print("Facilities:", facilities)
        print("Photo:", photo)

        try:
            if not validate_file(photo):
                flash("Invalid file. Please upload a valid image.", category='error')
                return redirect(url_for('add_property'))

            # Secure the filename and upload to S3
            photo_filename = secure_filename(photo.filename)
            print("Photo filename:", photo_filename)
            photo_url = upload_to_s3(photo, current_user.id)
            print("Uploaded photo URL:", photo_url)

            # Create the property record
            create_property_in_db(location, price, size, facilities, current_user.id, photo_url)
            flash('Property added successfully!', category='success')
            # Subscribe seller to SNS topic (after adding property)
            sns_topic_arn = session.get('sns_topic_arn')  # Get the SNS topic ARN from session
            if sns_topic_arn:
                subscribe_to_topic(sns_topic_arn, current_user.email)
            return redirect(url_for('view_properties'))
        except Exception as e:
            print(f"Error while adding property: {e}")
            flash(f"An error occurred: {e}", category='error')

    return render_template('add_property.html')


# File validation helper function
def validate_file(file):
    """
    Validates the uploaded file for type and format.
    """
    if not file or not isinstance(file, FileStorage):
        print("Invalid file type. Expected FileStorage.")
        return False

    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
    file_ext = file.filename.rsplit('.', 1)[-1].lower()
    if file_ext not in allowed_extensions:
        print(f"Invalid file extension: {file_ext}")
        return False

    return True
     

@app.route('/express_interest/<property_id>', methods=['POST'])
@login_required
def express_interest(property_id):
    if current_user.user_type != 'buyer':
        flash('Only buyers can express interest in properties.', category='error')
        return redirect(url_for('home'))

    # Retrieve the SNS topic ARN from the session
    topic_arn = session.get('sns_topic_arn')
    if not topic_arn:
        flash('Notification system is not configured. Please contact support.', category='error')
        return redirect(url_for('home'))

    try:
        # Query the property by ID to get details
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM properties WHERE id = %s", (property_id,))
            property = cursor.fetchone()

        if not property:
            flash('Property not found.', category='error')
            return redirect(url_for('home'))

        # Extract relevant details
        unique_property_id = property['property_id']
        property_details = {
            'location': property['location'],
            'price': property['price']
        }

        # Send SNS notification
        send_interest_notification(current_user.first_name, property_details, topic_arn, unique_property_id)
        flash(f'You have successfully expressed interest in the property at {property["location"]}.', category='success')

    except Exception as e:
        logging.error(f"Error expressing interest: {e}")
        flash('An unexpected error occurred. Please try again later.', category='error')

    return redirect(url_for('home'))




@app.route('/view_properties')
@login_required
def view_properties():
    # Fetch properties owned by the current user
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM properties WHERE owner_id = %s", (current_user.id,))
            properties = cursor.fetchall()

            # Split the facilities string into a list for rendering
            for property in properties:
                if property['facilities']:
                    property['facilities'] = property['facilities']
                else:
                    property['facilities'] = ''
    except Exception as e:
        flash(f"Error loading properties: {e}", category='error')
        properties = []

    return render_template('view_properties.html', properties=properties)


# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
    