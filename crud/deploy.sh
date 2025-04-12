#!/bin/bash

set -e # exit on first error

source $1

ENVIRONMENT_VARIABLES=()
for var in  REGION LOG_LEVEL; do
  ENVIRONMENT_VARIABLES+=($var=${!var})
done
ENVIRONMENT=$(IFS=, ; echo "${ENVIRONMENT_VARIABLES[*]}")

echo "ENVIRONMENT: ${ENVIRONMENT}"

aws dynamodb create-table \
  --table-name ${TABLE} \
  --attribute-definitions \
        AttributeName=thingID,AttributeType=S \
  --key-schema \
        AttributeName=thingID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ${REGION}

pushd lambda
zip lambda_crud.zip lambda_crud.py requirements.txt
LAMBDA_ARN=`aws lambda create-function \
   --function-name ${LAMBDA} \
  --zip-file fileb://lambda_crud.zip \
  --handler lambda_crud.lambda_handler \
  --runtime python3.13 \
  --role ${ROLE} \
  --environment "Variables={${ENVIRONMENT}}" \
  | jq -r '.FunctionArn'`

echo "LAMBDA_ARN: ${LAMBDA_ARN}"
popd

STATEMENT_ID=`uuidgen`
echo "STATEMENT_ID: ${STATEMENT_ID}"

aws lambda add-permission \
    --function-name ${LAMBDA} \
    --principal apigateway.amazonaws.com \
    --statement-id "${STATEMENT_ID}" \
    --action lambda:InvokeFunction

API_ID=`aws apigatewayv2 create-api \
  --name "CrudHttpAPI" \
  --protocol-type HTTP \
   | jq -r '.ApiId'`

echo "API_ID ${API_ID}"

INTEGRATION_ID=`aws apigatewayv2 create-integration \
    --api-id ${API_ID} \
    --integration-type AWS_PROXY \
    --integration-uri ${LAMBDA_ARN} \
    --integration-method ANY \
    --payload-format-version 2.0 \
    | jq -r '.IntegrationId' `

echo "INTEGRATION_ID: ${INTEGRATION_ID}"


for ROUTE in GET POST OPTIONS PUT DELETE; do
    aws apigatewayv2 create-route \
        --api-id ${API_ID} \
        --route-key "${ROUTE} /" \
        --target "integrations/${INTEGRATION_ID}"
done


STAGE="production"
aws apigatewayv2 create-stage \
     --api-id ${API_ID} \
     --stage-name ${STAGE} \
     --no-auto-deploy

aws apigatewayv2 create-deployment \
    --api-id ${API_ID} \
    --stage-name ${STAGE}


URL="https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}/?TableName=${TABLE}"
echo "URL: ${URL}"
curl $URL

echo -e "apiUrl = '${URL}';\nTableName = '${TABLE}';" > variables.js; cat variables.js