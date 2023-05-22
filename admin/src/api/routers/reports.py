import json
from operator import itemgetter
from typing import List
from urllib.parse import parse_qs

from db import reportsData
from fastapi import APIRouter, Request, Response
from models import ReportsResponse
from utils import filter_results, parse_params

router = APIRouter()


@router.get('/reports', response_model=List[ReportsResponse])
def get_reports(request: Request, response: Response) -> dict:
    """/reports endpoint with pagination and sorting from query params"""
    # get query params
    req_url = request.url
    start, end, field, order, search = parse_params(req_url)

    data = sorted(reportsData, key=itemgetter(
        field), reverse=bool(order == 'DESC'))
    if search:
        search_fields = ['type', 'user']
        search_result = filter_results(data, search, search_fields)
        response.headers['Content-Range'] = f'reports {start}-{end}/{len(search_result)}'
        return [ReportsResponse(**u) for u in search_result[start:end]]

    response.headers['Content-Range'] = f'reports {start}-{end}/{len(reportsData)}'

    return [ReportsResponse(**d) for d in data[start:end]]
