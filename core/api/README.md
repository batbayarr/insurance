# Django Ninja API Documentation

This directory contains the Django Ninja API implementation for the Silicon-AI Insurance system.

## Structure

```
core/api/
├── __init__.py
├── router.py          # Main API router
├── schemas.py         # Base Pydantic schemas
├── auth.py            # Authentication utilities
└── insurance/         # Insurance module APIs
    ├── __init__.py
    ├── router.py      # Insurance router
    ├── schemas.py     # Insurance schemas
    └── policy.py      # Policy endpoints
```

## Installation

Django Ninja is already added to `requirements.txt`. Install it with:

```bash
pip install -r requirements.txt
```

## Usage

### Accessing the API

- **API Documentation (Swagger UI)**: http://localhost:8000/api/docs
- **OpenAPI Schema**: http://localhost:8000/api/openapi.json
- **API Base URL**: http://localhost:8000/api/

### Example: Policy Templates

```python
# List all policy templates
GET /api/insurance/policy/templates

# Get a specific template
GET /api/insurance/policy/templates/{id}

# Create a new template
POST /api/insurance/policy/templates
{
    "PolicyTemplateName": "Auto Insurance",
    "PolicyTemplateCode": "AUTO001",
    "IsActive": true
}

# Update a template
PUT /api/insurance/policy/templates/{id}
{
    "PolicyTemplateName": "Updated Name",
    "IsActive": false
}

# Delete a template
DELETE /api/insurance/policy/templates/{id}
```

## Authentication

Currently using Django's session authentication. The `@login_required` decorator is used on all endpoints.

For API key authentication, see `auth.py` for the `APIKeyAuth` class.

## Adding New Endpoints

1. Create schemas in `insurance/schemas.py`
2. Add endpoints in `insurance/policy.py` (or create new files)
3. Register router in `insurance/router.py`
4. The endpoints will automatically appear in Swagger docs

## Benefits of Django Ninja

- **Performance**: Fast, similar to manual views
- **Type Safety**: Automatic validation with Pydantic
- **Auto Documentation**: Swagger UI generated automatically
- **Async Support**: Can handle async operations
- **Less Boilerplate**: Cleaner code than DRF

