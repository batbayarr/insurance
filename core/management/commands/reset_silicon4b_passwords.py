from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = 'Reset passwords for users in silicon4b database'

    def handle(self, *args, **options):
        # Set the database to silicon4b
        from django.conf import settings
        settings.DATABASES['default']['NAME'] = 'silicon4b'
        
        # Reset passwords for all users
        users = User.objects.all()
        
        for user in users:
            # Set a simple password for testing
            if user.username == 'admin':
                user.password = make_password('admin123')
            elif user.username == 'manager1':
                user.password = make_password('manager123')
            elif user.username == 'user1':
                user.password = make_password('user123')
            else:
                user.password = make_password('password123')
            
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Reset password for user: {user.username}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('All passwords have been reset!')
        )
        self.stdout.write('Use these passwords to login:')
        self.stdout.write('- admin: admin123')
        self.stdout.write('- manager1: manager123')
        self.stdout.write('- user1: user123') 