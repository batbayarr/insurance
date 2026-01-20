from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from .models import Ref_Account, RefClientType, RefClient, Ref_Currency, RefInventory, Cash_Document, Cash_DocumentDetail, RefAsset, Ref_Asset_Type, Ref_Asset_Card, Inv_Document, Inv_Document_Item, Inv_Document_Detail, Ref_Constant, CashBeginningBalance, Ast_Beginning_Balance, Ref_Asset_Depreciation_Account, Ast_Document, Ast_Document_Detail, Ast_Document_Item, Ref_Template, Ref_Template_Detail, Ref_Product_Group, Ref_Product_Type, Ref_Product, Ref_Item_Type, Ref_Item, Ref_Item_Question, Ref_Risk_Type, Ref_Risk, Ref_Ins_Client, Ref_Policy_Template, Ref_Template_Account, Ref_Template_Product, Ref_Template_Product_Item, Ref_Template_Product_Item_Risk, Ref_Branch, Ref_Channel, Policy_Main, Policy_Main_Coinsurance, Policy_Main_Schedule, Policy_Main_Files, Policy_Main_Product, Policy_Main_Product_Item, Policy_Main_Product_Item_Risk, Policy_Main_Product_Item_Question

@admin.register(Ref_Account)
class Ref_AccountAdmin(admin.ModelAdmin):
    list_display = ('AccountCode', 'AccountName', 'AccountTypeId', 'CurrencyId', 'IsDelete', 'CreatedDate')
    list_filter = ('AccountTypeId', 'CurrencyId', 'IsDelete', 'CreatedDate')
    search_fields = ('AccountCode', 'AccountName')
    ordering = ('AccountCode',)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_account')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_account')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_account')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_account')


@admin.register(RefClient)
class RefClientAdmin(admin.ModelAdmin):
    list_display = ('ClientCode', 'ClientName', 'ClientType', 'ClientRegister', 'IsDelete', 'CreatedDate')
    list_filter = ('ClientType', 'IsDelete', 'CreatedDate')
    search_fields = ('ClientCode', 'ClientName', 'ClientRegister')
    ordering = ('ClientCode',)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_refclient')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_refclient')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_refclient')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_refclient')


@admin.register(RefInventory)
class RefInventoryAdmin(admin.ModelAdmin):
    list_display = ('InventoryName', 'CreatedBy', 'IsActive', 'CreatedDate', 'ModifiedDate')
    list_filter = ('IsActive', 'CreatedDate')
    search_fields = ('InventoryName', 'CreatedBy')
    ordering = ('InventoryName',)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_refinventory')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_refinventory')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_refinventory')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_refinventory')

@admin.register(Cash_Document)
class CashDocumentAdmin(admin.ModelAdmin):
    list_display = ('DocumentNo', 'DocumentDate', 'Description', 'TemplateId', 'IsLock', 'IsDelete', 'CreatedBy', 'CreatedDate')
    list_filter = ('IsLock', 'IsDelete', 'DocumentDate', 'CreatedDate', 'TemplateId')
    search_fields = ('DocumentNo', 'Description', 'CreatedBy')
    ordering = ('-DocumentDate',)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_cash_document')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_cash_document')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_cash_document')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_cash_document')


@admin.register(Cash_DocumentDetail)
class CashDocumentDetailAdmin(admin.ModelAdmin):
    list_display = ('DocumentId', 'AccountId', 'ClientId', 'CurrencyId', 'CurrencyAmount', 'IsDebit', 'DebitAmount', 'CreditAmount')
    list_filter = ('IsDebit', 'CurrencyId', 'DocumentId__DocumentDate')
    search_fields = ('DocumentId__DocumentNo', 'AccountId__AccountName', 'ClientId__ClientName')
    ordering = ('DocumentId', 'AccountId')
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_cash_documentdetail')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_cash_documentdetail')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_cash_documentdetail')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_cash_documentdetail')


@admin.register(Inv_Document)
class InvDocumentAdmin(admin.ModelAdmin):
    list_display = ('DocumentNo', 'DocumentDate', 'Description', 'IsLock', 'IsDelete', 'CreatedBy', 'CreatedDate')
    list_filter = ('IsLock', 'IsDelete', 'DocumentDate', 'CreatedDate')
    search_fields = ('DocumentNo', 'Description', 'CreatedBy__username')
    ordering = ('-DocumentDate', '-DocumentNo')
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_inv_document')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_inv_document')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_inv_document')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_inv_document')


