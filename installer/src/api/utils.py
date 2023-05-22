"""Helper methods for api"""
import json
from urllib.parse import parse_qs

def parse_params(req_url):
    """parse query parameters"""
    params = parse_qs(req_url.query)
    search_field = json.loads(params['filter'][0])
    search = search_field.get('q')
    
    # pagination from react admin range query
    start, end = json.loads(params['range'][0])
    # field to sort by and order from react admin query param
    field, order = json.loads(params['sort'][0])

    return start, end + 1, field, order, search

def filter_results(response_data, search, search_fields):
    """filtering for search"""
    search_data = []
    for field in search_fields:
        for item in response_data:
            if search.lower() in str(item[field]).lower() and item not in search_data:
                search_data.append(item)
    return search_data