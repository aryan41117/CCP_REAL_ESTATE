import boto3
from botocore.exceptions import ClientError
import logging

# Create SNS client
sns_client = boto3.client('sns', region_name='us-east-1')  

def create_sns_topic(topic_name):
    """
    Creates an SNS topic and returns its ARN.
    """
    try:
        # Check if the topic already exists by listing topics
        response = sns_client.list_topics()
        existing_topics = response['Topics']
        
        # If the topic already exists, return the ARN
        for topic in existing_topics:
            if topic_name in topic['TopicArn']:
                logging.info(f"Topic '{topic_name}' already exists.")
                return topic['TopicArn']
        
        # If the topic doesn't exist, create it
        response = sns_client.create_topic(Name=topic_name)
        topic_arn = response['TopicArn']
        logging.info(f"Created new topic: {topic_name} with ARN: {topic_arn}")
        return topic_arn
    except ClientError as e:
        logging.error(f"Error creating SNS topic: {e}")
        return None

def subscribe_to_topic(topic_arn, email_address):
    """
    Subscribes an email address to the given SNS topic.
    """
    try:
        # Subscribe to the topic via email
        response = sns_client.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email_address
        )
        logging.info(f"Subscription request sent to {email_address}. Check your inbox to confirm.")
    except ClientError as e:
        logging.error(f"Error subscribing to SNS topic: {e}")

def publish_message_to_topic(topic_arn, message, subject):
    """
    Publishes a message to the given SNS topic.
    """
    try:
        sns_client.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject=subject
        )
        logging.info(f"Message published to SNS topic: {topic_arn}")
    except ClientError as e:
        logging.error(f"Error publishing message to SNS topic: {e}")

# Function to send SNS notifications
# Function to send SNS notifications
def send_interest_notification(buyer_name, property_details, topic_arn, unique_property_id):
    """
    Sends a notification to the seller when a buyer expresses interest.
    """
    message = (f"Buyer {buyer_name} has expressed interest in your property with Property ID: {unique_property_id}, "
               f"located at {property_details['location']}, priced at ${property_details['price']}.")
    
    try:
        response = sns_client.publish(
            TopicArn=topic_arn,  # Pass the ARN dynamically
            Message=message,
            Subject='New Property Interest'
        )
        logging.info(f"SNS Publish Response: {response}")
        return response
    except ClientError as e:
        logging.error(f"Error publishing to SNS: {e}")
        raise e

