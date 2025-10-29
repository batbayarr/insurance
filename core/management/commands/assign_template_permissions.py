from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Assign template permissions to user groups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to assign permissions to',
        )

    def handle(self, *args, **options):
        # Get template permissions (only main template permissions)
        template_permissions = Permission.objects.filter(
            codename__in=[
                'add_ref_template',
                'change_ref_template', 
                'delete_ref_template',
                'view_ref_template',
            ]
        )

        # Create or get groups
        admin_group, created = Group.objects.get_or_create(name='Template Admins')
        if created:
            self.stdout.write(self.style.SUCCESS('Created group: Template Admins'))
        
        user_group, created = Group.objects.get_or_create(name='Template Users')
        if created:
            self.stdout.write(self.style.SUCCESS('Created group: Template Users'))

        # Assign permissions to groups
        # Template Admins get all permissions
        admin_group.permissions.set(template_permissions)
        self.stdout.write(
            self.style.SUCCESS(f'Assigned all template permissions to Template Admins group')
        )

        # Template Users get only view permissions
        view_permissions = template_permissions.filter(
            codename__in=['view_ref_template']
        )
        user_group.permissions.set(view_permissions)
        self.stdout.write(
            self.style.SUCCESS(f'Assigned view permissions to Template Users group')
        )

        # If username provided, assign to specific user
        if options['username']:
            try:
                user = User.objects.get(username=options['username'])
                
                # Add user to Template Admins group
                user.groups.add(admin_group)
                self.stdout.write(
                    self.style.SUCCESS(f'Added user {options["username"]} to Template Admins group')
                )
                
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User {options["username"]} does not exist')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully assigned template permissions!')
        )
