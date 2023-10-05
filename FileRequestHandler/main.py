from flask import abort
from google.cloud import storage, pubsub_v1
import logging

BANNED_COUNTRIES = ['North Korea', 'Iran', 'Cuba', 'Myanmar', 'Iraq', 'Libya', 'Sudan', 'Zimbabwe', 'Syria']

def publish_message(project_id, topic_name, message):
    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, topic_name)

        # Data must be a bytestring
        data = message.encode('utf-8')

        # When you publish a message, the client returns a future.
        future = publisher.publish(topic_path, data=data)
        print(f"Publishing message to {topic_path}")

        # Wait for the publish future to resolve.
        message_id = future.result()

        print(f"Published message ID: {message_id}")

    except Exception as e:
        print(f"An error occurred: {e}")

def handle_request(request):
    # Check if the request method is GET
    if request.method != 'GET':
        return abort(501)
    
    # Extract the bucket name and file address from the request path
    path_parts = request.path.lstrip('/').split('/')
    if len(path_parts) < 2:
        return abort(400, 'Invalid path format')
    
    bucket_name = path_parts[0]
    file_name = '/'.join(path_parts[1:])

    # Retrieve the country from the request headers
    country = request.headers.get('X-country')

    logging.info(f"Received request for file: {file_name} from country: {country}")

    # Check if the country is banned
    if country in BANNED_COUNTRIES:
        # Log and send a message to the second app
        print(f"Forbidden request from {country}. Sending message to second app.")
        
        # Define your project_id and topic_name here
        project_id = 'myaccountproject'
        topic_name = 'forbidden-requests'
        
        # Construct the message you want to send
        message = f"Forbidden request attempted from {country} for file {file_name}"
        
        # Call publish_message function
        publish_message(project_id, topic_name, message)
        
        return abort(400)  # Permission denied

    # Set up Google Cloud Storage client
    storage_client = storage.Client(project='myaccountProject')

    # Try to retrieve the file from the storage bucket
    try:
        bucket = storage_client.get_bucket(bucket_name)
        blob = storage.Blob(file_name, bucket)
        file_content = blob.download_as_text()
        return file_content, 200
    except Exception as e:
        print(e)
        return abort(404)