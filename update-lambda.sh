#!/bin/sh
source "./config.sh"
./package.sh
aws lambda update-function-code \
  --function-name "${FUNCTION_NAME}" \
  --zip-file fileb://deploy.zip
