import base64
import decimal
import json
import logging
from datetime import datetime
from typing import List, Literal, Union, Optional

from boto3.dynamodb.conditions import Attr, Key
from pydantic import BaseModel

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants for key condition expressions
KEY_COND_EQ = 'EQ'
KEY_COND_GTE = 'GTE'


class DynamoJsonEncoder(json.JSONEncoder):
    """Helper class to convert a DynamoDB item to JSON by encoding decimals"""
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return { '__decimal__': True, 'value': str(o) }
        return super(DynamoJsonEncoder, self).default(o)


class DynamoPrimaryKey:
    class KeyQuery(BaseModel):
        key: str
        comparator: Literal['EQ', 'GTE'] = 'EQ'
        value: Union[str, int]
        type: Literal['partition', 'sort'] = 'partition'

        def get_typed_value(self):
            if self.type == 'sort':
                return int(self.value)
            return self.value

        def to_key_expression(self):
            if self.comparator == KEY_COND_EQ:
                # logger.info(f'Returning EQ key expression with {self.key} and {type(self.get_typed_value())} {self.value}')
                return Key(self.key).eq(self.get_typed_value())
            elif self.comparator == KEY_COND_GTE:
                # logger.info(f'Returning GTE key expression with {self.key} and {type(self.get_typed_value())} {self.value}')
                return Key(self.key).gte(self.get_typed_value())

    _partition: Optional[Union[dict, KeyQuery]] = None
    _sort: Optional[Union[dict, KeyQuery]] = None

    @property
    def partition(self) -> Optional[KeyQuery]:
        return self._partition

    @partition.setter
    def partition(self, key: Union[dict, KeyQuery]):
        if isinstance(key, dict):
            self._partition = DynamoPrimaryKey.KeyQuery(
                **{'key': list(key.keys())[0], 'value': list(key.values())[0], 'type': 'partition'}
            )
        else:
            key.type = 'partition'
            self._partition = key

    @property
    def sort(self) -> Optional[KeyQuery]:
        return self._sort

    @sort.setter
    def sort(self, key: Union[dict, KeyQuery]):
        if isinstance(key, dict):
            self._sort = DynamoPrimaryKey.KeyQuery(
                **{'key': list(key.keys())[0], 'value': list(key.values())[0], 'type': 'sort'}
            )
        else:
            key.type = 'sort'
            self._sort = key
        
    def keys(self) -> List[KeyQuery]:
        keys = []
        if self._partition:
            keys.append(self.partition)
        if self._sort:
            keys.append(self.sort)
        return keys


def create_dynamo_record(table, obj):
    record = mk_dynamo_record(obj)
    logger.info(f'Creating new dynamo record: {record}')
    return table.put_item(Item=record)


def decode_decimal(dct):
    if '__decimal__' in dct:
        return decimal.Decimal(dct['value'])
    return dct


def decode_token_to_key(token):
    json_string = base64.b64decode(token.encode('utf-8')).decode('utf-8')
    decoded_key = json.loads(json_string, object_hook=decode_decimal)
    return decoded_key


def encode_key_as_token(key):
    json_string = json.dumps(key, sort_keys=True, cls=DynamoJsonEncoder)
    return base64.b64encode(json_string.encode('utf-8')).decode('utf-8')


def fetch_items_by_pk(table, pk: DynamoPrimaryKey, limit=200, cursor_token=None, **kwargs):
    """
    Performs an efficient query operation on the user events table
    to produce a list of results and a 'LastEvaluatedKey' which if set
    can be passed in again to achieve cursor pagination.

    Can be passed additional kwargs that are forwarded to the query args.
    Some common keyword arguments here are IndexName for GSIs, ScanIndexForward
    to control sort order (False returns newest first).
    """
    key_condition_expression = mk_key_condition_expression(pk)

    # Note, table.query requires a KeyConditionExpression;
    # to query everything use db.scan_by_attributes
    query_args = {
        'KeyConditionExpression': key_condition_expression,  # Required
        **kwargs  # e.g., IndexName, ScanIndexForward
    }
    if cursor_token:
        decoder_cursor_token = decode_token_to_key(cursor_token)
        query_args['ExclusiveStartKey'] = decoder_cursor_token
    if limit:
        query_args['Limit'] = limit

    response = table.query(**query_args)
    response_last_evaluated_key = response.get('LastEvaluatedKey')
    encoded_cursor_token = None

    if response_last_evaluated_key:
        encoded_cursor_token = encode_key_as_token(response_last_evaluated_key)

    items = response['Items']
    logger.info(f'Dynamo response items from pk: {items},\n with encoded cursor:{encoded_cursor_token}')
    return items, encoded_cursor_token


