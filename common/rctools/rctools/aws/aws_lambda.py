import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def async_invoke(lambda_client, name, payload):
    logger.info(f'Async invoking {name}')
    res = lambda_client.invoke(
        FunctionName=name,
        InvocationType='Event',
        Payload=json.dumps(payload)
    )
    logger.info(f'Async response: {res}')
    return


def sync_invoke(lambda_client, name, payload):
    logger.info(f'Sync invoking {name}')
    res = lambda_client.invoke(
        FunctionName=name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    logger.info(f'Sync response: {res}')
    return
