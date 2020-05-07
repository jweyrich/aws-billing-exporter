#!/bin/sh
source "./config.sh"

./package.sh

#
# Create permissions for our lambda function
#
aws iam create-role \
  --role-name "${ROLE_NAME}" \
  --assume-role-policy-document '{"Version": "2012-10-17","Statement": [{ "Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'

aws iam attach-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"

aws iam create-policy \
  --policy-name "${POLICY_NAME}" \
  --policy-document "$(BUCKET_NAME=${BUCKET_NAME} envsubst < lambda-policy.json.template)"

aws iam attach-role-policy \
    --role-name "${ROLE_NAME}" \
    --policy-arn "arn:aws:iam::${CURRENT_ACCOUNT_ID}:policy/${POLICY_NAME}"

#
# Create our lambda function
#
aws lambda create-function \
  --function-name "${FUNCTION_NAME}" \
  --zip-file fileb://deploy.zip \
  --handler lambda.lambda_handler \
  --runtime python3.7 \
  --role "arn:aws:iam::${CURRENT_ACCOUNT_ID}:role/${ROLE_NAME}" \
  --environment "Variables={ACCOUNT_ID=${ACCOUNT_ID},BUCKET_NAME=${BUCKET_NAME}}"

#
# Configure Cross-Account Bucket Policy
#
aws s3api put-bucket-policy \
  --bucket "${BUCKET_NAME}" \
  --policy "$(ACCOUNT_ID=${ACCOUNT_ID} PRINCIPAL_USERNAME=${PRINCIPAL_USERNAME} BUCKET_NAME=${BUCKET_NAME} envsubst < bucket-policy.json.template)"

#
# Configure CloudWatch Scheduled Event
#
aws events put-rule \
  --name "${FUNCTION_NAME}-monthly" \
  --schedule-expression 'cron(0 0 3 * ? *)'

aws lambda add-permission \
  --function-name "${FUNCTION_NAME}" \
  --statement-id "events" \
  --action 'lambda:InvokeFunction' \
  --principal events.amazonaws.com \
  --source-arn "arn:aws:events:us-east-1:${CURRENT_ACCOUNT_ID}:rule/${FUNCTION_NAME}-monthly"

aws events put-targets \
  --rule "${FUNCTION_NAME}-monthly" \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:${CURRENT_ACCOUNT_ID}:function:${FUNCTION_NAME}"
