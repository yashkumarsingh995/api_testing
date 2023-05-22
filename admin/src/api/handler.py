"""
Setup for endpoints for the auth api service
"""
import os

from app import create_app
from mangum import Mangum
from models import HealthResponse
from routers import (admins, companies, customers, dashboard, installers,
                     job_tickets, payments, profile, reports, scheduling)

app = create_app()


@app.get('/health', response_model=HealthResponse)
def get_health():
    """
    Gets our health endpoint
    """
    return HealthResponse(**{'GIT_HASH': os.environ.get('GIT_HASH', 'dev')})


app.include_router(admins.router)
app.include_router(companies.router)
app.include_router(customers.router)
app.include_router(dashboard.router)
app.include_router(installers.router)
app.include_router(job_tickets.router)
app.include_router(payments.router)
app.include_router(profile.router)
app.include_router(reports.router)
app.include_router(scheduling.router)
app.include_router(payments.router)

handler = Mangum(app)
