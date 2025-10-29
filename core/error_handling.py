"""
Silicon4 Error Handling System - Backend
Comprehensive error handling for Django views and operations
"""

import logging
import traceback
from functools import wraps
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import DatabaseError, IntegrityError, transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

# Configure logging
logger = logging.getLogger(__name__)

# Error types and severity levels
class ErrorTypes:
    VALIDATION = 'validation'
    DATABASE = 'database'
    PERMISSION = 'permission'
    SYSTEM = 'system'
    NETWORK = 'network'
    BUSINESS_LOGIC = 'business_logic'

class ErrorSeverity:
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'

class Silicon4Error(Exception):
    """Custom exception class for Silicon4 errors"""
    def __init__(self, message, error_type=ErrorTypes.SYSTEM, severity=ErrorSeverity.MEDIUM, details=None):
        self.message = message
        self.error_type = error_type
        self.severity = severity
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(Silicon4Error):
    def __init__(self, message, details=None):
        super().__init__(message, ErrorTypes.VALIDATION, ErrorSeverity.MEDIUM, details)

class BusinessLogicError(Silicon4Error):
    def __init__(self, message, details=None):
        super().__init__(message, ErrorTypes.BUSINESS_LOGIC, ErrorSeverity.HIGH, details)

class DatabaseError(Silicon4Error):
    def __init__(self, message, details=None):
        super().__init__(message, ErrorTypes.DATABASE, ErrorSeverity.HIGH, details)

class PermissionError(Silicon4Error):
    def __init__(self, message, details=None):
        super().__init__(message, ErrorTypes.PERMISSION, ErrorSeverity.HIGH, details)

class ErrorHandler:
    """Main error handling class for backend operations"""
    
    @staticmethod
    def log_error(error, request=None, user=None):
        """Log error with context information"""
        error_context = {
            'error_type': getattr(error, 'error_type', ErrorTypes.SYSTEM),
            'severity': getattr(error, 'severity', ErrorSeverity.MEDIUM),
            'error_message': str(error),
            'details': getattr(error, 'details', {}),
            'user': str(user) if user else None,
            'user_id': user.id if user and hasattr(user, 'id') else None,
            'request_path': request.path if request else None,
            'request_method': request.method if request else None,
            'traceback': traceback.format_exc()
        }
        
        # Log based on severity
        severity = error_context['severity']
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f"CRITICAL ERROR: {error_context['error_message']}", extra=error_context)
        elif severity == ErrorSeverity.HIGH:
            logger.error(f"HIGH SEVERITY ERROR: {error_context['error_message']}", extra=error_context)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(f"MEDIUM SEVERITY ERROR: {error_context['error_message']}", extra=error_context)
        else:
            logger.info(f"LOW SEVERITY ERROR: {error_context['error_message']}", extra=error_context)
    
    @staticmethod
    def get_user_friendly_message(error):
        """Get user-friendly error message"""
        error_type = getattr(error, 'error_type', ErrorTypes.SYSTEM)
        severity = getattr(error, 'severity', ErrorSeverity.MEDIUM)
        
        messages = {
            ErrorTypes.VALIDATION: {
                ErrorSeverity.LOW: 'Please check your input and try again.',
                ErrorSeverity.MEDIUM: 'Please correct the highlighted fields and try again.',
                ErrorSeverity.HIGH: 'Please review all required fields and try again.',
                ErrorSeverity.CRITICAL: 'Form validation failed. Please contact support if this persists.'
            },
            ErrorTypes.DATABASE: {
                ErrorSeverity.MEDIUM: 'Database operation failed. Please try again.',
                ErrorSeverity.HIGH: 'Database error occurred. Please contact support.',
                ErrorSeverity.CRITICAL: 'Critical database error. Please contact support immediately.'
            },
            ErrorTypes.PERMISSION: {
                ErrorSeverity.MEDIUM: 'You do not have permission to perform this action.',
                ErrorSeverity.HIGH: 'Access denied. Please contact your administrator.',
                ErrorSeverity.CRITICAL: 'Security error. Please log out and log back in.'
            },
            ErrorTypes.BUSINESS_LOGIC: {
                ErrorSeverity.MEDIUM: 'Business rule violation. Please check your data.',
                ErrorSeverity.HIGH: 'Invalid operation. Please contact support.',
                ErrorSeverity.CRITICAL: 'Critical business logic error. Please contact support.'
            },
            ErrorTypes.SYSTEM: {
                ErrorSeverity.LOW: 'A minor system error occurred. Please try again.',
                ErrorSeverity.MEDIUM: 'System error occurred. Please refresh the page.',
                ErrorSeverity.HIGH: 'Critical system error. Please contact support.',
                ErrorSeverity.CRITICAL: 'Fatal system error. Please contact support immediately.'
            }
        }
        
        return messages.get(error_type, {}).get(severity, 'An unexpected error occurred. Please try again.')
    
    @staticmethod
    def handle_database_operation(operation, *args, **kwargs):
        """Handle database operations with error handling"""
        try:
            with transaction.atomic():
                return operation(*args, **kwargs)
        except IntegrityError as e:
            ErrorHandler.log_error(DatabaseError(f"Database integrity error: {str(e)}"))
            raise BusinessLogicError("Data integrity violation. Please check your input.")
        except DatabaseError as e:
            ErrorHandler.log_error(DatabaseError(f"Database error: {str(e)}"))
            raise DatabaseError("Database operation failed. Please try again.")
        except Exception as e:
            ErrorHandler.log_error(e)
            raise Silicon4Error("An unexpected error occurred during database operation.")

