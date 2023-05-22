"""
Setup for endpoints for the auth api service
"""
import os

from mangum import Mangum

from app import create_app
from models import HealthResponse
from routers import admin, company, customers, installers


app = create_app()

@app.get('/health', response_model=HealthResponse)
def get_health():
    """
    Gets our health endpoint
    """
    return HealthResponse(**{'GIT_HASH': os.environ.get('GIT_HASH', 'dev')})


app.include_router(admin.router)
app.include_router(company.router)
app.include_router(customers.router)
app.include_router(installers.router)
# app.include_router(payment.router)

handler = Mangum(app)
