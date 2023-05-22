"""
Setup for endpoints for the auth api service
"""
import os
from constants import SERVICE_NAME
from fastapi import Response
from mangum import Mangum

from app import create_app
from routers import alerts, customers, jobs, messages, scheduling

app = create_app()

@app.get("/health")
def get_health():
    """
    Gets our health endpoint
    """
    return Response(os.environ.get('GIT_HASH', 'healthy'), 200)

app.include_router(alerts.router)
app.include_router(customers.router)
app.include_router(jobs.router)
app.include_router(messages.router)
app.include_router(scheduling.router)


handler = Mangum(app)
