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