@admin.register(Inv_Document_Item)
class InvDocumentItemAdmin(admin.ModelAdmin):
    list_display = ('DocumentId', 'InventoryId', 'Quantity', 'UnitCost', 'UnitPrice')
    list_filter = ('DocumentId__DocumentDate',)
    search_fields = ('DocumentId__DocumentNo', 'InventoryId__InventoryName')
    ordering = ('DocumentId', 'InventoryId')
    
    def has_view_permission(self, request, obj=None):
        if hasattr(request, 'user'):
            return request.user.has_perm('core.view_inv_document_item')
        elif hasattr(request, 'has_perm'):
            return request.has_perm('core.view_inv_document_item')
        return False
    
    def has_add_permission(self, request):
        if hasattr(request, 'user'):
            return request.user.has_perm('core.add_inv_document_item')
        elif hasattr(request, 'has_perm'):
            return request.has_perm('core.add_inv_document_item')
        return False
    
    def has_change_permission(self, request, obj=None):
        if hasattr(request, 'user'):
            return request.user.has_perm('core.change_inv_document_item')
        elif hasattr(request, 'has_perm'):
            return request.has_perm('core.change_inv_document_item')
        return False
    
    def has_delete_permission(self, request, obj=None):
        if hasattr(request, 'user'):
            return request.user.has_perm('core.delete_inv_document_item')
        elif hasattr(request, 'has_perm'):
            return request.has_perm('core.delete_inv_document_item')
        return False


@admin.register(Inv_Document_Detail)
class InvDocumentDetailAdmin(admin.ModelAdmin):
    list_display = ('DocumentId', 'AccountId', 'ClientId', 'CurrencyId', 'CurrencyAmount', 'IsDebit', 'DebitAmount', 'CreditAmount')
    list_filter = ('IsDebit', 'CurrencyId', 'DocumentId__DocumentDate')
    search_fields = ('DocumentId__DocumentNo', 'AccountId__AccountName', 'ClientId__ClientName')
    ordering = ('DocumentId', 'AccountId')
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_inv_document_detail')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_inv_document_detail')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_inv_document_detail')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_inv_document_detail')


@admin.register(Ref_Constant)
class Ref_ConstantAdmin(admin.ModelAdmin):
    list_display = ('ConstantID', 'ConstantName', 'ConstantDescription')
    list_filter = ('ConstantName',)
    search_fields = ('ConstantName', 'ConstantDescription')
    ordering = ('ConstantID',)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_constant')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_constant')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_constant')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_constant')


