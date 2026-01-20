from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
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
    help = 'Assign insurance permissions to user groups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--group',
            type=str,
            help='Group name to assign permissions to',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Assign all insurance permissions (view, add, change, delete)',
        )
        parser.add_argument(
            '--view-only',
            action='store_true',
            help='Assign only view permissions',
        )

    def handle(self, *args, **options):
        group_name = options.get('group')
        assign_all = options.get('all', False)
        view_only = options.get('view_only', False)
        
        # Get content types
        policy_main_ct = ContentType.objects.get_for_model(Policy_Main)
        policy_coinsurance_ct = ContentType.objects.get_for_model(Policy_Main_Coinsurance)
        policy_schedule_ct = ContentType.objects.get_for_model(Policy_Main_Schedule)
        policy_files_ct = ContentType.objects.get_for_model(Policy_Main_Files)
        policy_product_ct = ContentType.objects.get_for_model(Policy_Main_Product)
        policy_product_item_ct = ContentType.objects.get_for_model(Policy_Main_Product_Item)
        policy_product_item_risk_ct = ContentType.objects.get_for_model(Policy_Main_Product_Item_Risk)
        policy_product_item_question_ct = ContentType.objects.get_for_model(Policy_Main_Product_Item_Question)
        
        # Define all insurance permission codenames
        all_permissions = [
            # Policy_Main
            'view_policy_main', 'add_policy_main', 'change_policy_main', 'delete_policy_main',
            # Policy_Main_Coinsurance
            'view_policy_main_coinsurance', 'add_policy_main_coinsurance', 
            'change_policy_main_coinsurance', 'delete_policy_main_coinsurance',
            # Policy_Main_Schedule
            'view_policy_main_schedule', 'add_policy_main_schedule',
            'change_policy_main_schedule', 'delete_policy_main_schedule',
            # Policy_Main_Files
            'view_policy_main_files', 'add_policy_main_files',
            'change_policy_main_files', 'delete_policy_main_files',
            # Policy_Main_Product
            'view_policy_main_product', 'add_policy_main_product',
            'change_policy_main_product', 'delete_policy_main_product',
            # Policy_Main_Product_Item
            'view_policy_main_product_item', 'add_policy_main_product_item',
            'change_policy_main_product_item', 'delete_policy_main_product_item',
            # Policy_Main_Product_Item_Risk
            'view_policy_main_product_item_risk', 'add_policy_main_product_item_risk',
            'change_policy_main_product_item_risk', 'delete_policy_main_product_item_risk',
            # Policy_Main_Product_Item_Question
            'view_policy_main_product_item_question', 'add_policy_main_product_item_question',
            'change_policy_main_product_item_question', 'delete_policy_main_product_item_question',
        ]
        
        # Content type mapping for permissions
        content_type_map = {
            'policy_main': policy_main_ct,
            'policy_main_coinsurance': policy_coinsurance_ct,
            'policy_main_schedule': policy_schedule_ct,
            'policy_main_files': policy_files_ct,
            'policy_main_product': policy_product_ct,
            'policy_main_product_item': policy_product_item_ct,
            'policy_main_product_item_risk': policy_product_item_risk_ct,
            'policy_main_product_item_question': policy_product_item_question_ct,
        }
        
        # Determine which permissions to assign
        if view_only:
            permissions_to_assign = [p for p in all_permissions if p.startswith('view_')]
        elif assign_all:
            permissions_to_assign = all_permissions
        else:
            # Default: assign all if no flag specified
            permissions_to_assign = all_permissions
        
        if group_name:
            # Assign to specific group
            try:
                group = Group.objects.get(name=group_name)
                self.stdout.write(f'Assigning permissions to group: {group_name}')
                
                assigned_count = 0
                for perm_codename in permissions_to_assign:
                    # Determine content type from permission codename
                    content_type = None
                    for key, ct in content_type_map.items():
                        if key in perm_codename:
                            content_type = ct
                            break
                    
                    if not content_type:
                        # Fallback: try to get from permission directly
                        try:
                            permission = Permission.objects.get(codename=perm_codename)
                            content_type = permission.content_type
                        except Permission.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(f'Permission not found: {perm_codename}')
                            )
                            continue
                    
                    try:
                        permission = Permission.objects.get(
                            codename=perm_codename,
                            content_type=content_type
                        )
                        group.permissions.add(permission)
                        assigned_count += 1
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f'Permission not found: {perm_codename}')
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully assigned {assigned_count} permissions to group: {group_name}'
                    )
                )
            except Group.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Group "{group_name}" does not exist.')
                )
                self.stdout.write('Available groups:')
                for group in Group.objects.all():
                    self.stdout.write(f'  - {group.name}')
        else:
            # Show usage
            self.stdout.write('Usage:')
            self.stdout.write('  python manage.py assign_insurance_permissions --group <group_name> [--all|--view-only]')
            self.stdout.write('')
            self.stdout.write('Options:')
            self.stdout.write('  --group <name>    : Group name to assign permissions to')
            self.stdout.write('  --all             : Assign all permissions (view, add, change, delete)')
            self.stdout.write('  --view-only       : Assign only view permissions')
            self.stdout.write('')
            self.stdout.write('Available groups:')
            for group in Group.objects.all():
                self.stdout.write(f'  - {group.name}')

