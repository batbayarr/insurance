from django.conf import settings
from .thread_local import get_current_db


class MultiTenantRouter:
    """
    Database router that dynamically creates per-tenant database connections
    based on thread-local storage. Each request gets isolated to its correct database.
    """
    
    def db_for_read(self, model, **hints):
        """Route read queries to the tenant-specific database."""
        # Always use default database for sessions
        if model and model._meta.app_label == 'sessions':
            return 'default'
        return self._get_tenant_db()
    
    def db_for_write(self, model, **hints):
        """Route write queries to the tenant-specific database."""
        # Always use default database for sessions
        if model and model._meta.app_label == 'sessions':
            return 'default'
        return self._get_tenant_db()
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Only allow migrations on the default database (admin/seed database)."""
        return db == 'default'
    
    def _get_tenant_db(self):
        """Get the current tenant database name from thread-local storage."""
        tenant_db = get_current_db()
        
        # Dynamically create database configuration for this tenant
        # by cloning the default config and changing only the NAME
        if tenant_db not in settings.DATABASES:
            self._create_tenant_db_config(tenant_db)
        
        return tenant_db
    
    def _create_tenant_db_config(self, db_name):
        """Create a database configuration for the tenant by cloning the default config."""
        from django.conf import settings
        
        # Clone the default database configuration
        default_config = settings.DATABASES['default'].copy()
        default_config['NAME'] = db_name
        
        # Add the tenant database to settings
        settings.DATABASES[db_name] = default_config
