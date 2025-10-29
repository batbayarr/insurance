from .utils import set_database
import logging

logger = logging.getLogger('core')

class DatabaseSelectionMiddleware:
    """
    Middleware to set the selected database based on user session
    Enhanced with connection pooling support and audit logging
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get the selected database from session
        selected_db = request.session.get('selected_database', 'silicon4')
        company_code = request.session.get('company_code', '')
        
        # Set the database name in settings
        set_database(selected_db)
        
        # Log database switches for monitoring
        if hasattr(request, 'user') and request.user.is_authenticated:
            if not hasattr(request, '_db_logged'):
                logger.debug(f"User {request.user.username} using database {selected_db} for company {company_code}")
                request._db_logged = True
        
        # Process the request
        response = self.get_response(request)
        
        return response 