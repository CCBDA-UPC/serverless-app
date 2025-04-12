import boto3
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

AWS_REGION = os.getenv('AWS_REGION')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
# AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')

# Kinesis stream name
stream_name = 'myStream'

# Create Kinesis client
kinesis = boto3.client('kinesis',
                       region_name=AWS_REGION,
                       aws_access_key_id=AWS_ACCESS_KEY_ID,
                       aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                       # aws_session_token=AWS_SESSION_TOKEN
                       )

# Sample data (can be any JSON-serializable data)
data = {
    'type': 123,
    'aircrafts':
        [{
            'longitude': f.longitude,
            'latitude': f.latitude,
            'ground': f.on_ground,
        }
        ],

}


# Send to Kinesis

for i in range(100):
    data['timestamp'] = time.time()
    data['event_id'] = i
    encoded_data = json.dumps(data).encode('utf-8')

    response = kinesis.put_record(
        StreamName=stream_name,
        Data=encoded_data,
        PartitionKey='partition-key-1'
    )

    print(f"Sent event {i}")
    # time.sleep(0.1)  # simulate 1-second interval
