CURRENT_ACCOUNT_ID=$(aws sts get-caller-identity | jq --raw-output '.Account')
ACCOUNT_ID="REPLACE_ME"
PRINCIPAL_USERNAME="REPLACE_ME"
FUNCTION_NAME="aws-billing-exporter-${ACCOUNT_ID}"
ROLE_NAME="aws-billing-exporter-${ACCOUNT_ID}"
POLICY_NAME="aws-billing-exporter-${ACCOUNT_ID}-perms"
BUCKET_NAME="exported-billing-reports"
