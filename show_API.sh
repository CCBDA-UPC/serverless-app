aws apigatewayv2 get-apis | jq -r '.Items[] | select(.ProtocolType=="WEBSOCKET") .ApiId' \
  | while read -r api_id; \
  do \
  (aws apigatewayv2 get-api --api-id $api_id ) > "api_${api_id}.json" ; \
  (aws apigatewayv2 get-routes --api-id $api_id | jq '.[] | sort_by(.RouteKey)') > "routes_${api_id}.json" ; \
  (aws apigatewayv2 get-integrations --api-id $api_id ) > "integrations_${api_id}.json" ;
  (aws apigatewayv2 get-integrations --api-id $api_id | jq -r '.Items[].IntegrationId' \
 | while read -r repo; \
 do aws apigatewayv2 get-integration-responses --api-id $api_id --integration-id $repo; \
 done) > "integration_response_${api_id}.json"
  done