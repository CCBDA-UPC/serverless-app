import json
import logging
import boto3
import os
import library_functions as library

DYNAMO_TABLE = os.environ['DYNAMO_TABLE']
REGION = os.environ['REGION']

logger = logging.getLogger()
logger.setLevel(os.environ['LOG_LEVEL'])


def lambda_handler(event, context):
    logger.debug(f'event {json.dumps(event, indent=2)}')
    connection_id = event['requestContext']['connectionId']
    try:
        dynamodb = boto3.client('dynamodb', region_name=REGION)
        dynamodb.delete_item(TableName=DYNAMO_TABLE,
                             Key={
                                 'connectionid': {'S': connection_id},
                                 'url': {'S': library.get_url(event, REGION)}
                             })
    except Exception as e:
        logger.error(f'Error disconnecting: "{connection_id}" {str(e)}')
        return library.handle_response(json.dumps('Error disconnecting.'), 400)
    logger.info(f'Disconnected: "{connection_id}"')
    return library.handle_response(json.dumps({'message': 'Disconnected successfully.'}))
