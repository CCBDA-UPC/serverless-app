import json
import boto3
import time
import os
from dotenv import load_dotenv
from FlightRadar24 import FlightRadar24API

load_dotenv()

AWS_REGION = os.getenv('AWS_REGION')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
CENTER = os.getenv('CENTER').split(':')
TOP_LEFT = os.getenv('TOP_LEFT').split(':')
BOTTOM_RIGHT = os.getenv('BOTTOM_RIGHT').split(':')
STREAM_NAME = os.getenv('STREAM_NAME')

RADIUS = 30000


kinesis = boto3.client('kinesis',
                       region_name=AWS_REGION,
                       aws_access_key_id=AWS_ACCESS_KEY_ID,
                       aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                       # aws_session_token=AWS_SESSION_TOKEN
                       )

fr_api = FlightRadar24API()
bounds = fr_api.get_bounds_by_point(float(CENTER[0]),float(CENTER[1]), RADIUS)
for i in range(1, 1000):
    list = {}
    for f in fr_api.get_flights(bounds=bounds):
        list[f.registration] = {
            "latitude": f.latitude,
            "longitude": f.longitude,
            "code": f.aircraft_code,
            "origin": f.origin_airport_iata,
            "destination": f.destination_airport_iata,
            "number": f.number,
            "flying": f.on_ground != 0,
            "airline": "BAW"
        }
    encoded_data = json.dumps(list).encode('utf-8')

    response = kinesis.put_record(
        StreamName=STREAM_NAME,
        Data=encoded_data,
        PartitionKey='partition-key-1'
    )
    print(f"Sent event {i}")
    time.sleep(5)
