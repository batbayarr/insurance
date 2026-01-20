"""
Authentication utilities for Django Ninja API
"""
from ninja.security import HttpBearer, APIKeyHeader
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from typing import Optional

User = get_user_model()


def django_auth(request):
    """
    Django session-based authentication function
    This works with Django's built-in session authentication
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        return request.user
    return None


# Alternative: API Key authentication (if needed)
class APIKeyAuth(APIKeyHeader):
    """
    API Key authentication for external API access
    """
    param_name = "X-API-Key"
    
    def authenticate(self, request, key: Optional[str]):
        if not key:
            return None
        try:
            # Implement your API key validation logic here
            # Example: user = User.objects.get(api_key=key)
            # return user
            return None
        except:
            return None

