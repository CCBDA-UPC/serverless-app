from datetime import datetime, timezone
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
    url = library.get_url(event, REGION)
    logger.info(f'New connection: {url} {connection_id}')
    try:
        dynamodb = boto3.client('dynamodb', region_name=REGION)
        dynamodb.put_item(TableName=DYNAMO_TABLE,
                          Item={
                              'connectionid': {'S': connection_id},
                              'url': {'S': url},
                              'when': {'S': datetime.now(timezone.utc).isoformat()}
                          })
    except Exception as e:
        logger.error(f'PutItem {str(e)}')
        return library.handle_response(json.dumps('Error connecting!'), 400)
    return library.handle_response(json.dumps('Connection sucessful!'))
