"""Helper methods for api"""
import json
from typing import Union
from urllib.parse import parse_qs


def build_content_range_header(resource: str, items: list, start: Union[None, int], end: Union[None, int]):
    """
    Builds the Content-Range header with React Admin params, or, if no RA
    parameters are present, calculates the range from start=0
    """
    if start == None:
        start = 0
    if end == None:
        end = len(items)
    return f'{resource} {start}-{end}/{len(items)}'



def filter_results(response_data, search, search_fields):
    """filtering for search"""
    search_data = []
    for field in search_fields:
        for item in response_data:
            if field not in item:
                continue
            if search.lower() in str(item[field]).lower() and item not in search_data:
                search_data.append(item)
    return search_data


def parse_params(req_url):
    """parse query parameters"""
    start, end, field, order, search = None, None, None, None, None
    params = parse_qs(req_url.query)
    if 'filter' in params:
        search_field = json.loads(params['filter'][0])
        search = search_field.get('q')
    # pagination from react admin range query
    if 'range' in params:
        start, end = json.loads(params['range'][0])
        end = end + 1
    # field to sort by and order from react admin query param
    if 'sort' in params:
        field, order = json.loads(params['sort'][0])
    return start, end, field, order, search
