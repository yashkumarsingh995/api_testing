"""Helper methods for reading and writing to S3"""
import json
import logging

from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_object_from_s3(s3_client, bucket, key, default=None):
    try:
        obj = s3_client.get_object(
            Bucket=bucket,
            Key=key
        )
        return json.loads(obj['Body'].read().decode('utf-8'))
    except ClientError:
        logger.exception(f'Error pulling object {key} from bucket {bucket}')
        if default is not None:
            logger.info(f'Returning default {default}')
            return default


def list_folders_in_s3(s3_client, bucket, prefix=''):
    """Lists the folders at a given level (prefix) in S3"""
    folders = []
    try:
        continuation_token = None
        while True:
            params = {
                'Bucket': bucket,
                'Prefix': prefix,
                'Delimiter': '/'
            }
            if continuation_token:
                params['ContinuationToken'] = continuation_token
            resp = s3_client.list_objects_v2(**params)
            logger.info('list_folders_in_s3 resp')
            logger.info(resp)
            for content in resp.get('CommonPrefixes', []):
                folders.append(content.get('Prefix'))
            if 'NextContinuationToken' not in resp:
                break
            continuation_token = resp.get('NextContinuationToken')
    except ClientError:
        logger.exception(f'Error reading folders at prefix {prefix} from bucket {bucket}')
    return folders 


def put_object_into_s3(s3_client, bucket, key, obj):
    try:
        resp = s3_client.put_object(
            Body=obj,
            Bucket=bucket,
            Key=key
        )
        return resp
    except ClientError:
        logger.exception(f'Error putting object {key} into bucket {bucket}')


def write_to_s3(s3_client, bucket, key, body):
    return s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(body, indent=4, sort_keys=True, default=str)
    )

