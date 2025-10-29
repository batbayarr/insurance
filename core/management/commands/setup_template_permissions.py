from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Ref_Template


class Command(BaseCommand):
    help = 'Setup permissions for Ref_Template model'

    def handle(self, *args, **options):
        # Get content type for the template model
        template_ct = ContentType.objects.get_for_model(Ref_Template)

        # Define permissions for Ref_Template only
        template_permissions = [
            ('add_ref_template', 'Can add template'),
            ('change_ref_template', 'Can change template'),
            ('delete_ref_template', 'Can delete template'),
            ('view_ref_template', 'Can view template'),
        ]

        # Create permissions for Ref_Template
        for codename, name in template_permissions:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=template_ct,
                defaults={'name': name}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created permission: {codename}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Permission already exists: {codename}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully setup template permissions!')
        )
