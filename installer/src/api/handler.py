"""
Setup for endpoints for the auth api service
"""
import os

from mangum import Mangum

from app import create_app
from models import HealthResponse
from routers import alerts, background_check, installers, jobs, messages, payments, scheduling

app = create_app()


@app.get('/health', response_model=HealthResponse)
def get_health():
    """
    Gets our health endpoint
    """
    return HealthResponse(**{'GIT_HASH': os.environ.get('GIT_HASH', 'dev')})


app.include_router(alerts.router)
app.include_router(background_check.router)
app.include_router(installers.router)
app.include_router(jobs.router)
app.include_router(messages.router)
app.include_router(payments.router)
app.include_router(scheduling.router)

handler = Mangum(app)
