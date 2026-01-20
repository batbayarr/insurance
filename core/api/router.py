"""
Main API router for Django Ninja
"""
from ninja import NinjaAPI
from django.conf import settings
from .auth import django_auth

# Create the main API instance
api = NinjaAPI(
    title="Silicon-AI Insurance API",
    version="1.0.0",
    description="API for Silicon-AI Insurance Management System",
    docs_url="/api/docs",  # Swagger UI
    openapi_url="/api/openapi.json",  # OpenAPI schema
    auth=django_auth,  # Default authentication for all endpoints
)

# Import and include routers here
from .insurance.router import router as insurance_router

api.add_router("/insurance", insurance_router)