@admin.register(CashBeginningBalance)
class CashBeginningBalanceAdmin(admin.ModelAdmin):
    list_display = ('BeginningBalanceID', 'AccountID', 'ClientID', 'CurrencyID', 'CurrencyExchange', 'CurrencyAmount', 'CreatedDate', 'CreatedBy', 'IsDelete')
    list_filter = ('CurrencyID', 'IsDelete', 'CreatedDate', 'CreatedBy')
    search_fields = ('AccountID__AccountName', 'AccountID__AccountCode', 'ClientID__ClientName', 'ClientID__ClientCode')
    ordering = ('-CreatedDate', 'AccountID')
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('AccountID', 'ClientID', 'CurrencyID')
        }),
        ('Amount Details', {
            'fields': ('CurrencyExchange', 'CurrencyAmount')
        }),
        ('Audit Information', {
            'fields': ('CreatedDate', 'CreatedBy', 'ModifiedDate', 'ModifiedBy', 'IsDelete'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        obj.ModifiedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_cashbeginningbalance')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_cashbeginningbalance')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_cashbeginningbalance')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_cashbeginningbalance')


@admin.register(Ast_Beginning_Balance)
class AstBeginningBalanceAdmin(admin.ModelAdmin):
    list_display = ('BeginningBalanceId', 'AccountId', 'AssetCardId', 'Quantity', 'UnitCost', 'UnitPrice', 'CumulatedDepreciation', 'ClientId', 'CreatedDate', 'CreatedBy', 'IsDelete')
    list_filter = ('IsDelete', 'CreatedDate', 'CreatedBy', 'ClientId')
    search_fields = ('AccountId__AccountName', 'AccountId__AccountCode', 'AssetCardId__AssetCardCode', 'AssetCardId__AssetId__AssetName', 'ClientId__ClientName', 'ClientId__ClientCode')
    ordering = ('-CreatedDate', 'AccountId')
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('AccountId', 'AssetCardId', 'ClientId')
        }),
        ('Asset Details', {
            'fields': ('Quantity', 'UnitCost', 'UnitPrice', 'CumulatedDepreciation')
        }),
        ('Audit Information', {
            'fields': ('CreatedDate', 'CreatedBy', 'ModifiedDate', 'ModifiedBy', 'IsDelete'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        obj.ModifiedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ast_beginning_balance')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ast_beginning_balance')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ast_beginning_balance')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ast_beginning_balance')


@admin.register(Ref_Asset_Card)
class RefAssetCardAdmin(admin.ModelAdmin):
    list_display = ('AssetCardId', 'AssetId', 'AssetCardCode', 'AssetCardName', 'ManufacturedDate', 'ReceivedDate', 'MonthsToUse', 'UnitCost', 'UnitPrice', 'DailyExpense', 'CumulatedDepreciation', 'ClientId', 'CreatedDate', 'CreatedBy')
    list_filter = ('AssetId__AssetTypeId', 'CreatedDate', 'CreatedBy', 'ClientId')
    search_fields = ('AssetCardCode', 'AssetCardName', 'AssetId__AssetName', 'AssetId__AssetCode', 'ClientId__ClientName', 'ClientId__ClientCode')
    ordering = ('AssetCardCode',)
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('AssetId', 'AssetCardCode', 'AssetCardName', 'ClientId')
        }),
        ('Asset Details', {
            'fields': ('ManufacturedDate', 'ReceivedDate', 'MonthsToUse', 'UnitCost', 'UnitPrice', 'DailyExpense', 'CumulatedDepreciation')
        }),
        ('Audit Information', {
            'fields': ('CreatedDate', 'CreatedBy', 'ModifiedDate', 'ModifiedBy'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        obj.ModifiedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_asset_card')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_asset_card')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_asset_card')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_asset_card')


@admin.register(Ref_Asset_Depreciation_Account)
class RefAssetDepreciationAccountAdmin(admin.ModelAdmin):
    list_display = ('AstDepId', 'AssetAccountId', 'DepreciationAccountId', 'ExpenseAccountId', 'CreatedDate', 'CreatedBy', 'IsDelete')
    list_filter = ('IsDelete', 'CreatedDate', 'CreatedBy')
    search_fields = ('AstDepId', 'AssetAccountId__AccountName', 'AssetAccountId__AccountCode', 'DepreciationAccountId__AccountName', 'DepreciationAccountId__AccountCode', 'ExpenseAccountId__AccountName', 'ExpenseAccountId__AccountCode')
    ordering = ('AstDepId',)
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    
    fieldsets = (
        ('Account Mapping', {
            'fields': ('AstDepId', 'AssetAccountId', 'DepreciationAccountId', 'ExpenseAccountId')
        }),
        ('Audit Information', {
            'fields': ('CreatedDate', 'CreatedBy', 'ModifiedDate', 'ModifiedBy', 'IsDelete'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        obj.ModifiedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_asset_depreciation_account')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_asset_depreciation_account')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_asset_depreciation_account')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_asset_depreciation_account')


@admin.register(Ast_Document)
class Ast_DocumentAdmin(admin.ModelAdmin):
    list_display = ('DocumentNo', 'DocumentDate', 'DocumentTypeId', 'AccountId', 'ClientId', 'Description', 'IsVat', 'IsLock', 'IsDelete', 'IsPosted', 'CreatedDate')
    list_filter = ('DocumentTypeId', 'IsVat', 'IsLock', 'IsDelete', 'IsPosted', 'CreatedDate', 'DocumentDate')
    search_fields = ('DocumentNo', 'Description', 'AccountId__AccountName', 'ClientId__ClientName')
    ordering = ('-CreatedDate', '-DocumentId')
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    
    fieldsets = (
        ('Document Information', {
            'fields': ('DocumentNo', 'DocumentTypeId', 'DocumentDate', 'Description')
        }),
        ('Account & Client', {
            'fields': ('AccountId', 'ClientId')
        }),
        ('VAT Information', {
            'fields': ('IsVat', 'VatAccountId', 'VatPercent'),
            'classes': ('collapse',)
        }),
        ('Amounts', {
            'fields': ('CostAmount', 'PriceAmount'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('IsLock', 'IsDelete', 'IsPosted')
        }),
        ('Audit Information', {
            'fields': ('CreatedBy', 'CreatedDate', 'ModifiedBy', 'ModifiedDate'),
            'classes': ('collapse',)
        }),
    )
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ast_document')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ast_document')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ast_document')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ast_document')


@admin.register(Ast_Document_Detail)
class Ast_Document_DetailAdmin(admin.ModelAdmin):
    list_display = ('DocumentDetailId', 'DocumentId', 'AccountId', 'ClientId', 'CurrencyId', 'CurrencyAmount', 'IsDebit', 'DebitAmount', 'CreditAmount')
    list_filter = ('IsDebit', 'CurrencyId', 'AccountId', 'DocumentId__DocumentTypeId')
    search_fields = ('DocumentId__DocumentNo', 'AccountId__AccountName', 'ClientId__ClientName')
    ordering = ('-DocumentDetailId',)
    
    fieldsets = (
        ('Document Information', {
            'fields': ('DocumentId',)
        }),
        ('Account & Client', {
            'fields': ('AccountId', 'ClientId')
        }),
        ('Currency Information', {
            'fields': ('CurrencyId', 'CurrencyExchange', 'CurrencyAmount')
        }),
        ('Amounts', {
            'fields': ('IsDebit', 'DebitAmount', 'CreditAmount')
        }),
    )
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ast_document_detail')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ast_document_detail')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ast_document_detail')


@admin.register(Ast_Document_Item)
class Ast_Document_ItemAdmin(admin.ModelAdmin):
    list_display = ('DocumentItemId', 'DocumentId', 'AssetCardId', 'Quantity', 'UnitCost', 'UnitPrice')
    list_filter = ('DocumentId__DocumentTypeId', 'AssetCardId__AssetId')
    search_fields = ('DocumentId__DocumentNo', 'AssetCardId__assetCardName', 'AssetCardId__assetCardCode')
    ordering = ('-DocumentItemId',)
    
    fieldsets = (
        ('Document Information', {
            'fields': ('DocumentId',)
        }),
        ('Asset Information', {
            'fields': ('AssetCardId',)
        }),
        ('Quantities & Prices', {
            'fields': ('Quantity', 'UnitCost', 'UnitPrice')
        }),
    )
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ast_document_item')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ast_document_item')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ast_document_item')


