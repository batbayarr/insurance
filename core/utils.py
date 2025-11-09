import os
from django.conf import settings

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