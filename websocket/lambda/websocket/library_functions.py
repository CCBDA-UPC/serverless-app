def get_url(event, region):
    return f'https://{event['requestContext']['apiId']}.execute-api.{region}.amazonaws.com/{event['requestContext']['stage']}/'

def handle_response(res, status=200):
    return {
        'statusCode': status,
        'body': res,
        'headers': {
            'Content-Type': 'application/json',
            "Access-Control-Allow-Headers": "Content-Type",
            'Access-Control-Allow-Origin': '*',
            "Access-Control-Allow-Methods": "GET, POST, DELETE, PUT, OPTIONS",
        },
    }