@admin.register(Ref_Template)
class Ref_TemplateAdmin(admin.ModelAdmin):
    list_display = ('TemplateId', 'TemplateName', 'DocumentTypeId', 'AccountId', 'IsDelete', 'CreatedBy', 'CreatedDate')
    list_filter = ('DocumentTypeId', 'AccountId', 'IsDelete', 'CreatedDate')
    search_fields = ('TemplateName', 'DocumentTypeId__Description', 'AccountId__AccountName')
    ordering = ('TemplateName',)
    readonly_fields = ('TemplateId', 'CreatedDate')
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_template')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_template')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_template')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_template')


@admin.register(Ref_Template_Detail)
class Ref_Template_DetailAdmin(admin.ModelAdmin):
    list_display = ('TemplateDetailId', 'TemplateId', 'AccountId', 'IsDebit')
    list_filter = ('TemplateId', 'IsDebit', 'AccountId__AccountTypeId')
    search_fields = ('TemplateId__TemplateName', 'AccountId__AccountCode', 'AccountId__AccountName')
    ordering = ('TemplateId', 'AccountId')
    readonly_fields = ('TemplateDetailId',)
    
    # Use template permissions for template details
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_template')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_template')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_template')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_template')


@admin.register(Ref_Product_Group)
class Ref_Product_GroupAdmin(admin.ModelAdmin):
    list_display = ('ProductGroupId', 'ProductGroupCode', 'ProductGroupName', 'IsActive')
    list_filter = ('IsActive',)
    search_fields = ('ProductGroupCode', 'ProductGroupName')
    ordering = ('ProductGroupCode',)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_product_group')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_product_group')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_product_group')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_product_group')


