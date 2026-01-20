from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from core.models import (
    Policy_Main,
    Policy_Main_Coinsurance,
    Policy_Main_Schedule,
    Policy_Main_Files,
    Policy_Main_Product,
    Policy_Main_Product_Item,
    Policy_Main_Product_Item_Risk,
    Policy_Main_Product_Item_Question
)


class Command(BaseCommand):
    help = 'Setup permissions for Insurance Policy models'

    def handle(self, *args, **options):
        self.stdout.write('Setting up insurance permissions...')
        
        # Get content types for all Policy models
        policy_main_ct = ContentType.objects.get_for_model(Policy_Main)
        policy_coinsurance_ct = ContentType.objects.get_for_model(Policy_Main_Coinsurance)
        policy_schedule_ct = ContentType.objects.get_for_model(Policy_Main_Schedule)
        policy_files_ct = ContentType.objects.get_for_model(Policy_Main_Files)
        policy_product_ct = ContentType.objects.get_for_model(Policy_Main_Product)
        policy_product_item_ct = ContentType.objects.get_for_model(Policy_Main_Product_Item)
        policy_product_item_risk_ct = ContentType.objects.get_for_model(Policy_Main_Product_Item_Risk)
        policy_product_item_question_ct = ContentType.objects.get_for_model(Policy_Main_Product_Item_Question)
        
        # Define permissions for all Policy models
        permissions = [
            # Policy_Main permissions
            ('view_policy_main', 'Can view policy', policy_main_ct),
            ('add_policy_main', 'Can add policy', policy_main_ct),
            ('change_policy_main', 'Can change policy', policy_main_ct),
            ('delete_policy_main', 'Can delete policy', policy_main_ct),
            
            # Policy_Main_Coinsurance permissions
            ('view_policy_main_coinsurance', 'Can view policy coinsurance', policy_coinsurance_ct),
            ('add_policy_main_coinsurance', 'Can add policy coinsurance', policy_coinsurance_ct),
            ('change_policy_main_coinsurance', 'Can change policy coinsurance', policy_coinsurance_ct),
            ('delete_policy_main_coinsurance', 'Can delete policy coinsurance', policy_coinsurance_ct),
            
            # Policy_Main_Schedule permissions
            ('view_policy_main_schedule', 'Can view policy payment schedule', policy_schedule_ct),
            ('add_policy_main_schedule', 'Can add policy payment schedule', policy_schedule_ct),
            ('change_policy_main_schedule', 'Can change policy payment schedule', policy_schedule_ct),
            ('delete_policy_main_schedule', 'Can delete policy payment schedule', policy_schedule_ct),
            
            # Policy_Main_Files permissions
            ('view_policy_main_files', 'Can view policy file', policy_files_ct),
            ('add_policy_main_files', 'Can add policy file', policy_files_ct),
            ('change_policy_main_files', 'Can change policy file', policy_files_ct),
            ('delete_policy_main_files', 'Can delete policy file', policy_files_ct),
            
            # Policy_Main_Product permissions
            ('view_policy_main_product', 'Can view policy product', policy_product_ct),
            ('add_policy_main_product', 'Can add policy product', policy_product_ct),
            ('change_policy_main_product', 'Can change policy product', policy_product_ct),
            ('delete_policy_main_product', 'Can delete policy product', policy_product_ct),
            
            # Policy_Main_Product_Item permissions
            ('view_policy_main_product_item', 'Can view policy product item', policy_product_item_ct),
            ('add_policy_main_product_item', 'Can add policy product item', policy_product_item_ct),
            ('change_policy_main_product_item', 'Can change policy product item', policy_product_item_ct),
            ('delete_policy_main_product_item', 'Can delete policy product item', policy_product_item_ct),
            
            # Policy_Main_Product_Item_Risk permissions
            ('view_policy_main_product_item_risk', 'Can view policy product item risk', policy_product_item_risk_ct),
            ('add_policy_main_product_item_risk', 'Can add policy product item risk', policy_product_item_risk_ct),
            ('change_policy_main_product_item_risk', 'Can change policy product item risk', policy_product_item_risk_ct),
            ('delete_policy_main_product_item_risk', 'Can delete policy product item risk', policy_product_item_risk_ct),
            
            # Policy_Main_Product_Item_Question permissions
            ('view_policy_main_product_item_question', 'Can view policy product item question', policy_product_item_question_ct),
            ('add_policy_main_product_item_question', 'Can add policy product item question', policy_product_item_question_ct),
            ('change_policy_main_product_item_question', 'Can change policy product item question', policy_product_item_question_ct),
            ('delete_policy_main_product_item_question', 'Can delete policy product item question', policy_product_item_question_ct),
        ]
        
        # Create permissions
        created_count = 0
        existing_count = 0
        
        for codename, name, content_type in permissions:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created permission: {name} ({codename})')
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'○ Permission already exists: {name} ({codename})')
                )
                existing_count += 1
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully setup insurance permissions! '
                f'Created: {created_count}, Already existed: {existing_count}'
            )
        )
        self.stdout.write('')
        self.stdout.write('Insurance permissions are now available in Django admin.')
        self.stdout.write('You can assign them to user groups via:')
        self.stdout.write('  - Django Admin > Authentication and Authorization > Groups')
        self.stdout.write('  - Or use: python manage.py assign_insurance_permissions --group <group_name>')

