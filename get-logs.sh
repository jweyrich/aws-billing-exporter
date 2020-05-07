#!/bin/sh
source "./config.sh"

# Gether latest logs of our function. From newest to oldest.
STREAM_NAMES=$(aws logs describe-log-streams \
  --log-group-name "/aws/lambda/${FUNCTION_NAME}" \
  --order-by "LastEventTime" \
  --descending \
  --max-items 5 | jq --raw-output '.logStreams[].logStreamName')

for name in ${STREAM_NAMES}; do
  aws logs get-log-events \
    --log-group-name "/aws/lambda/${FUNCTION_NAME}" \
    --log-stream-name "$name"
  sleep 1
done
