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
    
    # Insurance Clients
    path('refinsclients/', views.refinsclient_list, name='refinsclient_list'),
    path('refinsclients/create/', views.refinsclient_create, name='refinsclient_create'),
    path('refinsclients/<int:pk>/update/', views.refinsclient_update, name='refinsclient_update'),
    path('refinsclients/<int:pk>/delete/', views.refinsclient_delete, name='refinsclient_delete'),
    
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
    path('trial-depreciation/', views.trial_depreciation, name='trial_depreciation'),
    path('api/depreciation-summary/', views.api_depreciation_summary, name='api_depreciation_summary'),
    path('api/asset-depreciation-expenses/', views.api_asset_depreciation_expenses, name='api_asset_depreciation_expenses'),
    path('api/calculate-depreciation/', views.api_calculate_depreciation, name='api_calculate_depreciation'),
    path('api/calculate-closing-record/', views.api_calculate_closing_record, name='api_calculate_closing_record'),
    path('api/delete-closing-entries/', views.api_delete_closing_entries, name='api_delete_closing_entries'),
    path('api/delete-depreciation-entries/', views.api_delete_depreciation_entries, name='api_delete_depreciation_entries'),
    path('api/check-future-period-depreciation/', views.api_check_future_period_depreciation, name='api_check_future_period_depreciation'),
    path('api/period-begin-date/', views.api_get_period_begin_date, name='api_get_period_begin_date'),
    path('api/periods-list/', views.api_get_periods_list, name='api_get_periods_list'),
    path('api/calculate-cost-adjustment/', views.api_calculate_cost_adjustment, name='api_calculate_cost_adjustment'),
    
    
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
    path('api/asset-cards/', views.asset_cards_json, name='asset_cards_json'),
    path('api/clients/', views.clients_json, name='clients_json'),
    path('api/accounts/', views.api_accounts_json, name='api_accounts_json'),
    path('api/client-lookup-by-name/', views.api_client_lookup_by_name, name='api_client_lookup_by_name'),
    path('api/account-lookup-by-code/', views.api_account_lookup_by_code, name='api_account_lookup_by_code'),
    path('api/check-account-uniqueness/', views.check_account_uniqueness, name='check_account_uniqueness'),
    path('api/check-client-name-register-uniqueness/', views.check_client_name_register_uniqueness, name='check_client_name_register_uniqueness'),
    path('api/cash-import-bulk/', views.api_cash_import_bulk, name='api_cash_import_bulk'),
    path('api/refclienttypes/', views.refclient_types_json, name='refclient_types_json'),
    path('api/refinventorytypes/', views.refinventory_types_json, name='refinventory_types_json'),
    path('api/refmeasurements/', views.refmeasurements_json, name='refmeasurements_json'),
    path('api/asset-card-usage-check/', views.api_asset_card_usage_check, name='api_asset_card_usage_check'),
    path('api/check-depreciation-expense-by-date/', views.api_check_depreciation_expense_by_date, name='api_check_depreciation_expense_by_date'),
    path('api/check-all-previous-periods-depreciation-by-date/', views.api_check_all_previous_periods_depreciation_by_date, name='api_check_all_previous_periods_depreciation_by_date'),
    path('api/check-asset-document-balance/', views.api_check_asset_document_balance, name='api_check_asset_document_balance'),
    path('api/check-document-period-depreciation/', views.api_check_document_period_depreciation, name='api_check_document_period_depreciation'),
    path('api/check-period-depreciation-by-date/', views.api_check_period_depreciation_by_date, name='api_check_period_depreciation_by_date'),
    path('api/check-asset-document-has-details/', views.api_check_asset_document_has_details, name='api_check_asset_document_has_details'),
    path('api/check-asset-card-depreciation/', views.api_check_asset_card_has_depreciation, name='api_check_asset_card_has_depreciation'),
    path('api/check-asset-card-usage-edit-delete/', views.api_check_asset_card_usage_for_edit_delete, name='api_check_asset_card_usage_for_edit_delete'),
    

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
    path('api/trial-balance-by-stbalance/', views.api_trial_balance_by_stbalance, name='api_trial_balance_by_stbalance'),
    path('api/account-statement/', views.account_statement_detail, name='account_statement_detail'),
    path('api/subsidiary-ledger/', views.subsidiary_ledger_detail, name='subsidiary_ledger_detail'),
    path('api/inventory-balance-warehouse/', views.api_get_inventory_balance_warehouse, name='api_get_inventory_balance_warehouse'),
    path('api/inventory-list/', views.api_get_inventory_list, name='api_get_inventory_list'),
    
    
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

    # Insurance Product Type & Product (Master-Detail)
    path('product-types/', views.product_type_master_detail, name='product_type_master_detail'),
    path('product-types/create/', views.product_type_create, name='product_type_create'),
    path('product-types/<int:pk>/update/', views.product_type_update, name='product_type_update'),
    path('product-types/<int:pk>/delete/', views.product_type_delete, name='product_type_delete'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/update/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # API endpoints for product type and product
    path('api/product-types/', views.api_product_types_list, name='api_product_types_list'),
    path('api/product-type/<int:pk>/', views.api_product_type_detail, name='api_product_type_detail'),
    path('api/products/', views.api_products_list, name='api_products_list'),
    path('api/product/<int:pk>/', views.api_product_detail, name='api_product_detail'),
    
    # Insurance Risk Type & Risk (Master-Detail)
    path('risk-types/', views.risk_type_master_detail, name='risk_type_master_detail'),
    path('risk-types/create/', views.risk_type_create, name='risk_type_create'),
    path('risk-types/<int:pk>/update/', views.risk_type_update, name='risk_type_update'),
    path('risk-types/<int:pk>/delete/', views.risk_type_delete, name='risk_type_delete'),
    path('risks/create/', views.risk_create, name='risk_create'),
    path('risks/<int:pk>/update/', views.risk_update, name='risk_update'),
    path('risks/<int:pk>/delete/', views.risk_delete, name='risk_delete'),
    
    # API endpoints for risk type and risk
    path('api/risk-types/', views.api_risk_types_list, name='api_risk_types_list'),
    path('api/risk-type/<int:pk>/', views.api_risk_type_detail, name='api_risk_type_detail'),
    path('api/risks/', views.api_risks_list, name='api_risks_list'),
    path('api/risk/<int:pk>/', views.api_risk_detail, name='api_risk_detail'),
    
    # Insurance Item & Item Question (Master-Detail)
    path('items/', views.item_master_detail, name='item_master_detail'),
    path('items/create/', views.item_create, name='item_create'),
    path('items/<int:pk>/update/', views.item_update, name='item_update'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),
    path('item-questions/create/', views.item_question_create, name='item_question_create'),
    path('item-questions/<int:pk>/update/', views.item_question_update, name='item_question_update'),
    path('item-questions/<int:pk>/delete/', views.item_question_delete, name='item_question_delete'),
    
    # API endpoints for item and item question
    path('api/items/', views.api_items_list, name='api_items_list'),
    path('api/item/<int:pk>/', views.api_item_detail, name='api_item_detail'),
    path('api/item-questions/', views.api_item_questions_list, name='api_item_questions_list'),
    path('api/item-question/<int:pk>/', views.api_item_question_detail, name='api_item_question_detail'),

    # Insurance Policy Template & Detail (Master-Detail)
    path('insurance-templates/', views.template_management, name='template_management'),
    
    # Insurance Policy List
    path('policies/', views.policy_list, name='policy_list'),
    path('policies/<int:policy_id>/update/', views.policy_update, name='policy_update'),
    path('policies/<int:policy_id>/delete/', views.policy_delete, name='policy_delete'),
    path('api/templates/upload-file/', views.api_template_upload_file, name='api_template_upload_file'),
    path('policy-templates/create/', views.policy_template_create, name='policy_template_create'),
    path('policy-templates/<int:pk>/update/', views.policy_template_update, name='policy_template_update'),
    path('policy-templates/<int:pk>/delete/', views.policy_template_delete, name='policy_template_delete'),
    # API endpoints for policy template
    path('api/policy-template/<int:pk>/', views.api_policy_template_detail, name='api_policy_template_detail'),
    path('api/policy-template/<int:template_id>/full-data/', views.api_policy_template_full_data, name='api_policy_template_full_data'),

    # Insurance Policy
    path('policies/create/', views.policy_create, name='policy_create'),
    path('policies/<int:policy_id>/generate-word/', views.policy_generate_word, name='policy_generate_word'),
    path('api/policy-item/<int:policy_main_product_item_id>/questions/', views.api_policy_item_questions, name='api_policy_item_questions'),
    path('api/policy-item/<int:policy_main_product_item_id>/risks/', views.api_policy_item_risks, name='api_policy_item_risks'),
    path('api/policy/<int:policy_id>/edit-data/', views.api_policy_edit_data, name='api_policy_edit_data'),
    
    # Insurance Item Type
    path('item-types/', views.item_type_list, name='item_type_list'),
    path('item-types/create/', views.item_type_create, name='item_type_create'),
    path('item-types/<int:pk>/update/', views.item_type_update, name='item_type_update'),
    path('item-types/<int:pk>/delete/', views.item_type_delete, name='item_type_delete'),
    # API endpoints for item type
    path('api/item-types/', views.api_item_types_list, name='api_item_types_list'),
    path('api/item-type/<int:pk>/', views.api_item_type_detail, name='api_item_type_detail'),
    
    # Insurance Branch
    path('branches/', views.branch_list, name='branch_list'),
    path('branches/create/', views.branch_create, name='branch_create'),
    path('branches/<int:pk>/update/', views.branch_update, name='branch_update'),
    path('branches/<int:pk>/delete/', views.branch_delete, name='branch_delete'),
    # API endpoints for branch
    path('api/branches/', views.api_branches_list, name='api_branches_list'),
    path('api/branch/<int:pk>/', views.api_branch_detail, name='api_branch_detail'),
    
    # Insurance Channel
    path('channels/', views.channel_list, name='channel_list'),
    path('channels/create/', views.channel_create, name='channel_create'),
    path('channels/<int:pk>/update/', views.channel_update, name='channel_update'),
    path('channels/<int:pk>/delete/', views.channel_delete, name='channel_delete'),
    # API endpoints for channel
    path('api/channels/', views.api_channels_list, name='api_channels_list'),
    path('api/channel/<int:pk>/', views.api_channel_detail, name='api_channel_detail'),
    # API endpoint for user branch and channel
    path('api/user-branch-channel/', views.api_user_branch_channel, name='api_user_branch_channel'),
    # API endpoint for branch users (for agent dropdown)
    path('api/branch-users/', views.api_branch_users_list, name='api_branch_users_list'),
    # API endpoint for currencies
    path('api/currencies/', views.api_currencies_list, name='api_currencies_list'),
    
    # Template Design
    path('template-designs/', views.template_design_list, name='template_design_list'),
    path('template-designs/create/', views.template_design_create, name='template_design_create'),
    path('template-designs/<int:pk>/update/', views.template_design_update, name='template_design_update'),
    path('template-designs/<int:pk>/delete/', views.template_design_delete, name='template_design_delete'),
    # API endpoints for template design
    path('api/template-designs/', views.api_template_designs_list, name='api_template_designs_list'),
    path('api/template-design/<int:pk>/', views.api_template_design_detail, name='api_template_design_detail'),
    path('api/table-fields/<str:table_name>/', views.api_table_fields, name='api_table_fields'),

    ] 