@admin.register(Ref_Product_Type)
class Ref_Product_TypeAdmin(admin.ModelAdmin):
    list_display = ('ProductTypeId', 'ProductTypeCode', 'ProductTypeName', 'ProductGroupId', 'IsActive', 'CreatedDate', 'CreatedBy')
    list_filter = ('IsActive', 'ProductGroupId', 'CreatedDate')
    search_fields = ('ProductTypeCode', 'ProductTypeName', 'ProductGroupId__ProductGroupName')
    ordering = ('ProductTypeCode',)
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('ProductTypeCode', 'ProductTypeName', 'ProductGroupId', 'IsActive')
        }),
        ('Audit Information', {
            'fields': ('CreatedBy', 'CreatedDate', 'ModifiedBy', 'ModifiedDate'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        obj.ModifiedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_product_type')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_product_type')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_product_type')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_product_type')


@admin.register(Ref_Product)
class Ref_ProductAdmin(admin.ModelAdmin):
    list_display = ('ProductId', 'ProductCode', 'ProductName', 'ProductTypeId', 'IsActive', 'CreatedDate', 'CreatedBy')
    list_filter = ('IsActive', 'ProductTypeId', 'CreatedDate')
    search_fields = ('ProductCode', 'ProductName', 'ProductTypeId__ProductTypeName')
    ordering = ('ProductCode',)
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('ProductCode', 'ProductName', 'ProductTypeId', 'IsActive')
        }),
        ('Audit Information', {
            'fields': ('CreatedBy', 'CreatedDate', 'ModifiedBy', 'ModifiedDate'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        obj.ModifiedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_product')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_product')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_product')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_product')


@admin.register(Ref_Item_Type)
class Ref_Item_TypeAdmin(admin.ModelAdmin):
    list_display = ('ItemTypeId', 'ItemTypeCode', 'ItemTypeName', 'ParentId', 'IsActive', 'CreatedDate', 'CreatedBy')
    list_filter = ('IsActive', 'ParentId', 'CreatedDate')
    search_fields = ('ItemTypeCode', 'ItemTypeName', 'ParentId__ItemTypeName')
    ordering = ('ItemTypeCode',)
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('ItemTypeCode', 'ItemTypeName', 'ParentId', 'IsActive')
        }),
        ('Audit Information', {
            'fields': ('CreatedBy', 'CreatedDate', 'ModifiedBy', 'ModifiedDate'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        obj.ModifiedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_item_type')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_item_type')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_item_type')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_item_type')


@admin.register(Ref_Item)
class Ref_ItemAdmin(admin.ModelAdmin):
    list_display = ('ItemId', 'ItemCode', 'ItemName', 'ItemTypeId', 'IsActive', 'CreatedDate', 'CreatedBy')
    list_filter = ('IsActive', 'ItemTypeId', 'CreatedDate')
    search_fields = ('ItemCode', 'ItemName', 'ItemTypeId__ItemTypeName')
    ordering = ('ItemCode',)
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('ItemCode', 'ItemName', 'ItemTypeId', 'IsActive')
        }),
        ('Audit Information', {
            'fields': ('CreatedBy', 'CreatedDate', 'ModifiedBy', 'ModifiedDate'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        obj.ModifiedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_item')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_item')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_item')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_item')


@admin.register(Ref_Item_Question)
class Ref_Item_QuestionAdmin(admin.ModelAdmin):
    list_display = ('ItemQuestionId', 'ItemQuestionCode', 'ItemQuestionName', 'ItemId', 'QuestionType', 'FieldType', 'Order', 'IsActive', 'CreatedDate', 'CreatedBy')
    list_filter = ('IsActive', 'QuestionType', 'FieldType', 'ItemId', 'CreatedDate')
    search_fields = ('ItemQuestionCode', 'ItemQuestionName', 'ItemId__ItemName', 'ItemId__ItemCode')
    ordering = ('Order', 'ItemQuestionCode')
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('ItemQuestionCode', 'ItemQuestionName', 'ItemId', 'IsActive')
        }),
        ('Question Configuration', {
            'fields': ('QuestionType', 'FieldType', 'FieldValue', 'FieldMask', 'Order')
        }),
        ('Audit Information', {
            'fields': ('CreatedBy', 'CreatedDate', 'ModifiedBy', 'ModifiedDate'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        obj.ModifiedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_item_question')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_item_question')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_item_question')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_item_question')


@admin.register(Ref_Risk_Type)
class Ref_Risk_TypeAdmin(admin.ModelAdmin):
    list_display = ('RiskTypeId', 'RiskTypeCode', 'RiskTypeName', 'IsActive', 'CreatedDate', 'CreatedBy')
    list_filter = ('IsActive', 'CreatedDate')
    search_fields = ('RiskTypeCode', 'RiskTypeName')
    ordering = ('RiskTypeCode',)
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('RiskTypeCode', 'RiskTypeName', 'IsActive')
        }),
        ('Audit Information', {
            'fields': ('CreatedBy', 'CreatedDate', 'ModifiedBy', 'ModifiedDate'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        obj.ModifiedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_risk_type')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_risk_type')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_risk_type')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_risk_type')


@admin.register(Ref_Risk)
class Ref_RiskAdmin(admin.ModelAdmin):
    list_display = ('RiskId', 'RiskCode', 'RiskName', 'CategoryName', 'RiskTypeId', 'IsCoreRisk', 'IsActive', 'CreatedDate', 'CreatedBy')
    list_filter = ('IsActive', 'IsCoreRisk', 'RiskTypeId', 'CategoryName', 'CreatedDate')
    search_fields = ('RiskCode', 'RiskName', 'CategoryName', 'RiskTypeId__RiskTypeName', 'Description')
    ordering = ('RiskCode',)
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('RiskCode', 'RiskName', 'CategoryName', 'RiskTypeId', 'IsCoreRisk', 'IsActive')
        }),
        ('Description', {
            'fields': ('Description',)
        }),
        ('Audit Information', {
            'fields': ('CreatedBy', 'CreatedDate', 'ModifiedBy', 'ModifiedDate'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        obj.ModifiedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_risk')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_risk')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_risk')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_risk')


@admin.register(Ref_Ins_Client)
class Ref_Ins_ClientAdmin(admin.ModelAdmin):
    list_display = ('InsClientId', 'InsClientCode', 'ClientId', 'OrgName', 'FirstName', 'LastName', 'IsOrg', 'IsActive', 'CreatedDate', 'CreatedBy')
    list_filter = ('IsActive', 'IsOrg', 'IsPolitics', 'IsInvestor', 'CreatedDate')
    search_fields = ('InsClientCode', 'OrgName', 'FirstName', 'LastName', 'Email', 'Phone1', 'Phone2', 'ClientId__ClientName', 'ClientId__ClientCode')
    ordering = ('InsClientCode',)
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('InsClientCode', 'ClientId', 'IsActive')
        }),
        ('Organization Information', {
            'fields': ('IsOrg', 'OrgName', 'OrgRegister', 'IsPolitics', 'IsInvestor'),
            'classes': ('collapse',)
        }),
        ('Personal Information', {
            'fields': ('FirstName', 'LastName', 'Gender', 'NationalityId', 'PhotoPath'),
            'classes': ('collapse',)
        }),
        ('Contact Information', {
            'fields': ('Phone1', 'Phone2', 'Email', 'EmergencyContact'),
            'classes': ('collapse',)
        }),
        ('Driver Information', {
            'fields': ('DriverLicenceNo', 'DriverLicentceYear'),
            'classes': ('collapse',)
        }),
        ('Location', {
            'fields': ('DistrictId',),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('CreatedBy', 'CreatedDate', 'ModifiedBy', 'ModifiedDate'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        obj.ModifiedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_ins_client')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_ins_client')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_ins_client')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_ins_client')


@admin.register(Ref_Policy_Template)
class Ref_Policy_TemplateAdmin(admin.ModelAdmin):
    list_display = ('PolicyTemplateId', 'PolicyTemplateName', 'Description', 'FilePath', 'IsActive', 'IsDelete', 'CreatedDate', 'CreatedBy')
    list_filter = ('IsActive', 'IsDelete', 'CreatedDate')
    search_fields = ('PolicyTemplateName', 'Description', 'FilePath')
    ordering = ('PolicyTemplateName',)
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('PolicyTemplateName', 'Description', 'FilePath', 'IsActive', 'IsDelete')
        }),
        ('Audit Information', {
            'fields': ('CreatedBy', 'CreatedDate', 'ModifiedBy', 'ModifiedDate'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        obj.ModifiedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_policy_template')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_policy_template')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_policy_template')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_policy_template')


@admin.register(Ref_Template_Account)
class Ref_Template_AccountAdmin(admin.ModelAdmin):
    list_display = ('TemplateAccountId', 'PolicyTemplateId', 'AccountId', 'IsDebit', 'CashFlowId', 'CalculationType')
    list_filter = ('IsDebit', 'CalculationType', 'PolicyTemplateId', 'AccountId__AccountTypeId', 'CashFlowId')
    search_fields = ('PolicyTemplateId__PolicyTemplateName', 'AccountId__AccountCode', 'AccountId__AccountName', 'CashFlowId__Description')
    ordering = ('PolicyTemplateId', 'AccountId')
    
    fieldsets = (
        ('Template Information', {
            'fields': ('PolicyTemplateId',)
        }),
        ('Account Information', {
            'fields': ('AccountId', 'IsDebit', 'CalculationType')
        }),
        ('Cash Flow', {
            'fields': ('CashFlowId',),
            'classes': ('collapse',)
        }),
    )
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_policy_template_transaction')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_policy_template_transaction')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_policy_template_transaction')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_policy_template_transaction')


