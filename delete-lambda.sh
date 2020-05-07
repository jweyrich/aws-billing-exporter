#!/bin/sh
source "./config.sh"
aws lambda delete-function --function-name "${FUNCTION_NAME}"
