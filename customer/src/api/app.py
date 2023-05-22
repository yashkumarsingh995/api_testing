"""
Initial FastAPI App Setup
"""
import logging
from constants import SERVICE_NAME

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def create_app():
    """
    Setup app
    """
    app = FastAPI(
        title=f'{SERVICE_NAME}'
    )

    # Documentation for FastAPI CORS here: https://fastapi.tiangolo.com/tutorial/cors/
    origins = [
        "http://localhost",
        "http://localhost:3000",  # Default port for react-admin
        # Backup port RA uses in case something is already running there
        "http://localhost:3001",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=['Content-Range']
    )

    @app.middleware("http")
    async def middleware_logging(request: Request, call_next):
        """
        Middleware for each request to log simple information about it.
        """
        logging.info('Logging request. Method: %s on path of: %s',
                     request.method, request.url.path)
        return await call_next(request)

    return app
