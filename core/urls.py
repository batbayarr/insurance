from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Accounts
    path('refaccounts/', views.refaccount_list, name='refaccount_list'),
    path('refaccounts/create/', views.refaccount_create, name='refaccount_create'),
    path('refaccounts/<int:pk>/update/', views.refaccount_update, name='refaccount_update'),
    path('refaccounts/<int:pk>/delete/', views.refaccount_delete, name='refaccount_delete'),

    # Clients
    path('refclients/', views.refclient_list, name='refclient_list'),
    path('refclients/create/', views.refclient_create, name='refclient_create'),
    path('refclients/<int:pk>/update/', views.refclient_update, name='refclient_update'),
    path('refclients/<int:pk>/delete/', views.refclient_delete, name='refclient_delete'),
    
    # Client Banks
    path('client-bank-list/<int:client_id>/', views.client_bank_list, name='client_bank_list'),
    path('client-bank/create/', views.client_bank_create, name='client_bank_create'),
    path('client-bank/update/<int:pk>/', views.client_bank_update, name='client_bank_update'),
    path('client-bank/delete/<int:pk>/', views.client_bank_delete, name='client_bank_delete'),
    
    
    
    # Inventory
    path('refinventory/', views.refinventory_list, name='refinventory_list'),
    path('refinventory/create/', views.refinventory_create, name='refinventory_create'),
    path('refinventory/<int:pk>/update/', views.refinventory_update, name='refinventory_update'),
    path('refinventory/<int:pk>/delete/', views.refinventory_delete, name='refinventory_delete'),
    
    
    # Period Lock API
    path('api/check-period-lock/', views.api_check_period_lock, name='api_check_period_lock'),
    path('api/validate-period-dates/', views.api_validate_period_dates, name='api_validate_period_dates'),
    path('api/exchange-rate-adjustment-bulk/', views.api_exchange_rate_adjustment_bulk, name='api_exchange_rate_adjustment_bulk'),
    
    # Cash Documents (Master-Detail)
    path('cashdocuments/', views.cashdocument_master_detail, name='cashdocument_master_detail'),
    path('cashdocuments/create/', views.cashdocument_create, name='cashdocument_create'),
    path('cashdocuments/<int:pk>/update/', views.cashdocument_update, name='cashdocument_update'),
    path('cashdocuments/<int:pk>/delete/', views.cashdocument_delete, name='cashdocument_delete'),
    
    # Cash Documents Views
    path('cashdocuments-tabs/', views.cash_documents, name='cash_journal'),
    path('cashimport/', views.cash_import, name='cash_import'),
    path('api/cash-documents-filtered/', views.get_cash_documents_filtered, name='get_cash_documents_filtered'),
    path('api/cash-documents-master/', views.get_cash_documents_master, name='api_cash_documents_master'),
    path('api/inventory-documents-master/', views.get_inventory_documents_master, name='api_inventory_documents_master'),
    path('api/asset-documents-master/', views.get_asset_documents_master, name='api_asset_documents_master'),
    
    # Trial Closing Entry (Depreciation & Closing)
    path('trial-closing-entry/', views.trial_closing_entry, name='trial_closing_entry'),
    path('api/depreciation-summary/', views.api_depreciation_summary, name='api_depreciation_summary'),
    path('api/asset-depreciation-expenses/', views.api_asset_depreciation_expenses, name='api_asset_depreciation_expenses'),
    path('api/calculate-depreciation/', views.api_calculate_depreciation, name='api_calculate_depreciation'),
    path('api/calculate-closing-record/', views.api_calculate_closing_record, name='api_calculate_closing_record'),
    
    
    # Cash Document Details
    path('cashdocumentdetails/', views.cashdocumentdetail_list, name='cashdocumentdetail_list'),
    path('cashdocumentdetails/<int:pk>/delete/', views.cashdocumentdetail_delete, name='cashdocumentdetail_delete'),
    
    # Unified Bulk Manage Details
    path('cashdocuments/<int:document_id>/bulk-manage-details/', views.bulk_manage_details, name='bulk_manage_details'),
    
    # API Bulk Manage Details
    path('api/cashdocuments/<int:document_id>/bulk-manage-details/', views.api_bulk_manage_details, name='api_bulk_manage_details'),
    
    # API Search for Large Datasets
    path('api/cashdocuments/search/', views.api_cashdocument_search, name='api_cashdocument_search'),
    
    # Inventory Documents (Master-Detail)
    path('invdocuments/', views.invdocument_master_detail, name='invdocument_master_detail'),
    path('invdocuments/create/', views.invdocument_create, name='invdocument_create'),
    path('invdocuments/create/<int:parentid>/', views.invdocument_create, name='invdocument_create_with_parent'),
    path('invdocuments/<int:pk>/update/', views.invdocument_update, name='invdocument_update'),
    path('invdocuments/<int:pk>/update/<int:parentid>/', views.invdocument_update, name='invdocument_update_with_parent'),
    path('invdocuments/<int:pk>/delete/', views.invdocument_delete, name='invdocument_delete'),
    
    
    # Inventory Document Items
    path('invdocuments/<int:document_id>/bulk-manage-details/', views.bulk_manage_inv_details, name='bulk_manage_inv_details'),
    path('invdocuments/<int:document_id>/bulk-manage-details/api/', views.bulk_manage_inv_details_api, name='bulk_manage_inv_details_api'),
    
    # Inventory Documents Views
    path('invdocuments-tabs/', views.inv_documents, name='invjournal'),
    path('api/inv-documents-filtered/', views.get_inv_documents_filtered, name='get_inv_documents_filtered'),
    path('api/inv-balance-data/', views.get_inv_balance_data, name='get_inv_balance_data'),
    
    # Asset Documents Views
    path('astdocuments-tabs/', views.ast_documents, name='astjournal'),
    path('api/ast-documents-filtered/', views.get_ast_documents_filtered, name='get_ast_documents_filtered'),
    path('api/ast-balance-data/', views.get_ast_balance_data, name='get_ast_balance_data'),
    
    # Currency Journal
    path('currencyjournal/', views.currency_journal, name='currency_journal'),

    # Asset Documents (Master-Detail)
    path('astdocuments/', views.astdocument_master_detail, name='astdocument_master_detail'),
    path('astdocuments/create/', views.astdocument_create, name='astdocument_create'),
    path('astdocuments/create/<int:parentid>/', views.astdocument_create, name='astdocument_create_with_parent'),
    path('astdocuments/<int:pk>/update/', views.astdocument_update, name='astdocument_update'),
    path('astdocuments/<int:pk>/update/<int:parentid>/', views.astdocument_update, name='astdocument_update_with_parent'),
    path('astdocuments/<int:pk>/delete/', views.astdocument_delete, name='astdocument_delete'),
    
    # Asset Document Items
    path('astdocuments/<int:document_id>/bulk-manage-details/', views.bulk_manage_ast_details, name='bulk_manage_ast_details'),
    path('astdocuments/<int:document_id>/bulk-manage-details/api/', views.api_bulk_manage_ast_details, name='api_bulk_manage_ast_details'),

    # Asset Management
    path('assets/', views.asset_master_detail, name='asset_master_detail'),
    path('assets/create/', views.refasset_create, name='refasset_create'),
    path('assets/<int:pk>/update/', views.refasset_update, name='refasset_update'),
    path('assets/<int:pk>/delete/', views.refasset_delete, name='refasset_delete'),
    
    # Asset Cards
    path('asset-cards/', views.ref_asset_card_list, name='ref_asset_card_list'),
    path('asset-cards/create/', views.ref_asset_card_create, name='ref_asset_card_create'),
    path('asset-cards/<int:pk>/update/', views.ref_asset_card_update, name='ref_asset_card_update'),
    path('asset-cards/<int:pk>/delete/', views.ref_asset_card_delete, name='ref_asset_card_delete'),

    # Asset Depreciation Accounts
    path('asset-depreciation-accounts/', views.ref_asset_depreciation_account_list, name='ref_asset_depreciation_account_list'),
    path('asset-depreciation-accounts/create/', views.ref_asset_depreciation_account_form, name='ref_asset_depreciation_account_create'),
    path('asset-depreciation-accounts/<int:ast_dep_id>/edit/', views.ref_asset_depreciation_account_form, name='ref_asset_depreciation_account_edit'),
    path('asset-depreciation-accounts/<int:ast_dep_id>/delete/', views.ref_asset_depreciation_account_delete, name='ref_asset_depreciation_account_delete'),

    # JSON API Endpoints
    path('api/assets/', views.assets_json, name='assets_json'),
    path('api/clients/', views.clients_json, name='clients_json'),
    path('api/accounts/', views.api_accounts_json, name='api_accounts_json'),
    path('api/client-lookup-by-name/', views.api_client_lookup_by_name, name='api_client_lookup_by_name'),
    path('api/account-lookup-by-code/', views.api_account_lookup_by_code, name='api_account_lookup_by_code'),
    path('api/cash-import-bulk/', views.api_cash_import_bulk, name='api_cash_import_bulk'),
    path('api/refclienttypes/', views.refclient_types_json, name='refclient_types_json'),
    

    # Beginning Balance (Generic)
    path('beginningbalances/<str:balance_type>/', views.cashbeginningbalance_list, name='beginningbalance_list'),
    path('beginningbalances/<str:balance_type>/create/', views.cashbeginningbalance_create, name='beginningbalance_create'),
    path('beginningbalances/<str:balance_type>/<int:balance_id>/update/', views.cashbeginningbalance_update, name='beginningbalance_update'),
    path('beginningbalances/<str:balance_type>/<int:balance_id>/delete/', views.cashbeginningbalance_delete, name='beginningbalance_delete'),
    
    # Legacy Cash Beginning Balance URLs (for backward compatibility)
    path('cashbeginningbalances/', views.cashbeginningbalance_list, {'balance_type': 'cash'}, name='cashbeginningbalance_list'),
    path('cashbeginningbalances/create/', views.cashbeginningbalance_create, name='cashbeginningbalance_create'),
    path('cashbeginningbalances/<int:balance_id>/update/', views.cashbeginningbalance_update, name='cashbeginningbalance_update'),
    path('cashbeginningbalances/<int:balance_id>/delete/', views.cashbeginningbalance_delete, name='cashbeginningbalance_delete'),
    
    # Inventory Beginning Balance URLs
    path('invbeginningbalances/', views.invbeginningbalance_list, name='invbeginningbalance_list'),
    path('invbeginningbalances/create/', views.invbeginningbalance_create, name='invbeginningbalance_create'),
    path('invbeginningbalances/<int:balance_id>/update/', views.invbeginningbalance_update, name='invbeginningbalance_update'),
    path('invbeginningbalances/<int:balance_id>/delete/', views.invbeginningbalance_delete, name='invbeginningbalance_delete'),
    
    # Asset Beginning Balance URLs
    path('astbeginningbalances/', views.astbeginningbalance_list, name='astbeginningbalance_list'),
    path('astbeginningbalances/create/', views.astbeginningbalance_create, name='astbeginningbalance_create'),
    path('astbeginningbalances/<int:balance_id>/update/', views.astbeginningbalance_update, name='astbeginningbalance_update'),
    path('astbeginningbalances/<int:balance_id>/delete/', views.astbeginningbalance_delete, name='astbeginningbalance_delete'),

    # API Endpoints
    path('api/get-next-document-number/', views.get_next_document_number, name='get_next_document_number'),
    path('api/log-error/', views.log_frontend_error, name='log_frontend_error'),
    path('api/get-databases/', views.get_databases_for_company, name='get_databases_for_company'),
    
    # Template API Endpoints
    path('api/templates/', views.api_templates_list, name='api_templates_list'),
    path('api/templates-by-account-code/', views.api_templates_by_account_code, name='api_templates_by_account_code'),
    path('api/templates/<int:template_id>/details/', views.api_template_details, name='api_template_details'),
    path('api/accounts/<int:account_id>/details/', views.api_account_details, name='api_account_details'),

    # Reports
    path('reports/trial-balance/', views.trial_balance, name='trial_balance'),
    path('reports/trial-recpay-balance/', views.recpay_balance, name='recpay_balance'),
    path('reports/account-statement/', views.account_statement, name='account_statement'),
    path('reports/subsidiary-ledger/', views.subsidiary_ledger, name='subsidiary_ledger'),
    path('reports/y-balance/', views.y_balance, name='y_balance'),
    path('api/account-statement/', views.account_statement_detail, name='account_statement_detail'),
    path('api/subsidiary-ledger/', views.subsidiary_ledger_detail, name='subsidiary_ledger_detail'),
    path('api/inventory-balance-warehouse/', views.api_get_inventory_balance_warehouse, name='api_get_inventory_balance_warehouse'),
    path('api/inventory-list/', views.api_get_inventory_list, name='api_get_inventory_list'),
    
    # Depreciation
    path('depreciation/calculate/', views.calculate_depreciation_view, name='calculate_depreciation'),
    
    # Template Management
    path('templates/', views.template_master_detail, name='template_master_detail'),
    path('templates/create/', views.template_create, name='template_create'),
    
    # Period Lock Management
    path('period-lock/', views.period_lock_list, name='period_lock_list'),
    path('period-lock/<int:period_id>/toggle/', views.period_lock_toggle, name='period_lock_toggle'),
    path('templates/<int:pk>/update/', views.template_update, name='template_update'),
    path('templates/<int:pk>/delete/', views.template_delete, name='template_delete'),
    path('templates/<int:template_id>/details/create/', views.template_detail_create, name='template_detail_create'),
    path('templates/details/<int:pk>/update/', views.template_detail_update, name='template_detail_update'),
    path('templates/details/<int:pk>/delete/', views.template_detail_delete, name='template_detail_delete'),
    
    path('api/test/', views.test_api, name='test_api'),

    ] 