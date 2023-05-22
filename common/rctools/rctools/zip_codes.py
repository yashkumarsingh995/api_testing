import logging

from rctools.aws.s3 import get_object_from_s3
from rctools.aws.dynamodb import fetch_items_by_pk, DynamoPrimaryKey
from typing import Literal, Union


logger = logging.getLogger()
logger.setLevel(logging.INFO)


ValidRadius = Union[Literal[10], Literal[25], Literal[50], Literal[75], Literal[100], Literal[200], Literal[500]]


def get_installers_by_zip(table, zip_code: str):
    """
    Queries the service area table and returns all installer IDs that service that zip
    """
    pk = DynamoPrimaryKey()
    pk = {'zip_code': zip_code}
    items, pagination_token = [], None
    while True:
        rows, cursor_token = fetch_items_by_pk(table, pk, cursor_token=pagination_token)
        items += rows
        if not cursor_token:
            break
        pagination_token = cursor_token
    return [r['installer_id'] for r in items]
    

def get_zip_codes_in_radius(s3_client, bucket: str, zip_code: str, radius: ValidRadius):
    """
    Returns the zip codes that are within the given radius of the home zip code.
    """
    result = []
    try:
        key = f'zips/{zip_code}.min.json'
        zips = get_object_from_s3(s3_client, bucket, key)
        for r in zips.keys():
            if int(r) <= int(radius):
                result += zips[r]
    except:
        logger.exception(f'There was an error returning nearby zip codes for {zip_code} and radius {radius}')
    return result
