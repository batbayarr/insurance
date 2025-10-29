"""
Unicode Middleware for handling encoding issues on Windows
"""

import sys
import logging

logger = logging.getLogger(__name__)

class UnicodeMiddleware:
    """Middleware to handle Unicode encoding issues"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Set up proper encoding for Windows
        if sys.platform.startswith('win'):
            import codecs
            import locale
            
            # Set UTF-8 encoding for stdout and stderr without detaching
            try:
                # Only set encoding if streams haven't been modified yet
                if hasattr(sys.stdout, 'buffer') and not hasattr(sys.stdout, '_encoding_set'):
                    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
                    sys.stdout._encoding_set = True
                if hasattr(sys.stderr, 'buffer') and not hasattr(sys.stderr, '_encoding_set'):
                    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
                    sys.stderr._encoding_set = True
            except Exception as e:
                logger.warning(f"Could not set UTF-8 encoding for stdout/stderr: {e}")
            
            # Set locale to UTF-8 if possible
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
                except locale.Error:
                    logger.warning("Could not set UTF-8 locale")

    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        
        # Ensure response has proper encoding
        if hasattr(response, 'content'):
            try:
                # Ensure content is properly encoded
                if isinstance(response.content, bytes):
                    response.content.decode('utf-8')
            except UnicodeDecodeError:
                logger.warning("Response content has encoding issues")
        
        return response