@admin.register(Ref_Template_Product)
class Ref_Template_ProductAdmin(admin.ModelAdmin):
    list_display = ('TemplateProductId', 'TemplateId', 'ProductId')
    list_filter = ('TemplateId', 'ProductId')
    search_fields = ('TemplateId__PolicyTemplateName', 'ProductId__ProductName', 'ProductId__ProductCode')
    ordering = ('TemplateId', 'ProductId')
    
    fieldsets = (
        ('Template Information', {
            'fields': ('TemplateId',)
        }),
        ('Product Information', {
            'fields': ('ProductId',)
        }),
    )
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_template_product')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_template_product')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_template_product')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_template_product')


@admin.register(Ref_Template_Product_Item)
class Ref_Template_Product_ItemAdmin(admin.ModelAdmin):
    list_display = ('TemplateProductItemId', 'TemplateProductId', 'ItemId')
    list_filter = ('TemplateProductId', 'ItemId')
    search_fields = ('TemplateProductId__TemplateId__PolicyTemplateName', 'TemplateProductId__ProductId__ProductName', 'ItemId__ItemName', 'ItemId__ItemCode')
    ordering = ('TemplateProductId', 'ItemId')
    
    fieldsets = (
        ('Template Product Information', {
            'fields': ('TemplateProductId',)
        }),
        ('Item Information', {
            'fields': ('ItemId',)
        }),
    )
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_template_product_item')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_template_product_item')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_template_product_item')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_template_product_item')


@admin.register(Ref_Template_Product_Item_Risk)
class Ref_Template_Product_Item_RiskAdmin(admin.ModelAdmin):
    list_display = ('TemplateProductItemRiskId', 'TemplateProductItemId', 'RiskId', 'CommPercent')
    list_filter = ('TemplateProductItemId', 'RiskId')
    search_fields = ('TemplateProductItemId__TemplateProductId__TemplateId__PolicyTemplateName', 'TemplateProductItemId__TemplateProductId__ProductId__ProductName', 'TemplateProductItemId__ItemId__ItemName', 'RiskId__RiskName', 'RiskId__RiskCode')
    ordering = ('TemplateProductItemId', 'RiskId')
    
    fieldsets = (
        ('Template Product Item Information', {
            'fields': ('TemplateProductItemId',)
        }),
        ('Risk Information', {
            'fields': ('RiskId',)
        }),
        ('Commission', {
            'fields': ('CommPercent',)
        }),
    )
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_template_product_item_risk')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_template_product_item_risk')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_template_product_item_risk')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_template_product_item_risk')


