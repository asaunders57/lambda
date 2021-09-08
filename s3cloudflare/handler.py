import requests
import boto3
import logging
import traceback
import sys
import json

s3 = boto3.client('s3')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    bucket_names = event['bucket_names']

    # Convert variable to list if only passed one bucket
    if type(bucket_names) is str:
        bucket_names = [bucket_names]

    # Get current Cloudflare IP ranges
    response = requests.get('https://api.cloudflare.com/client/v4/ips').json()
    cloudflare_ip_list = response["result"]["ipv4_cidrs"] + \
        response["result"]["ipv6_cidrs"]

    for bucket in bucket_names:
        # Get list of IP ranges in bucket policy statement allowing access from Cloudflare
        policy = s3.get_bucket_policy(Bucket=bucket)['Policy']
        policy_dict = json.loads(policy)
        # Assume statement contains "Sid" key with value "AllowPublicReadCloudflare"
        for i, statement in enumerate(policy_dict['Statement']):
            if 'Sid' in statement and statement['Sid'] == 'AllowPublicReadCloudflare':
                policy_ip_list = policy_dict['Statement'][i]['Condition']['IpAddress']['aws:SourceIp']

        if cloudflare_ip_list == policy_ip_list:
            logger.info(
                "The list of IPs in the bucket policy statement for %s are up-to-date", bucket)
        else:
            logger.info(
                "Updating the list of IPs in the bucket policy statement for %s...", bucket)
            update_bucket_policy(bucket, policy_dict, cloudflare_ip_list)
            logger.info(
                "Updated the list of IPs in the bucket policy statement for %s", bucket)


def update_bucket_policy(bucket_name, bucket_policy, cloudflare_ip_list):
    try:
        for i, statement in enumerate(bucket_policy['Statement']):
            if 'Sid' in statement and statement['Sid'] == 'AllowPublicReadCloudflare':
                bucket_policy['Statement'][i]['Condition']['IpAddress']['aws:SourceIp'] = cloudflare_ip_list
                new_policy = json.dumps(bucket_policy)
                s3.put_bucket_policy(Bucket=bucket_name, Policy=new_policy)
    except Exception:
        exception_type, exception_value, exception_traceback = sys.exc_info()
        traceback_string = traceback.format_exception(
            exception_type, exception_value, exception_traceback)
        err_msg = json.dumps({
            "errorType": exception_type.__name__,
            "errorMessage": str(exception_value),
            "stackTrace": traceback_string
        })
        logger.error(err_msg)
