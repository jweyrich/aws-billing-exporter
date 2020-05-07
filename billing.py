import boto3
from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import json
import logging

class AWSMonthlyBillingResult:
    def __init__(self, value):
        self._value = value
        # TODO(jweyrich): Parse value.

    def __str__(self):
        return str(self._value)

    @property
    def value(self) -> object:
        return self._value

class AWSMonthlyBillingFetcher:
    def __init__(self, accountId: str, year: int, month: int):
        self._result = None
        self._accountId = accountId
        self._period = self.__class__.makeMonthlyPeriod(year, month)

    @property
    def result(self) -> AWSMonthlyBillingResult:
        return self._result

    @property
    def accountId(self) -> str:
        return self._accountId

    @property
    def startDate(self) -> date:
        return self._period[0]

    @property
    def endDate(self) -> date:
        return self._period[1]

    @staticmethod
    def makeMonthlyPeriod(year: int, month: int) -> (date, date):
        start_date = date(year=year, month=month, day=1)
        end_date = (start_date + relativedelta(months=1)).replace(day=1)
        return start_date, end_date

    def fetch(self):
        client = boto3.client('ce', region_name='us-east-1')

        # Parameters for the CostExplorer API
        params = {
            'TimePeriod': {
                'Start': self.startDate.isoformat(), # inclusive, 'yyyy-mm-dd'
                'End': self.endDate.isoformat() # exclusive, 'yyyy-mm-dd'
            },
            'Granularity': 'MONTHLY',
            'Filter': {
                'And': [
                    {
                        'Dimensions': {
                            'Key': 'LINKED_ACCOUNT',
                            'Values': [ self.accountId ]
                        }
                    }, {
                        'Not': {
                            'Dimensions': {
                                'Key': 'RECORD_TYPE',
                                'Values': [
                                    # 'Credit', 'Refund', 'Upfront', 'Recurring', 'Tax', 'Support', 'Other'
                                    'Refund', 'Tax'
                                ]
                            }
                        }
                    }
                ]
            },
            'Metrics': [
                # 'AmortizedCost', 'BlendedCost', 'NetAmortizedCost', 'NetUnblendedCost', 'NormalizedUsageAmount', 'UnblendedCost', 'UsageQuantity'
                'UnblendedCost', 'UsageQuantity'
            ],
            'GroupBy': [
                { 'Type': 'DIMENSION', 'Key': 'SERVICE' },
                { 'Type': 'DIMENSION', 'Key': 'USAGE_TYPE' }
            ]
        }

        # Accumulated responses
        chunks = []

        while True:
            # Request Cost & Usage data for the given account and period.
            response = client.get_cost_and_usage(**params)

            if 'ResultsByTime' in response:
                chunks.extend(response['ResultsByTime'])

            # If there's a `NextPageToken` in the response it means the result was
            # paginated. To get the next chunk of the response we need to send this
            # value in the next request, so we append it to `params` which will be
            # re-used in the next request.
            if not 'NextPageToken' in response:
                break
            params['NextPageToken'] = response['NextPageToken']

        # Use the 1st chunk and iterate over the remaining chunks
        # to merge the attributes we're interested in.
        chunks_iter = iter(chunks)
        result = next(chunks_iter)
        for chunk in chunks_iter:
            result['Groups'].extend(chunk['Groups'])

        # Store the Unit (currency) from the 1st item.
        first_group = next(iter(result['Groups']))
        result['Total']['Unit'] = first_group['Metrics']['UnblendedCost']['Unit']
        # Accumulate costs
        result['Total']['Amount'] = str(sum(
            Decimal(g['Metrics']['UnblendedCost']['Amount'])
            for g in result['Groups']
        ))

        self._result = AWSMonthlyBillingResult(result)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(filename)s: %(message)s')
    lastMonth = date.today() - relativedelta(month=1)
    fetcher = AWSMonthlyBillingFetcher(accountId='REPLACE_ME', year=lastMonth.year, month=lastMonth.month)
    fetcher.fetch()
    json_result = json.dumps(fetcher.result.value, indent=4)
    print(json_result)
