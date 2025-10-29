from django.contrib import admin
from .models import Ref_Account, RefClientType, RefClient, Ref_Currency, RefInventory, Cash_Document, Cash_DocumentDetail, RefAsset, Ref_Asset_Type, Ref_Asset_Card, Inv_Document, Inv_Document_Item, Inv_Document_Detail, Ref_Constant, CashBeginningBalance, Ast_Beginning_Balance, Ref_Asset_Depreciation_Account, Ast_Document, Ast_Document_Detail, Ast_Document_Item, Ref_Template, Ref_Template_Detail

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
    list_display = ('AssetCardId', 'AssetId', 'AssetCardCode', 'AssetCardName', 'ManufacturedDate', 'ReceivedDate', 'MonthsToUse', 'UnitCost', 'UnitPrice', 'DailyExpense', 'ClientId', 'CreatedDate', 'CreatedBy')
    list_filter = ('AssetId__AssetTypeId', 'CreatedDate', 'CreatedBy', 'ClientId')
    search_fields = ('AssetCardCode', 'AssetCardName', 'AssetId__AssetName', 'AssetId__AssetCode', 'ClientId__ClientName', 'ClientId__ClientCode')
    ordering = ('AssetCardCode',)
    readonly_fields = ('CreatedDate', 'ModifiedDate')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('AssetId', 'AssetCardCode', 'AssetCardName', 'ClientId')
        }),
        ('Asset Details', {
            'fields': ('ManufacturedDate', 'ReceivedDate', 'MonthsToUse', 'UnitCost', 'UnitPrice', 'DailyExpense')
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
    list_display = ('TemplateId', 'TemplateName', 'DocumentTypeId', 'AccountId', 'CashFlowId', 'IsVat', 'IsDelete', 'CreatedBy', 'CreatedDate')
    list_filter = ('DocumentTypeId', 'AccountId', 'CashFlowId', 'IsVat', 'IsDelete', 'CreatedDate')
    search_fields = ('TemplateName', 'DocumentTypeId__Description', 'AccountId__AccountName', 'CashFlowId__Description')
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


