import json
import logging
import boto3
import os
import library_functions as library

API_KEY = os.environ['API_KEY']
REGION = os.environ['REGION']
CENTER = os.environ['CENTER'].split(':')
TOP_LEFT = os.environ['TOP_LEFT'].split(':')
BOTTOM_RIGHT = os.environ['BOTTOM_RIGHT'].split(':')

logger = logging.getLogger()
logger.setLevel(os.environ['LOG_LEVEL'])


def lambda_handler(event, context):
    connection_id = event['requestContext']['connectionId']
    logger.info(f'event {json.dumps(event, indent=2)}')

    if event['body'] == 'hello!':
        config = {
            'type': 'init',
            'apiKey': API_KEY,
            'center': CENTER,
            'bounds': [TOP_LEFT, BOTTOM_RIGHT],
        }
        message = json.dumps(config)
        logger.debug(f'send_message_to_client "{connection_id}" message {message}')
        apigw = boto3.client('apigatewaymanagementapi', endpoint_url=library.get_url(event,REGION))
        try:
            apigw.post_to_connection(
                ConnectionId=connection_id,
                Data=message
            )
        except apigw.exceptions.GoneException:
            logger.info(f'Connection "{connection_id}" is no longer valid.')
        except Exception as e:
            logger.error(f'Error sending "{message}" to connection "{connection_id}" {str(e)}')
        return library.handle_response(json.dumps('Init message sent.'))
    else:
        return library.handle_response(json.dumps('I cannot respond'), 400)



