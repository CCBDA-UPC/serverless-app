import boto3
import json
import logging
import os

REGION = os.environ['REGION']

logger = logging.getLogger()
logger.setLevel(os.environ['LOG_LEVEL'])

dynamodb = boto3.client('dynamodb', region_name=REGION)


def lambda_handler(event, context):
    operation = event['requestContext']['http']['method']
    logger.debug(f'operation {operation}')
    try:
        if operation == 'GET':
            return respond(dynamodb.scan(**event['queryStringParameters']))
        elif operation == 'POST':
            return respond(dynamodb.put_item(**json.loads(event['body'])))
        elif operation == 'DELETE':
            return respond(dynamodb.delete_item(**json.loads(event['body'])))
        elif operation == 'PUT':
            return respond(dynamodb.update_item(**json.loads(event['body'])))
        elif operation == 'OPTIONS':
            return respond('')
        else:
            return respond(None, f'Unsupported method "{operation}"')
    except Exception as e:
        respond(None, f'{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}')

def respond(res, err=None):
    response = {
        'statusCode': '200' if err is None else '400',
        'body': json.dumps(res) if err is None else err,
        'headers': {
            'Content-Type': 'application/json',
            "Access-Control-Allow-Headers": "Content-Type",
            'Access-Control-Allow-Origin': '*',
            "Access-Control-Allow-Methods": "GET, POST, DELETE, PUT, OPTIONS",
        },
    }
    logger.debug(f'response {json.dumps(response, indent=2)}')
    return response