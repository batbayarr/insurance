import os
from django.conf import settings
from django.utils import timezone
from datetime import date

def get_available_databases(company_code=None):
    """
    Read available databases from databases.txt file
    If company_code is provided, return only databases for that company
    """
    databases = []
    db_file_path = os.path.join(settings.BASE_DIR, 'databases.txt')
    
    try:
        with open(db_file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse CSV format: company_code,database_name,description
                    parts = line.split(',')
                    if len(parts) >= 2:
                        db_company_code = parts[0].strip()
                        db_name = parts[1].strip()
                        description = parts[2].strip().strip('"') if len(parts) > 2 else db_name
                        
                        # If company_code is specified, filter by it
                        if company_code is None or db_company_code == company_code:
                            databases.append({
                                'db_name': db_name,
                                'description': description,
                                'company_code': db_company_code
                            })
    except FileNotFoundError:
        # If file doesn't exist, return default database
        databases = [{'db_name': 'silicon4', 'description': 'Default Database', 'company_code': 'default'}]
    
    return databases

def set_database(db_name):
    """
    Set the database name for the current request context only.
    No global settings mutation; safe for concurrent users.
    Uses thread-local storage to ensure per-request isolation.
    """
    from .thread_local import set_current_db
    set_current_db(db_name)

def get_database_description(company_code, db_name):
    """
    Get the description for a specific database and company code
    """
    databases = get_available_databases(company_code)
    for db in databases:
        if db['db_name'] == db_name:
            return db['description']
    return db_name  # Fallback to database name if not found

def check_dep_expense_after_date(document_date):
    """
    Check if depreciation expenses exist in periods that start on or after the given document date.
    
    Args:
        document_date: A date object or string in 'YYYY-MM-DD' format representing the document date
        
    Returns:
        bool: True if depreciation expenses exist in periods with BeginDate >= document_date, False otherwise
        
    Example:
        >>> from datetime import date
        >>> check_dep_expense_after_date(date(2024, 1, 15))
        True  # or False
    """
    # Import here to avoid circular imports
    from core.models import AstDepreciationExpense
    
    # Convert string to date if needed
    if isinstance(document_date, str):
        from datetime import datetime
        document_date = datetime.strptime(document_date, '%Y-%m-%d').date()
    elif isinstance(document_date, timezone.datetime):
        document_date = document_date.date()
    
    # Check if any depreciation expenses exist where period BeginDate >= document_date
    return AstDepreciationExpense.objects.filter(
        PeriodId__BeginDate__gte=document_date
    ).exists() 