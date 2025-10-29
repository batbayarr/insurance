from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Ref_Account, RefClientType, RefClient, Ref_Currency, RefInventory, RefAsset, Ref_Asset_Type, CashBeginningBalance, Inv_Document, Inv_Document_Item, Inv_Document_Detail, Ast_Beginning_Balance, Ref_Asset_Card, Ref_Asset_Depreciation_Account, Cash_Document, Cash_DocumentDetail, Ref_Constant


class Command(BaseCommand):
    help = 'Set up default permissions and groups for the accounting application'

    def handle(self, *args, **options):
        self.stdout.write('Setting up permissions and groups...')
        
        # Get content types
        account_ct = ContentType.objects.get_for_model(Ref_Account)
        refclienttype_ct = ContentType.objects.get_for_model(RefClientType)
        refclient_ct = ContentType.objects.get_for_model(RefClient)
        ref_currency_ct = ContentType.objects.get_for_model(Ref_Currency)
        inventory_ct = ContentType.objects.get_for_model(RefInventory)
        asset_ct = ContentType.objects.get_for_model(RefAsset)
        ref_asset_type_ct = ContentType.objects.get_for_model(Ref_Asset_Type)
        cash_beginning_balance_ct = ContentType.objects.get_for_model(CashBeginningBalance)
        inv_document_ct = ContentType.objects.get_for_model(Inv_Document)
        inv_document_item_ct = ContentType.objects.get_for_model(Inv_Document_Item)
        inv_document_detail_ct = ContentType.objects.get_for_model(Inv_Document_Detail)
        ast_beginning_balance_ct = ContentType.objects.get_for_model(Ast_Beginning_Balance)
        ref_asset_card_ct = ContentType.objects.get_for_model(Ref_Asset_Card)
        ref_asset_depreciation_account_ct = ContentType.objects.get_for_model(Ref_Asset_Depreciation_Account)
        cash_document_ct = ContentType.objects.get_for_model(Cash_Document)
        cash_document_detail_ct = ContentType.objects.get_for_model(Cash_DocumentDetail)
        ref_constant_ct = ContentType.objects.get_for_model(Ref_Constant)
        
        # Create permissions if they don't exist
        permissions = [
            # Account permissions
            ('view_refaccount', 'Can view account', account_ct),
            ('add_refaccount', 'Can add account', account_ct),
            ('change_refaccount', 'Can change account', account_ct),
            ('delete_refaccount', 'Can delete account', account_ct),
            
            # Inventory permissions
            ('view_refinventory', 'Can view inventory', inventory_ct),
            ('add_refinventory', 'Can add inventory', inventory_ct),
            ('change_refinventory', 'Can change inventory', inventory_ct),
            ('delete_refinventory', 'Can delete inventory', inventory_ct),
            
            # Inventory Document permissions
            ('view_invdocument', 'Can view inventory document', inv_document_ct),
            ('add_invdocument', 'Can add inventory document', inv_document_ct),
            ('change_invdocument', 'Can change inventory document', inv_document_ct),
            ('delete_invdocument', 'Can delete inventory document', inv_document_ct),
            
            # Asset permissions
            ('view_refasset', 'Can view asset', asset_ct),
            ('add_refasset', 'Can add asset', asset_ct),
            ('change_refasset', 'Can change asset', asset_ct),
            ('delete_refasset', 'Can delete asset', asset_ct),
            
            # Cash Beginning Balance permissions
            ('view_cashbeginningbalance', 'Can view cash beginning balance', cash_beginning_balance_ct),
            ('add_cashbeginningbalance', 'Can add cash beginning balance', cash_beginning_balance_ct),
            ('change_cashbeginningbalance', 'Can change cash beginning balance', cash_beginning_balance_ct),
            ('delete_cashbeginningbalance', 'Can delete cash beginning balance', cash_beginning_balance_ct),
            
            # Asset Beginning Balance permissions
            ('view_ast_beginning_balance', 'Can view asset beginning balance', ast_beginning_balance_ct),
            ('add_ast_beginning_balance', 'Can add asset beginning balance', ast_beginning_balance_ct),
            ('change_ast_beginning_balance', 'Can change asset beginning balance', ast_beginning_balance_ct),
            ('delete_ast_beginning_balance', 'Can delete asset beginning balance', ast_beginning_balance_ct),
            
            # Asset Card permissions
            ('view_ref_asset_card', 'Can view asset card', ref_asset_card_ct),
            ('add_ref_asset_card', 'Can add asset card', ref_asset_card_ct),
            ('change_ref_asset_card', 'Can change asset card', ref_asset_card_ct),
            ('delete_ref_asset_card', 'Can delete asset card', ref_asset_card_ct),
            
            # Asset Depreciation Account permissions
            ('view_ref_asset_depreciation_account', 'Can view asset depreciation account', ref_asset_depreciation_account_ct),
            ('add_ref_asset_depreciation_account', 'Can add asset depreciation account', ref_asset_depreciation_account_ct),
            ('change_ref_asset_depreciation_account', 'Can change asset depreciation account', ref_asset_depreciation_account_ct),
            ('delete_ref_asset_depreciation_account', 'Can delete asset depreciation account', ref_asset_depreciation_account_ct),
        ]
        
        for codename, name, content_type in permissions:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            if created:
                self.stdout.write(f'Created permission: {name}')
        
        # Create groups - baraa_nyarav and mungu_nyabo groups
        groups_data = [
            {
                'name': 'baraa_nyarav',
                'description': 'Can manage inventory items and documents',
                'permissions': [
                    'view_refinventory', 'add_refinventory', 'change_refinventory', 'delete_refinventory',
                    'view_invdocument', 'add_invdocument', 'change_invdocument', 'delete_invdocument',
                    'view_refaccount', 'add_refaccount', 'change_refaccount', 'delete_refaccount',
                    'view_cash_document', 'add_cashdocument', 'change_cash_document', 'delete_cash_document',
                    'view_cash_documentdetail', 'add_cashdocumentdetail', 'change_cash_documentdetail', 'delete_cash_documentdetail',
                    'view_cashbeginningbalance', 'add_cashbeginningbalance', 'change_cashbeginningbalance', 'delete_cashbeginningbalance',
                    'view_refasset', 'add_refasset', 'change_refasset', 'delete_refasset',
                    'view_ast_beginning_balance', 'add_ast_beginning_balance', 'change_ast_beginning_balance', 'delete_ast_beginning_balance',
                    'view_ref_asset_card', 'add_ref_asset_card', 'change_ref_asset_card', 'delete_ref_asset_card',
                    'view_ref_asset_depreciation_account', 'add_ref_asset_depreciation_account', 'change_ref_asset_depreciation_account', 'delete_ref_asset_depreciation_account',
                    'view_refclienttype', 'add_refclienttype', 'change_refclienttype', 'delete_refclienttype',
                    'view_refclient', 'add_refclient', 'change_refclient', 'delete_refclient',
                    'view_ref_currency', 'add_ref_currency', 'change_ref_currency', 'delete_ref_currency',
                    'view_ref_asset_type', 'add_ref_asset_type', 'change_ref_asset_type', 'delete_ref_asset_type',
                    'view_inv_document_item', 'add_inv_document_item', 'change_inv_document_item', 'delete_inv_document_item',
                    'view_inv_document_detail', 'add_inv_document_detail', 'change_inv_document_detail', 'delete_inv_document_detail',
                    'view_ref_constant', 'add_ref_constant', 'change_ref_constant', 'delete_ref_constant'
                ]
            },
            {
                'name': 'mungu_nyabo',
                'description': 'Can manage cash documents, accounts, and clients',
                'permissions': [
                    'view_cash_document', 'add_cash_document', 'change_cash_document', 'delete_cash_document',
                    'view_cash_documentdetail', 'add_cash_documentdetail', 'change_cash_documentdetail', 'delete_cash_documentdetail',
                    'view_refaccount', 'add_refaccount', 'change_refaccount', 'delete_refaccount',
                    'view_refclient', 'add_refclient', 'change_refclient', 'delete_refclient',
                ]
            }
        ]
        
        for group_data in groups_data:
            group, created = Group.objects.get_or_create(
                name=group_data['name']
            )
            if created:
                self.stdout.write(f'Created group: {group.name}')
            
            # Add permissions to group
            for perm_codename in group_data['permissions']:
                if 'refclienttype' in perm_codename:
                    content_type = refclienttype_ct
                elif 'refclient' in perm_codename and 'refclienttype' not in perm_codename:
                    content_type = refclient_ct
                elif 'ref_currency' in perm_codename:
                    content_type = ref_currency_ct
                elif 'refinventory' in perm_codename:
                    content_type = inventory_ct
                elif 'invdocument' in perm_codename and 'inv_document_item' not in perm_codename and 'inv_document_detail' not in perm_codename:
                    content_type = inv_document_ct
                elif 'inv_document_item' in perm_codename:
                    content_type = inv_document_item_ct
                elif 'inv_document_detail' in perm_codename:
                    content_type = inv_document_detail_ct
                elif 'refasset' in perm_codename and 'ref_asset_card' not in perm_codename and 'ref_asset_depreciation_account' not in perm_codename and 'ref_asset_type' not in perm_codename:
                    content_type = asset_ct
                elif 'ref_asset_type' in perm_codename:
                    content_type = ref_asset_type_ct
                elif 'ast_beginning_balance' in perm_codename:
                    content_type = ast_beginning_balance_ct
                elif 'ref_asset_card' in perm_codename:
                    content_type = ref_asset_card_ct
                elif 'ref_asset_depreciation_account' in perm_codename:
                    content_type = ref_asset_depreciation_account_ct
                elif 'cashbeginningbalance' in perm_codename:
                    content_type = cash_beginning_balance_ct
                elif 'cash_document' in perm_codename and 'cash_documentdetail' not in perm_codename:
                    content_type = cash_document_ct
                elif 'cash_documentdetail' in perm_codename:
                    content_type = cash_document_detail_ct
                elif 'cashdocument' in perm_codename and 'cashdocumentdetail' not in perm_codename:
                    content_type = cash_document_ct
                elif 'cashdocumentdetail' in perm_codename:
                    content_type = cash_document_detail_ct
                elif 'ref_constant' in perm_codename:
                    content_type = ref_constant_ct
                else:
                    content_type = account_ct
                
                try:
                    permission = Permission.objects.get(
                        codename=perm_codename,
                        content_type=content_type
                    )
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(f'Warning: Permission {perm_codename} not found')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up permissions and groups!')
        )
        self.stdout.write('\nAvailable groups:')
        for group in Group.objects.all():
            self.stdout.write(f'  - {group.name}: {group.permissions.count()} permissions') 