@admin.register(Ref_Branch)
class Ref_BranchAdmin(admin.ModelAdmin):
    list_display = ('BranchId', 'BranchCode', 'BranchName', 'DirectorName', 'IsActive', 'CreatedDate', 'CreatedBy')
    list_filter = ('IsActive', 'CreatedDate')
    search_fields = ('BranchCode', 'BranchName', 'DirectorName')
    ordering = ('BranchCode',)
    readonly_fields = ('CreatedDate',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('BranchCode', 'BranchName', 'DirectorName', 'IsActive')
        }),
        ('Audit Information', {
            'fields': ('CreatedBy', 'CreatedDate'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_branch')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_branch')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_branch')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_branch')


@admin.register(Ref_Channel)
class Ref_ChannelAdmin(admin.ModelAdmin):
    list_display = ('ChannelId', 'ChannelName', 'IsActive', 'CreatedDate', 'CreatedBy')
    list_filter = ('IsActive', 'CreatedDate')
    search_fields = ('ChannelName',)
    ordering = ('ChannelName',)
    readonly_fields = ('CreatedDate',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('ChannelName', 'IsActive')
        }),
        ('Audit Information', {
            'fields': ('CreatedBy', 'CreatedDate'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_ref_channel')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_ref_channel')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_ref_channel')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_ref_channel')


# Inline admins for Policy_Main related models
class Policy_Main_CoinsuranceInline(admin.TabularInline):
    model = Policy_Main_Coinsurance
    extra = 0
    fields = ('ClientId', 'Description')
    verbose_name = 'Coinsurance'
    verbose_name_plural = 'Coinsurance'


class Policy_Main_ScheduleInline(admin.TabularInline):
    model = Policy_Main_Schedule
    extra = 0
    fields = ('DueDate', 'Amount')
    verbose_name = 'Payment Schedule'
    verbose_name_plural = 'Payment Schedules'


class Policy_Main_FilesInline(admin.TabularInline):
    model = Policy_Main_Files
    extra = 0
    fields = ('FileName', 'FilePath')
    verbose_name = 'File'
    verbose_name_plural = 'Files'


@admin.register(Policy_Main)
class Policy_MainAdmin(admin.ModelAdmin):
    list_display = ('PolicyId', 'PolicyNo', 'ClientId', 'AgentId', 'BeginDate', 'EndDate', 'IsActive', 'IsLock', 'IsPosted', 'CreatedDate', 'CreatedBy')
    list_filter = ('IsActive', 'IsLock', 'IsPosted', 'StatusId', 'CreatedDate')
    search_fields = ('PolicyNo', 'ClientId__ClientName', 'AgentId__username', 'Description')
    ordering = ('-CreatedDate',)
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    date_hierarchy = 'CreatedDate'
    inlines = [Policy_Main_CoinsuranceInline, Policy_Main_ScheduleInline, Policy_Main_FilesInline]
    verbose_name = 'Insurance Policy'
    verbose_name_plural = 'Insurance Policies'
    
    fieldsets = (
        ('Policy Information', {
            'fields': ('PolicyNo', 'PolicyTemplateId', 'ClientId', 'AgentId', 'BeginDate', 'EndDate', 'Description')
        }),
        ('Financial Information', {
            'fields': ('CurrencyId', 'CurrencyExchange')
        }),
        ('Agent Information', {
            'fields': ('AgentBranchId', 'AgentChannelId', 'DirectorName')
        }),
        ('Status & Control', {
            'fields': ('IsActive', 'IsLock', 'IsPosted', 'StatusId', 'ApprovedBy')
        }),
        ('Audit Information', {
            'fields': ('CreatedBy', 'CreatedDate', 'ModifiedBy', 'ModifiedDate'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.CreatedBy = request.user
        obj.ModifiedBy = request.user
        super().save_model(request, obj, form, change)
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_policy_main')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_policy_main')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_policy_main')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_policy_main')


@admin.register(Policy_Main_Coinsurance)
class Policy_Main_CoinsuranceAdmin(admin.ModelAdmin):
    list_display = ('PolicyCoInsuredId', 'PolicyId', 'ClientId', 'Description')
    list_filter = ('PolicyId',)
    search_fields = ('PolicyId__PolicyNo', 'ClientId__ClientName', 'Description')
    ordering = ('PolicyId', 'ClientId')
    verbose_name = 'Insurance Policy Coinsurance'
    verbose_name_plural = 'Insurance Policy Coinsurance'
    
    fieldsets = (
        ('Coinsurance Information', {
            'fields': ('PolicyId', 'ClientId', 'Description')
        }),
    )
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_policy_main_coinsurance')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_policy_main_coinsurance')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_policy_main_coinsurance')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_policy_main_coinsurance')


@admin.register(Policy_Main_Schedule)
class Policy_Main_ScheduleAdmin(admin.ModelAdmin):
    list_display = ('PolicyPaymentScheduleId', 'PolicyId', 'DueDate', 'Amount')
    list_filter = ('DueDate', 'PolicyId')
    search_fields = ('PolicyId__PolicyNo',)
    ordering = ('PolicyId', 'DueDate')
    date_hierarchy = 'DueDate'
    verbose_name = 'Insurance Policy Payment Schedule'
    verbose_name_plural = 'Insurance Policy Payment Schedules'
    
    fieldsets = (
        ('Payment Schedule Information', {
            'fields': ('PolicyId', 'DueDate', 'Amount')
        }),
    )
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_policy_main_schedule')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_policy_main_schedule')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_policy_main_schedule')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_policy_main_schedule')


@admin.register(Policy_Main_Files)
class Policy_Main_FilesAdmin(admin.ModelAdmin):
    list_display = ('PolicyAttachmentId', 'PolicyId', 'FileName', 'FilePath')
    list_filter = ('PolicyId',)
    search_fields = ('PolicyId__PolicyNo', 'FileName', 'FilePath')
    ordering = ('PolicyId', 'FileName')
    verbose_name = 'Insurance Policy File'
    verbose_name_plural = 'Insurance Policy Files'
    
    fieldsets = (
        ('File Information', {
            'fields': ('PolicyId', 'FileName', 'FilePath')
        }),
    )
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_policy_main_files')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_policy_main_files')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_policy_main_files')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_policy_main_files')


