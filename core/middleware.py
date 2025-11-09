from .thread_local import set_current_db, clear_current_db
import logging

logger = logging.getLogger('core')

class DatabaseSelectionMiddleware:
    """
    Middleware to set the selected database based on user session (per-request).
    Uses thread-local storage to ensure each request is isolated to its correct database.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get the selected database from session
        selected_db = request.session.get('selected_database', 'silicon4')
        company_code = request.session.get('company_code', '')
        
        # Set per-request DB context (thread-local)
        set_current_db(selected_db)
        
        # Log database switches for monitoring
        if hasattr(request, 'user') and request.user.is_authenticated:
            if not hasattr(request, '_db_logged'):
                logger.debug(f"User {request.user.username} using database {selected_db} for company {company_code}")
                request._db_logged = True
        
        try:
            # Process the request
            response = self.get_response(request)
            return response
        finally:
            # Ensure cleanup of thread-local to avoid any leakage
            clear_current_db()


class NoCacheMiddleware:
    """
    Middleware to add no-cache headers to HTML responses to prevent browser caching.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only add no-cache headers for HTML responses
        if response.get('Content-Type', '').startswith('text/html'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response 