def handle_errors(error_type=ErrorTypes.SYSTEM, severity=ErrorSeverity.MEDIUM, return_json=False):
    """Decorator for handling errors in views"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                return view_func(request, *args, **kwargs)
            except Silicon4Error as e:
                ErrorHandler.log_error(e, request, request.user)
                user_message = ErrorHandler.get_user_friendly_message(e)
                
                if return_json:
                    return JsonResponse({
                        'success': False,
                        'error': user_message,
                        'error_type': e.error_type,
                        'severity': e.severity
                    }, status=400)
                else:
                    messages.error(request, user_message)
                    return HttpResponse(status=400)
                    
            except ValidationError as e:
                ErrorHandler.log_error(ValidationError(str(e)), request, request.user)
                user_message = "Please check your input and try again."
                
                if return_json:
                    return JsonResponse({
                        'success': False,
                        'error': user_message,
                        'error_type': ErrorTypes.VALIDATION,
                        'details': e.message_dict if hasattr(e, 'message_dict') else {}
                    }, status=400)
                else:
                    messages.error(request, user_message)
                    return HttpResponse(status=400)
                    
            except PermissionDenied as e:
                ErrorHandler.log_error(PermissionError(str(e)), request, request.user)
                user_message = "You do not have permission to perform this action."
                
                if return_json:
                    return JsonResponse({
                        'success': False,
                        'error': user_message,
                        'error_type': ErrorTypes.PERMISSION
                    }, status=403)
                else:
                    messages.error(request, user_message)
                    return HttpResponse(status=403)
                    
            except DatabaseError as e:
                ErrorHandler.log_error(DatabaseError(str(e)), request, request.user)
                user_message = "Database error occurred. Please try again."
                
                if return_json:
                    return JsonResponse({
                        'success': False,
                        'error': user_message,
                        'error_type': ErrorTypes.DATABASE
                    }, status=500)
                else:
                    messages.error(request, user_message)
                    return HttpResponse(status=500)
                    
            except Exception as e:
                ErrorHandler.log_error(Silicon4Error(str(e), error_type, severity), request, request.user)
                user_message = "An unexpected error occurred. Please try again."
                
                if return_json:
                    return JsonResponse({
                        'success': False,
                        'error': user_message,
                        'error_type': error_type
                    }, status=500)
                else:
                    messages.error(request, user_message)
                    return HttpResponse(status=500)
        
        return wrapper
    return decorator

def handle_ajax_errors(view_func):
    """Decorator specifically for AJAX views"""
    return handle_errors(return_json=True)(view_func)

def handle_form_errors(view_func):
    """Decorator specifically for form views"""
    return handle_errors(ErrorTypes.VALIDATION, ErrorSeverity.MEDIUM, return_json=False)(view_func)

def safe_database_operation(operation, *args, **kwargs):
    """Safely execute database operations"""
    return ErrorHandler.handle_database_operation(operation, *args, **kwargs)

# API endpoint for logging frontend errors
@csrf_exempt
@require_http_methods(["POST"])
def log_frontend_error(request):
    """API endpoint to receive frontend error logs"""
    try:
        error_data = json.loads(request.body)
        
        # Log the frontend error
        logger.warning(f"Frontend Error: {error_data.get('message', 'Unknown error')}", extra={
            'frontend_error': error_data,
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'ip_address': request.META.get('REMOTE_ADDR'),
            'error_message': error_data.get('message', 'Unknown error')
        })
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Failed to log frontend error: {str(e)}")
        return JsonResponse({'success': False}, status=500)

# Utility functions for common error scenarios
def validate_required_fields(data, required_fields):
    """Validate required fields in data"""
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    return True

def validate_user_permissions(user, required_permission):
    """Validate user permissions"""
    if not user.has_perm(required_permission):
        raise PermissionError(f"User {user.username} does not have permission: {required_permission}")
    
    return True

def validate_business_rules(data, rules):
    """Validate business rules"""
    for rule_name, rule_func in rules.items():
        try:
            if not rule_func(data):
                raise BusinessLogicError(f"Business rule violation: {rule_name}")
        except Exception as e:
            raise BusinessLogicError(f"Business rule validation failed: {rule_name} - {str(e)}")
    
    return True
