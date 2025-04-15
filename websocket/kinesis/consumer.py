import asyncio
import json
import boto3
import websockets
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

AWS_REGION = os.getenv('AWS_REGION')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
#AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')

# AWS + Kinesis setup
kinesis_client = boto3.client('kinesis', region_name=AWS_REGION,
                              aws_access_key_id=AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                              # aws_session_token=AWS_SESSION_TOKEN
                              )
stream_name = 'myStream'

# WebSocket server URI
websocket_uri = "ws://localhost:8765"  # Or your actual WebSocket endpoint


async def send_kinesis_data():
    # Get the shard iterator
    response = kinesis_client.describe_stream(
        StreamName=stream_name
    )
    shard_id = response['StreamDescription']['Shards'][0]['ShardId']

    shard_iterator = kinesis_client.get_shard_iterator(
        StreamName=stream_name,
        ShardId=shard_id,
        ShardIteratorType='LATEST'
    )['ShardIterator']

    if False:
        async with websockets.connect(websocket_uri) as websocket:
            while True:
                # Read records from Kinesis
                output = kinesis_client.get_records(ShardIterator=shard_iterator, Limit=10)
                shard_iterator = output['NextShardIterator']

                # Send each record to WebSocket
                for record in output['Records']:
                    data = record['Data'].decode('utf-8')  # Assuming UTF-8 string data
                    await websocket.send(data)
                    print(f"Sent to WebSocket: {data}")

                await asyncio.sleep(1)  # Poll interval
    else:
        while True:
            # Read records from Kinesis
            output = kinesis_client.get_records(ShardIterator=shard_iterator, Limit=10)
            shard_iterator = output['NextShardIterator']
            # Send each record to WebSocket
            for record in output['Records']:
                data = record['Data'].decode('utf-8')  # Assuming UTF-8 string data
                print(f"Sent to WebSocket: {data}")
            await asyncio.sleep(1)

# Run the async loop
asyncio.run(send_kinesis_data())
