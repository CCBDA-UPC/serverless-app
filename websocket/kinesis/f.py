import json
import requests
import math
from typing import Dict
from flights.flight import Flight
import boto3
import time
import os
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables from a .env file
load_dotenv()

AWS_REGION = os.getenv('AWS_REGION')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

CONFIG = {
    'latitude': 41.29707,
    'longitude': 2.078463,
}
RADIUS = 30000
stream_name = 'myStream'

kinesis = boto3.client('kinesis',
                       region_name=AWS_REGION,
                       aws_access_key_id=AWS_ACCESS_KEY_ID,
                       aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                       # aws_session_token=AWS_SESSION_TOKEN
                       )


def get_bounds(zone: Dict[str, float]) -> str:
    """
    Convert coordinate dictionary to a string "y1, y2, x1, x2".

    :param zone: Dictionary containing the following keys: tl_y, tl_x, br_y, br_x
    """
    return "{},{},{},{}".format(zone["tl_y"], zone["br_y"], zone["tl_x"], zone["br_x"])


def get_bounds_by_point(latitude: float, longitude: float, radius: float) -> str:
    """
    Convert a point coordinate and a radius to a string "y1, y2, x1, x2".

    :param latitude: Latitude of the point
    :param longitude: Longitude of the point
    :param radius: Radius in meters to create area around the point
    """
    half_side_in_km = abs(radius) / 1000

    lat = math.radians(latitude)
    lon = math.radians(longitude)

    approx_earth_radius = 6371
    hypotenuse_distance = math.sqrt(2 * (math.pow(half_side_in_km, 2)))

    lat_min = math.asin(
        math.sin(lat) * math.cos(hypotenuse_distance / approx_earth_radius)
        + math.cos(lat)
        * math.sin(hypotenuse_distance / approx_earth_radius)
        * math.cos(225 * (math.pi / 180)),
    )
    lon_min = lon + math.atan2(
        math.sin(225 * (math.pi / 180))
        * math.sin(hypotenuse_distance / approx_earth_radius)
        * math.cos(lat),
        math.cos(hypotenuse_distance / approx_earth_radius)
        - math.sin(lat) * math.sin(lat_min),
    )

    lat_max = math.asin(
        math.sin(lat) * math.cos(hypotenuse_distance / approx_earth_radius)
        + math.cos(lat)
        * math.sin(hypotenuse_distance / approx_earth_radius)
        * math.cos(45 * (math.pi / 180)),
    )
    lon_max = lon + math.atan2(
        math.sin(45 * (math.pi / 180))
        * math.sin(hypotenuse_distance / approx_earth_radius)
        * math.cos(lat),
        math.cos(hypotenuse_distance / approx_earth_radius)
        - math.sin(lat) * math.sin(lat_max),
    )

    rad2deg = math.degrees

    zone = {
        "tl_y": rad2deg(lat_max),
        "br_y": rad2deg(lat_min),
        "tl_x": rad2deg(lon_min),
        "br_x": rad2deg(lon_max)
    }
    return get_bounds(zone)


if False:
    fr_api = FlightRadar24API()
    airport_details = fr_api.get_airport_details('BCN')
    position = airport_details['airport']['pluginData']['details']['position']

    fr_api = FlightRadar24API()
    bounds = fr_api.get_bounds_by_point(CONFIG['latitude'], CONFIG['longitude'], RADIUS)
    for f in fr_api.get_flights(bounds=bounds):
        print(f)
    exit()
headers = {'accept': 'application/json',
           'accept-encoding': 'gzip, br',
           'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
           'cache-control': 'max-age=0',
           'origin': 'https://www.flightradar24.com',
           'referer': 'https://www.flightradar24.com/',
           'sec-fetch-dest': 'empty',
           'sec-fetch-mode': 'cors',
           'sec-fetch-site': 'same-site',
           'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
           }

url = 'https://api.flightradar24.com/common/v1/airport.json?format=json&code=BCN&limit=100&page=1'

r = requests.get(url, headers=headers)
bounds = get_bounds_by_point(CONFIG['latitude'], CONFIG['longitude'], RADIUS)
qs = {
    'adsb': '1',
    'air': '1',
    'bounds': bounds,
    'estimated': '1',
    'faa': '1',
    'flarm': '1',
    'gliders': '1',
    'gnd': '1',
    'limit': '5000',
    'maxage': '14400',
    'mlat': '1',
    'satellite': '1',
    'stats': '1',
    'vehicles': '1'}
url = 'https://data-cloud.flightradar24.com/zones/fcgi/feed.js'

for i in range(60*15):
    r = requests.get(url, headers=headers, params=qs)
    flights = json.loads(r.text)
    data = {}
    for k, v in flights.items():
        if k in ['full_count', 'version', 'stats']:
            continue
        ff = Flight(flight_id=k, info=v)
        registration = ff.registration
        if len(registration) > 0:
            if ff.origin == 'BCN' or ff.destination == 'BCN':
                info = ff.__dict__
                del info['registration']
                data[registration] = info

    encoded_data = json.dumps(data).encode('utf-8')

    response = kinesis.put_record(
        StreamName=stream_name,
        Data=encoded_data,
        PartitionKey='partition-key-1'
    )
    print(f"Sent event {i}")
    with open('flights.json', 'a') as fw:
        now = datetime.now(timezone.utc).strftime('%H:%M:%S')
        data = {now:data}
        fw.write(json.dumps(data)+'\n')
    time.sleep(1)