@admin.register(Policy_Main_Product)
class Policy_Main_ProductAdmin(admin.ModelAdmin):
    list_display = ('PolicyMainProductId', 'PolicyMainId', 'ProductId')
    list_filter = ('PolicyMainId', 'ProductId')
    search_fields = ('PolicyMainId__PolicyNo', 'ProductId__ProductName', 'ProductId__ProductCode')
    ordering = ('PolicyMainId', 'ProductId')
    verbose_name = 'Insurance Policy Product'
    verbose_name_plural = 'Insurance Policy Products'
    
    fieldsets = (
        ('Policy Product Information', {
            'fields': ('PolicyMainId', 'ProductId')
        }),
    )
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_policy_main_product')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_policy_main_product')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_policy_main_product')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_policy_main_product')


@admin.register(Policy_Main_Product_Item)
class Policy_Main_Product_ItemAdmin(admin.ModelAdmin):
    list_display = ('PolicyMainProductItemId', 'PolicyMainProductId', 'ItemId', 'BeginDate', 'EndDate', 'Valuation', 'CommPercent', 'CommAmount')
    list_filter = ('PolicyMainProductId', 'ItemId', 'BeginDate', 'EndDate')
    search_fields = ('PolicyMainProductId__PolicyMainId__PolicyNo', 'ItemId__ItemName', 'ItemId__ItemCode')
    ordering = ('PolicyMainProductId', 'ItemId')
    verbose_name = 'Insurance Policy Product Item'
    verbose_name_plural = 'Insurance Policy Product Items'
    
    fieldsets = (
        ('Policy Product Item Information', {
            'fields': ('PolicyMainProductId', 'ItemId', 'BeginDate', 'EndDate', 'Valuation', 'CommPercent', 'CommAmount')
        }),
    )
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_policy_main_product_item')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_policy_main_product_item')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_policy_main_product_item')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_policy_main_product_item')


@admin.register(Policy_Main_Product_Item_Risk)
class Policy_Main_Product_Item_RiskAdmin(admin.ModelAdmin):
    list_display = ('PolicyMainProductItemRiskId', 'PolicyMainProductItemId', 'RiskId', 'RiskPercent')
    list_filter = ('PolicyMainProductItemId', 'RiskId')
    search_fields = ('PolicyMainProductItemId__PolicyMainProductId__PolicyMainId__PolicyNo', 'RiskId__RiskName', 'RiskId__RiskCode')
    ordering = ('PolicyMainProductItemId', 'RiskId')
    verbose_name = 'Insurance Policy Product Item Risk'
    verbose_name_plural = 'Insurance Policy Product Item Risks'
    
    fieldsets = (
        ('Policy Product Item Risk Information', {
            'fields': ('PolicyMainProductItemId', 'RiskId', 'RiskPercent')
        }),
    )
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_policy_main_product_item_risk')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_policy_main_product_item_risk')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_policy_main_product_item_risk')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_policy_main_product_item_risk')


@admin.register(Policy_Main_Product_Item_Question)
class Policy_Main_Product_Item_QuestionAdmin(admin.ModelAdmin):
    list_display = ('PolicyMainProductItemQuestionId', 'PolicyMainProductItemId', 'ItemQuestionId', 'Answer')
    list_filter = ('PolicyMainProductItemId', 'ItemQuestionId')
    search_fields = ('PolicyMainProductItemId__PolicyMainProductId__PolicyMainId__PolicyNo', 'ItemQuestionId__ItemQuestionName', 'Answer')
    ordering = ('PolicyMainProductItemId', 'ItemQuestionId')
    verbose_name = 'Insurance Policy Product Item Question'
    verbose_name_plural = 'Insurance Policy Product Item Questions'
    
    fieldsets = (
        ('Policy Product Item Question Information', {
            'fields': ('PolicyMainProductItemId', 'ItemQuestionId', 'Answer')
        }),
    )
    
    def has_view_permission(self, request, obj=None):
        return request.user.has_perm('core.view_policy_main_product_item_question')
    
    def has_add_permission(self, request):
        return request.user.has_perm('core.add_policy_main_product_item_question')
    
    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('core.change_policy_main_product_item_question')
    
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_policy_main_product_item_question')


# Make Permissions visible in admin
@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('codename', 'name', 'content_type', 'get_model_name')
    list_filter = ('content_type__app_label', 'content_type__model')
    search_fields = ('codename', 'name', 'content_type__model')
    ordering = ('content_type__app_label', 'content_type__model', 'codename')
    
    def get_model_name(self, obj):
        return obj.content_type.model
    get_model_name.short_description = 'Model'
    get_model_name.admin_order_field = 'content_type__model'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('content_type')


# Register ContentType model
@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ('app_label', 'model', 'id')
    list_filter = ('app_label',)
    search_fields = ('app_label', 'model')
    ordering = ('app_label', 'model')

