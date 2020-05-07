import boto3
from botocore.exceptions import ClientError
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import json
import logging
import os
import sys

from billing import AWSMonthlyBillingFetcher

def upload_to_s3(binary_data, bucket_name, object_name):
    # Upload the file
    s3_client = boto3.client('s3')
    try:
        s3_client.put_object(Body=binary_data, Bucket=bucket_name, Key=object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def lambda_handler(event, context):
    logging.basicConfig(level=logging.INFO, format='%(filename)s: %(message)s')
    logging.info('event: %s', json.dumps(event, indent=4))

    account_id = os.environ.get('ACCOUNT_ID', '')
    bucket_name = os.environ.get('BUCKET_NAME', '')
    if not account_id:
        logging.error('Missing environment variable: ACCOUNT_ID')
        sys.exit(1)
    if not bucket_name:
        logging.error('Missing environment variable: BUCKET_NAME')
        sys.exit(1)

    last_month = date.today() - relativedelta(months=1)

    logging.info('account_id: %s', account_id)
    logging.info('bucket_name: %s', bucket_name)
    logging.info('period: %02d/%d', last_month.month, last_month.year)

    fetcher = AWSMonthlyBillingFetcher(accountId=account_id, year=last_month.year, month=last_month.month)
    fetcher.fetch()
    json_string = json.dumps(fetcher.result.value, indent=4)

    object_name = '%s/billing/%d-%02d.json' % (account_id, last_month.year, last_month.month)
    logging.info('object_name: %s', object_name)

    #file_name = '%s-billing-%d-%02d.json' % (account_id, last_month.year, last_month.month)
    #with open(file_name, "w") as outfile:
    #    outfile.write(json_string)

    logging.info('uploading file...')
    upload_to_s3(json_string, bucket_name, object_name)
    logging.info('upload complete')

    return {
        'account_id': account_id,
        'bucket_name': bucket_name,
        'year': last_month.year,
        'month': last_month.month,
        'object_name': object_name,
    }

if __name__ == '__main__':
    os.environ['ACCOUNT_ID'] = 'REPLACE_ME'
    os.environ['BUCKET_NAME'] = 'exported-billing-reports'
    lambda_handler({}, {})
