import base64
import json


def get_secret(secrets_client, secret_name: str, region: str) -> str:
    """Returns a secrets object from AWS Secrets Manager"""
    resp = secrets_client.get_secret_value(SecretId=secret_name)
    if 'SecretString' in resp:
        secret = resp['SecretString']
        return secret
    decoded_binary_secret = base64.b64decode(resp['SecretBinary'])
    return decoded_binary_secret


def get_json_secret(secrets_client, secret_name: str, region: str) -> dict:
    """Returns a decoded JSON dict from a secret stored in AWS Secrets Manager"""
    return json.loads(get_secret(secrets_client, secret_name, region))
