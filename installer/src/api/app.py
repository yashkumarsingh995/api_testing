"""
Initial FastAPI App Setup
"""
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from constants import SERVICE_NAME

logger = logging.getLogger()
logger.setLevel(logging.INFO)

STAGE = os.environ.get('STAGE')

def create_app():
    """
    Setup app
    """
    app = FastAPI(
        title=f'{SERVICE_NAME}'
    )

    # Documentation for FastAPI CORS here: https://fastapi.tiangolo.com/tutorial/cors/
    origins = [
        'http://localhost',
        'http://localhost:3000',
        'http://localhost:3001',
        'https://d10hfuvgyvf0sb.cloudfront.net',
        'https://d33lku6mjhkiuq.cloudfront.net',
        'https://admin--api--{STAGE}.rcdevel.com',
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
        expose_headers=['Content-Range']
    )

    @app.middleware('http')
    async def middleware_logging(request: Request, call_next):
        """
        Middleware for each request to log simple information about it.
        """
        logging.info('Logging request. Method: %s on path of: %s',
                     request.method, request.url.path)
        return await call_next(request)

    return app
