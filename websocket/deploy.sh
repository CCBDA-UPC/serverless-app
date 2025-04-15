#!/bin/bash

set -e # exit on first error

source $1

ENVIRONMENT_VARIABLES=()
for var in API_KEY REGION CENTER TOP_LEFT BOTTOM_RIGHT DYNAMO_TABLE LOG_LEVEL STREAM_NAME; do
  ENVIRONMENT_VARIABLES+=($var=${!var})
done
ENVIRONMENT=$(IFS=, ; echo "${ENVIRONMENT_VARIABLES[*]}")

echo "ENVIRONMENT: ${ENVIRONMENT}"

pushd lambda/kinesis
zip lambda_kinesis.zip lambda_kinesis.py library_functions.py requirements.txt
LAMBDA_ARN=`aws lambda create-function \
   --function-name ${LAMBDA_KINESIS} \
  --zip-file fileb://lambda_kinesis.zip \
  --handler lambda_kinesis.lambda_handler \
  --runtime python3.13 \
  --role ${ROLE} \
  --environment "Variables={${ENVIRONMENT}}" \
  | jq -r '.FunctionArn'`

echo "LAMBDA_ARN: ${LAMBDA_ARN}"
popd


API_ID=`aws apigatewayv2 create-api \
  --name "WebSocketAPI" \
  --protocol-type WEBSOCKET \
  --route-selection-expression "\$request.body.action" \
   | jq -r '.ApiId'`


echo "API_ID ${API_ID}"

pushd lambda/websocket

for ROUTE in connect disconnect default; do
    echo "ROUTE: ${ROUTE}"

    zip lambda_websocket_${ROUTE}.zip lambda_${ROUTE}.py library_functions.py requirements.txt
    LAMBDA_ARN=`aws lambda create-function \
    --function-name ${LAMBDA_WEBSOCKET}_${ROUTE} \
    --zip-file fileb://lambda_websocket_${ROUTE}.zip \
    --handler lambda_${ROUTE}.lambda_handler \
    --runtime python3.13 \
    --role ${ROLE} \
    --environment "Variables={${ENVIRONMENT}}" \
    | jq -r '.FunctionArn'`

    echo "LAMBDA_ARN: ${}"

    STATEMENT_ID=`uuidgen`

    echo "STATEMENT_ID ${}"

    aws lambda add-permission \
      --function-name ${LAMBDA_WEBSOCKET}_${ROUTE} \
      --principal apigateway.amazonaws.com \
      --statement-id "${STATEMENT_ID}" \
      --action lambda:InvokeFunction \
      --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT_ID}:${API_ID}/*/\$${ROUTE}"

    INTEGRATION_ID=`aws apigatewayv2 create-integration \
    --api-id ${API_ID} \
    --integration-type AWS_PROXY \
    --integration-uri arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations \
    --integration-method POST \
    | jq -r '.IntegrationId' `

    echo "INTEGRATION_ID: ${INTEGRATION_ID}"

    aws apigatewayv2 create-route \
      --api-id ${API_ID} \
      --route-key \$${ROUTE} \
      --target "integrations/${INTEGRATION_ID}"
done
popd

STAGE="production"
aws apigatewayv2 create-stage \
     --api-id ${API_ID} \
     --stage-name ${STAGE} \
     --auto-deploy | cat

URL="wss://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}/"

echo "URL: ${URL}"