def mk_dynamo_record(obj):
    """
    Recurses through an object, replacing floats with decimals and
    generally making the object suitable for writing to Dynamo
    """
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%dT%H:%M:%SZ')
    if isinstance(obj, list):
        for i in range(len(obj)):
            ditem = mk_dynamo_record(obj[i])
            if ditem is None:
                ditem = ''
            obj[i] = ditem
        return obj
    if isinstance(obj, dict):
        return {k: mk_dynamo_record(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, float):
        return decimal.Decimal(str(obj))

    return obj


def mk_key_condition_expression(pk: DynamoPrimaryKey):
    key_condition_expression = None
    if pk:
        for key in pk.keys():
            if not key_condition_expression:
                key_condition_expression = key.to_key_expression()
                continue
            key_condition_expression &= key.to_key_expression()
    return key_condition_expression


def mk_fetch_key_condition_expression(pk={}):
    key_condition_expression = None
    for key, value in pk.items():
        if not key_condition_expression:
            key_condition_expression = Key(key).eq(value)
            continue
        key_condition_expression &= Key(key).eq(value)
    return key_condition_expression


def mk_update_expression(update={}):
    update_expression = 'SET '
    expression_attribute_values = {}
    expressions = []
    for key, val in update.items():
        expressions.append(f'{key} = :{key.lower()}')
        expression_attribute_values[f':{key.lower()}'] = val
    update_expression += ", ".join(expressions)
    logger.info(f'Update expression: {update_expression}')
    logger.info(f'Expression attr values {expression_attribute_values}')
    return update_expression, expression_attribute_values


def query_items_with_pk(table, pk: DynamoPrimaryKey, limit=200, cursor_token=None):
    """
    Performs an efficient query operation on the user events table
    to produce a list of results and a 'LastEvaluatedKey' which if set
    can be passed in again to achieve cursor pagination.
    """
    key_condition_expression = mk_key_condition_expression(pk)

    # Note, table.query requires a KeyConditionExpression;
    # to query everything use db.scan_by_attributes
    query_args = {
        'KeyConditionExpression': key_condition_expression,  # Required
        'Limit': limit,
    }
    if cursor_token:
        decoder_cursor_token = decode_token_to_key(cursor_token)
        query_args['ExclusiveStartKey'] = decoder_cursor_token

    response = table.query(**query_args)
    response_last_evaluated_key = response.get('LastEvaluatedKey')
    encoded_cursor_token = None

    if response_last_evaluated_key:
        encoded_cursor_token = encode_key_as_token(response_last_evaluated_key)

    items = response['Items']
    logger.info(f'Dynamo response items from pk: {items},\n with encoded cursor:{encoded_cursor_token}')
    return items, encoded_cursor_token


def scan_by_attributes(table, attrs={}, limit=200, cursor_token=None):
        """
        Similar to fetch_items_by_pk except that it provides the capability
        to perform a scan on the table by attributes
        """
        attr_condition_expression = None
        for attr, value in attrs.items():
            if not attr_condition_expression:
                attr_condition_expression = Attr(attr).eq(value)
                continue
            attr_condition_expression &= Attr(attr).eq(value)

        scan_args = {
            'Limit': limit,
        }
        if attr_condition_expression:
            scan_args['FilterExpression'] = attr_condition_expression
        if cursor_token:
            decoder_cursor_token = decode_token_to_key(cursor_token)
            scan_args['ExclusiveStartKey'] = decoder_cursor_token

        response = table.scan(**scan_args)
        response_last_evaluated_key = response.get('LastEvaluatedKey')
        encoded_cursor_token = None
        
        if response_last_evaluated_key:
            encoded_cursor_token = encode_key_as_token(response_last_evaluated_key)
        items = response['Items']
        return items, encoded_cursor_token


def update_dynamo_record(table, pk={}, update={}):
    """
    Updates an existing item in dynamo
    """
    if update is not None:
        record = mk_dynamo_record(update)
        update_expression, expression_attribute_values = mk_update_expression(record)
        logger.info(f'Updating record {record}')
    resp = table.update_item(
        Key=pk,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values
    )
    logger.info(f'Dynamo response {resp}')
    return resp


def delete_dynamo_record(table, pk={}, update={}):
    """
    Deletes a record from dynamo

    Only to be used in rare cases. Most of the time, we want to de-activate records
    """
    # if update is not None:
    #     record = mk_dynamo_record(update)
    #     update_expression, expression_attribute_values = mk_update_expression(record)
    #     logger.info(f'Deleting record {record}')
    return table.delete_item(
        Key=pk,
        # UpdateExpression=update_expression,
        # ExpressionAttributeValues=expression_attribute_values
    )


def fetch_items_by_gsi(table, pk: DynamoPrimaryKey, indexName, limit=200,  cursor_token=None):
    """
    Performs an efficient query operation on the user events table
    to produce a list of results and a 'LastEvaluatedKey' which if set
    can be passed in again to achieve cursor pagination.
    """
    key_condition_expression = mk_key_condition_expression(pk)

    # Note, table.query requires a KeyConditionExpression;
    # to query everything use db.scan_by_attributes
    query_args = {
        'KeyConditionExpression': key_condition_expression,  # Required
        'IndexName': indexName,
        'Limit': limit,
    }
    if cursor_token:
        decoder_cursor_token = decode_token_to_key(cursor_token)
        query_args['ExclusiveStartKey'] = decoder_cursor_token

    response = table.query(**query_args)
    response_last_evaluated_key = response.get('LastEvaluatedKey')
    encoded_cursor_token = None

    if response_last_evaluated_key:
        encoded_cursor_token = encode_key_as_token(response_last_evaluated_key)

    items = response['Items']
    logger.info(
        f'Dynamo response items from pk: {items},\n with encoded cursor:{encoded_cursor_token}')
    return items, encoded_cursor_token
