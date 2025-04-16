#!/bin/bash

set -e # exit on first error

source $1

ENVIRONMENT_VARIABLES=()
for var in API_KEY REGION CENTER TOP_LEFT BOTTOM_RIGHT DYNAMO_TABLE LOG_LEVEL; do
  ENVIRONMENT_VARIABLES+=($var=${!var})
done
ENVIRONMENT=$(IFS=, ; echo "${ENVIRONMENT_VARIABLES[*]}")

echo "ENVIRONMENT: ${ENVIRONMENT}"


aws kinesis create-stream \
    --stream-name ${STREAM_NAME} \
    --shard-count 1

STREAM_ARN=`aws kinesis describe-stream \
    --stream-name ${STREAM_NAME} \
    | jq -r '.StreamDescription.StreamARN'`

echo "STREAM_ARN: ${STREAM_ARN}"


aws dynamodb create-table \
  --table-name ${DYNAMO_TABLE} \
  --attribute-definitions \
        AttributeName=connectionid,AttributeType=S \
  --key-schema \
        AttributeName=connectionid,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ${REGION}

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

aws lambda create-event-source-mapping \
    --function-name ${LAMBDA_KINESIS} \
    --event-source  ${STREAM_ARN} \
    --batch-size 100 \
    --starting-position LATEST

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

    echo "LAMBDA_ARN: ${LAMBDA_ARN}"

    STATEMENT_ID=`uuidgen`

    echo "STATEMENT_ID ${STATEMENT_ID}"

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
     --no-auto-deploy

aws apigatewayv2 create-deployment \
    --api-id ${API_ID} \
    --stage-name ${STAGE}

URL="wss://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}/"

echo "URL: ${URL}"

echo -e "{\"url\":\"${URL}\"}" > variables.json; cat variables.json