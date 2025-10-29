from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
import time
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import ProtectedError
import json
from .models import Ref_Account_Type, Ref_Account, RefClientType, RefClient, Ref_Currency, RefInventory, Ref_Document_Type, Ref_Document_Counter, Ref_CashFlow, Ref_Contract, Ref_Warehouse, Cash_Document, Cash_DocumentDetail, Inv_Document, Inv_Document_Item, Inv_Document_Detail, Ref_Asset_Type, RefAsset, Ref_Asset_Card, CashBeginningBalance, Inv_Beginning_Balance, Ast_Beginning_Balance, Ast_Document, Ast_Document_Detail, Ast_Document_Item, Ref_Asset_Depreciation_Account, Ref_Period, Ref_Template, Ref_Template_Detail, AstDepreciationExpense
from django.db import connection
from .forms import Ref_AccountForm, RefClientForm, RefInventoryForm, CashDocumentForm, InvDocumentForm, RefAssetForm, Ref_Asset_CardForm, InvBeginningBalanceForm, AstDocumentForm, Ref_Asset_Depreciation_AccountForm, Ref_TemplateForm, Ref_Template_DetailForm
from .utils import get_available_databases, set_database
from .error_handling import (
    handle_errors, handle_ajax_errors, handle_form_errors, 
    safe_database_operation, Silicon4Error, ValidationError, 
    BusinessLogicError, DatabaseError, PermissionError,
    validate_required_fields, validate_user_permissions, validate_business_rules,
    log_frontend_error
)


def get_databases_for_company(request):
    """
    AJAX endpoint to get available databases for a company code
    """
    if request.method == 'GET':
        company_code = request.GET.get('company_code', '').strip()
        
        if not company_code:
            return JsonResponse({'error': 'Company code is required'}, status=400)
        
        # Get databases for the company code
        databases = get_available_databases(company_code)
        
        if not databases:
            return JsonResponse({'error': 'Та компаниа бүртүүлээгүй байна'}, status=404)
        
        # Format response for dropdown
        response_data = {
            'databases': [
                {
                    'value': db['db_name'],
                    'label': db['description']
                }
                for db in databases
            ]
        }
        
        return JsonResponse(response_data)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def custom_login(request):
    """Custom login view with company code and database selection"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        company_code = request.POST.get('company_code', '').strip()
        selected_db = request.POST.get('database')
        
        if form.is_valid() and company_code and selected_db:
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Validate that the selected database belongs to the company code
            available_databases = get_available_databases(company_code)
            db_names = [db['db_name'] for db in available_databases]
            
            if selected_db not in db_names:
                form.add_error(None, 'Selected database is not valid for this company')
            else:
                # Store selected database and company code in session
                request.session['selected_database'] = selected_db
                request.session['company_code'] = company_code
                
                # Set the database name in settings
                set_database(selected_db)
                
                # Use the selected database for authentication
                from django.contrib.auth import authenticate
                
                # Authenticate using the selected database
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('home')
                else:
                    # Add error message for invalid credentials
                    form.add_error(None, 'Invalid username or password')
        else:
            # Add appropriate error messages
            if not company_code:
                form.add_error(None, 'Please enter company code')
            elif not selected_db:
                form.add_error(None, 'Please select a database')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {
        'form': form
    })


def custom_logout(request):
    """Custom logout view"""
    logout(request)
    # Clear the selected database from session
    if 'selected_database' in request.session:
        del request.session['selected_database']
    return redirect('login')


@login_required
def home(request):
    """Home page view"""
    return render(request, 'home.html')


@login_required
@permission_required('core.view_ref_account', raise_exception=True)
def refaccount_list(request):
    """List all accounts with pagination and inline filtering"""
    accounts_list = Ref_Account.objects.select_related('AccountTypeId', 'CurrencyId').all()
    
    # Check if this is a modal request for account selection
    is_modal = request.GET.get('modal') == 'true'
    is_select_mode = request.GET.get('select_mode') == 'true'
    
    # Apply filters
    code_filter = request.GET.get('code', '')
    name_filter = request.GET.get('name', '')
    type_filter = request.GET.get('type', '')
    description_filter = request.GET.get('description', '')
    status_filter = request.GET.get('status', '')
    account_type_filter = request.GET.get('account_type', '')
    document_type_id = request.GET.get('document_type_id')
    
    if code_filter:
        accounts_list = accounts_list.filter(AccountCode__icontains=code_filter)
    
    if name_filter:
        accounts_list = accounts_list.filter(AccountName__icontains=name_filter)
    
    if type_filter:
        accounts_list = accounts_list.filter(AccountTypeId__AccountTypeName__icontains=type_filter)
    
    if description_filter:
        accounts_list = accounts_list.filter(Description__icontains=description_filter)
    
    if status_filter:
        if status_filter == 'active':
            accounts_list = accounts_list.filter(IsDelete=False)
        elif status_filter == 'inactive':
            accounts_list = accounts_list.filter(IsDelete=True)
    
    # If no explicit account_type filter but we have document_type_id, derive it
    # Mapping rules:
    # - Inventory documents (5,6,7) → account types 8,9,11
    # - ParentId == 1 → account type 1
    # - ParentId == 2 → account type 2
    # - Otherwise → account types 1,2
    if not account_type_filter and document_type_id:
        # Inventory documents: 5, 6, 7 → account types 8, 9, 11
        if str(document_type_id) in {'5', '6', '7'}:
            account_type_filter = '8,9,11'
        else:
            # Fallback to ParentId mapping
            try:
                doc_type = Ref_Document_Type.objects.get(DocumentTypeId=document_type_id)
                if doc_type.ParentId == 1:
                    account_type_filter = '1'
                elif doc_type.ParentId == 2:
                    account_type_filter = '2'
                else:
                    account_type_filter = '1,2'
            except Ref_Document_Type.DoesNotExist:
                pass

    # Filter by account type ID (for document type filtering)
    if account_type_filter:
        # Check if multiple account types are provided (comma-separated)
        if ',' in account_type_filter:
            account_type_ids = [int(x.strip()) for x in account_type_filter.split(',') if x.strip().isdigit()]
            accounts_list = accounts_list.filter(AccountTypeId__AccountTypeId__in=account_type_ids)
        else:
            # Single account type ID
            accounts_list = accounts_list.filter(AccountTypeId__AccountTypeId=account_type_filter)
    
    # Order by code
    accounts_list = accounts_list.order_by('AccountCode')
    
    # For modal/select mode, show more items and no pagination
    if is_modal or is_select_mode:
        accounts = accounts_list
        paginator = None
    else:
        # Pagination
        paginator = Paginator(accounts_list, 4)  # Show 4 items per page
        page = request.GET.get('page')
        
        try:
            accounts = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page
            accounts = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results
            accounts = paginator.page(paginator.num_pages)
    
    # Get all account types for filter dropdown
    account_types = Ref_Account_Type.objects.all().order_by('AccountTypeName')
    
    context = {
        'accounts': accounts,
        'paginator': paginator,
        'account_types': account_types,
        'filters': {
            'code': code_filter,
            'name': name_filter,
            'type': type_filter,
            'description': description_filter,
            'status': status_filter,
        },
        'is_modal': is_modal,
        'is_select_mode': is_select_mode,
    }
    
    return render(request, 'core/refaccount_list.html', context)


@login_required
@permission_required('core.add_ref_account', raise_exception=True)
def refaccount_create(request):
    """Create new account"""
    if request.method == 'POST':
        # Handle the custom field name
        post_data = request.POST.copy()
        if 'account_type_selector' in post_data:
            post_data['AccountTypeId'] = post_data['account_type_selector']
        
        form = Ref_AccountForm(post_data)
        if form.is_valid():
            form.save()
            return redirect('core:refaccount_list')
        else:
            # Debug: print form errors
            print("Form errors:", form.errors)
            print("Form data:", request.POST)
    else:
        form = Ref_AccountForm()
    
    account_types = Ref_Account_Type.objects.all()
    currencies = Ref_Currency.objects.filter(IsActive=True).order_by('CurrencyId')
    return render(request, 'core/refaccount_form.html', {
        'form': form,
        'item': None,  # No existing item for create
        'account_types': account_types,
        'currencies': currencies
    })


@login_required
def refaccount_update(request, pk):
    """Update existing account"""
    account = get_object_or_404(Ref_Account, pk=pk)
    
    if request.method == 'POST':
        # Handle the custom field name
        post_data = request.POST.copy()
        if 'account_type_selector' in post_data:
            post_data['AccountTypeId'] = post_data['account_type_selector']
        
        form = Ref_AccountForm(post_data, instance=account)
        if form.is_valid():
            form.save()
            return redirect('core:refaccount_list')
    else:
        form = Ref_AccountForm(instance=account)
    
    account_types = Ref_Account_Type.objects.all()
    currencies = Ref_Currency.objects.filter(IsActive=True).order_by('CurrencyId')
    return render(request, 'core/refaccount_form.html', {
        'item': account,
        'form': form,
        'account_types': account_types,
        'currencies': currencies
    })


@login_required
@permission_required('core.delete_ref_account', raise_exception=True)
def refaccount_delete(request, pk):
    """Delete account with soft delete"""
    account = get_object_or_404(Ref_Account, pk=pk)
    
    # Check if this is a modal request
    if request.GET.get('modal'):
        # Return modal content
        return render(request, 'core/components/delete_modal.html', {
            'item_name': f"{account.AccountCode} - {account.AccountName}",
            'delete_url': reverse('core:refaccount_delete', args=[pk])
        })
    
    # Handle API request (JSON)
    if request.method == 'POST' and request.headers.get('Content-Type') == 'application/json':
        try:
            import json
            data = json.loads(request.body)
            
            # Check if already deleted
            if account.IsDelete:
                return JsonResponse({
                    'success': False,
                    'message': f'Account "{account.AccountCode} - {account.AccountName}" is already deleted.'
                })
            
            # Perform soft delete
            account.IsDelete = True
            account.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Account "{account.AccountCode} - {account.AccountName}" has been deleted successfully.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting account: {str(e)}'
            })
    
    # Handle regular form POST
    if request.method == 'POST':
        try:
            # Check if already deleted
            if account.IsDelete:
                messages.warning(request, f'Account "{account.AccountCode} - {account.AccountName}" is already deleted.')
                return redirect('core:refaccount_list')
            
            # Perform soft delete
            account.IsDelete = True
            account.save()
            messages.success(request, f'Account "{account.AccountCode} - {account.AccountName}" has been deleted successfully.')
            
        except Exception as e:
            messages.error(request, f'Error deleting account: {str(e)}')
        
        return redirect('core:refaccount_list')
    
    # GET request without modal parameter - redirect to list
    return redirect('core:refaccount_list')


@login_required
@permission_required('core.view_refclient', raise_exception=True)
def refclient_list(request):
    """List all clients with pagination and inline filtering"""
    clients_list = RefClient.objects.select_related('ClientType').all()
    
    # Check if this is a modal request for client selection
    is_modal = request.GET.get('modal') == 'true'
    is_select_mode = request.GET.get('select_mode') == 'true'
    
    # Apply filters
    code_filter = request.GET.get('code', '')
    name_filter = request.GET.get('name', '')
    type_filter = request.GET.get('type', '')
    register_filter = request.GET.get('register', '')
    status_filter = request.GET.get('status', '')
    
    if code_filter:
        clients_list = clients_list.filter(ClientCode__icontains=code_filter)
    if name_filter:
        clients_list = clients_list.filter(ClientName__icontains=name_filter)
    if type_filter:
        clients_list = clients_list.filter(ClientType__ClientTypeName__icontains=type_filter)
    if register_filter:
        clients_list = clients_list.filter(ClientRegister__icontains=register_filter)
    if status_filter:
        if status_filter == 'active':
            clients_list = clients_list.filter(IsDelete=False)
        elif status_filter == 'deleted':
            clients_list = clients_list.filter(IsDelete=True)
    
    clients_list = clients_list.order_by('ClientCode')
    paginator = Paginator(clients_list, 20)  # Show 20 items per page
    page = request.GET.get('page')
    try:
        clients = paginator.page(page)
    except PageNotAnInteger:
        clients = paginator.page(1)
    except EmptyPage:
        clients = paginator.page(paginator.num_pages)
    
    # Get all client types for filter dropdown
    client_types = RefClientType.objects.all().order_by('ClientTypeName')
    
    # For modal requests, return a simplified template
    if is_modal and is_select_mode:
        return render(request, 'core/refclient_list.html', {
            'clients': clients,
            'is_modal': True,
            'is_select_mode': True,
            'client_types': client_types,  # Include client types for modal
        })
    
    return render(request, 'core/refclient_list.html', {
        'clients': clients,
        'paginator': paginator,
        'client_types': client_types,
        'filters': {
            'code': code_filter,
            'name': name_filter,
            'type': type_filter,
            'register': register_filter,
            'status': status_filter,
        }
    })

@login_required
@permission_required('core.add_refclient', raise_exception=True)
def refclient_create(request):
    """Create new client"""
    if request.method == 'POST':
        form = RefClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.CreatedBy = request.user
            client.save()
            
            # Check if this is an AJAX request from modal
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Client created successfully!',
                    'client_id': client.ClientId,
                    'client_code': client.ClientCode,
                    'client_name': client.ClientName
                })
            
            return redirect('core:refclient_list')
        else:
            # Check if this is an AJAX request from modal
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Validation failed',
                    'errors': form.errors
                })
    else:
        form = RefClientForm()
    
    client_types = RefClientType.objects.all()
    return render(request, 'core/refclient_form.html', {
        'form': form,
        'client_types': client_types
    })

@login_required
@permission_required('core.change_refclient', raise_exception=True)
def refclient_update(request, pk):
    """Update existing client"""
    client = get_object_or_404(RefClient, pk=pk)
    if request.method == 'POST':
        form = RefClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save(commit=False)
            client.ModifiedBy = request.user
            client.save()
            
            # Check if this is an AJAX request from modal
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Client updated successfully!',
                    'client_id': client.ClientId,
                    'client_code': client.ClientCode,
                    'client_name': client.ClientName
                })
            
            return redirect('core:refclient_list')
        else:
            # Check if this is an AJAX request from modal
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Validation failed',
                    'errors': form.errors
                })
    else:
        form = RefClientForm(instance=client)
    
    client_types = RefClientType.objects.all()
    return render(request, 'core/refclient_form.html', {
        'form': form, 
        'item': client,
        'client_types': client_types
    })

@login_required
@permission_required('core.delete_refclient', raise_exception=True)
def refclient_delete(request, pk):
    client = get_object_or_404(RefClient, pk=pk)
    
    # Check if this is a modal request
    if request.GET.get('modal'):
        # Return modal content
        return render(request, 'core/components/delete_modal.html', {
            'item_name': client.ClientName,
            'delete_url': reverse('core:refclient_delete', args=[pk])
        })
    
    # Handle API request (JSON)
    if request.method == 'POST' and request.headers.get('Content-Type') == 'application/json':
        try:
            import json
            data = json.loads(request.body)
            
            # Check if already deleted
            if client.IsDelete:
                return JsonResponse({
                    'success': False,
                    'message': f'Client "{client.ClientCode} - {client.ClientName}" is already deleted.'
                })
            
            # Perform soft delete
            client.IsDelete = True
            if hasattr(client, 'ModifiedBy'):
                client.ModifiedBy = request.user
            client.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Client "{client.ClientCode} - {client.ClientName}" has been deleted successfully.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting client: {str(e)}'
            })
    
    # Handle regular form POST
    if request.method == 'POST':
        try:
            # Check if already deleted
            if client.IsDelete:
                messages.warning(request, f'Client "{client.ClientCode} - {client.ClientName}" is already deleted.')
                return redirect('core:refclient_list')
            
            # Perform soft delete
            client.IsDelete = True
            if hasattr(client, 'ModifiedBy'):
                client.ModifiedBy = request.user
            client.save()
            messages.success(request, f'Client "{client.ClientCode} - {client.ClientName}" has been deleted successfully.')
            
        except Exception as e:
            messages.error(request, f'Error deleting client: {str(e)}')
        
        return redirect('core:refclient_list')
    
    # GET request without modal parameter - redirect to list
    return redirect('core:refclient_list')


# RefClientType Views


# Template views removed





















@login_required
@permission_required('core.view_refinventory', raise_exception=True)
def refinventory_list(request):
    """List all inventory items with pagination and inline filtering"""
    inventory_list = RefInventory.objects.all()
    
    # Check if this is a modal request for inventory selection
    is_modal = request.GET.get('modal') == 'true'
    is_select_mode = request.GET.get('select_mode') == 'true'
    
    # Apply filters
    name_filter = request.GET.get('name', '')
    created_by_filter = request.GET.get('created_by', '')
    status_filter = request.GET.get('status', '')
    
    if name_filter:
        inventory_list = inventory_list.filter(InventoryName__icontains=name_filter)
    
    if created_by_filter:
        inventory_list = inventory_list.filter(CreatedBy__username__icontains=created_by_filter)
    
    if status_filter:
        if status_filter == 'active':
            inventory_list = inventory_list.filter(IsActive=True)
        elif status_filter == 'inactive':
            inventory_list = inventory_list.filter(IsActive=False)
    
    # Order by name
    inventory_list = inventory_list.order_by('InventoryName')
    
    # For modal/select mode, show more items and no pagination
    if is_modal or is_select_mode:
        inventories = inventory_list
        paginator = None
    else:
        # Pagination
        paginator = Paginator(inventory_list, 10)  # Show 10 items per page
        page = request.GET.get('page')
        
        try:
            inventories = paginator.page(page)
        except PageNotAnInteger:
            inventories = paginator.page(1)
        except EmptyPage:
            inventories = paginator.page(paginator.num_pages)
    
    context = {
        'inventories': inventories,
        'paginator': paginator,
        'name_filter': name_filter,
        'created_by_filter': created_by_filter,
        'status_filter': status_filter,
        'is_modal': is_modal,
        'is_select_mode': is_select_mode,
    }
    
    return render(request, 'core/refinventory_list.html', context)


@login_required
@permission_required('core.add_refinventory', raise_exception=True)
def refinventory_create(request):
    """Create a new inventory item"""
    if request.method == 'POST':
        form = RefInventoryForm(request.POST)
        if form.is_valid():
            inventory = form.save(commit=False)
            inventory.CreatedBy = request.user
            inventory.save()
            messages.success(request, 'Inventory item created successfully.')
            return redirect('core:refinventory_list')
    else:
        form = RefInventoryForm()
    
    return render(request, 'core/refinventory_form.html', {'form': form, 'title': 'Create Inventory Item'})


@login_required
@permission_required('core.change_refinventory', raise_exception=True)
def refinventory_update(request, pk):
    """Update an existing inventory item"""
    inventory = get_object_or_404(RefInventory, pk=pk)
    
    if request.method == 'POST':
        form = RefInventoryForm(request.POST, instance=inventory)
        if form.is_valid():
            inventory = form.save(commit=False)
            inventory.ModifiedBy = request.user
            inventory.save()
            messages.success(request, 'Inventory item updated successfully.')
            return redirect('core:refinventory_list')
    else:
        form = RefInventoryForm(instance=inventory)
    
    return render(request, 'core/refinventory_form.html', {
        'form': form, 
        'title': 'Update Inventory Item',
        'inventory': inventory
    })


@login_required
@permission_required('core.delete_refinventory', raise_exception=True)
def refinventory_delete(request, pk):
    """Delete an inventory item"""
    inventory = get_object_or_404(RefInventory, pk=pk)
    
    if request.method == 'POST':
        try:
            inventory.delete()
            messages.success(request, 'Inventory item deleted successfully.')
        except ProtectedError as e:
            messages.error(request, f'Cannot delete inventory item "{inventory.InventoryName}" because it is referenced by other records. Please remove all references first.')
        return redirect('core:refinventory_list')
    
    context = {
        'inventory': inventory,
        'item_name': inventory.InventoryName,
        'delete_url': reverse('core:refinventory_delete', kwargs={'pk': pk})
    }
    
    return render(request, 'core/components/delete_modal.html', context)



@login_required
@permission_required('core.view_cash_document', raise_exception=True)
def cashdocument_master_detail(request):
    """Master-detail view for cash documents
    
    Master table data is loaded via API endpoint (get_cash_documents_master).
    This view handles the initial page load and AJAX requests for detail grid.
    """
    
    # Get selected document ID for detail grid (AJAX request)
    selected_document_id = request.GET.get('selected_document')
    document_details = []
    selected_document = None
    
    if selected_document_id:
        try:
            selected_document = Cash_Document.objects.get(DocumentId=selected_document_id)
            # Optimize query: get all details with related objects in one query using ForeignKeys
            document_details = Cash_DocumentDetail.objects.filter(
                DocumentId=selected_document_id
            ).select_related('AccountId', 'ClientId', 'CurrencyId', 'CashFlowId', 'ContractId')
            
            # Totals are now calculated in frontend - no backend calculation needed
        except Cash_Document.DoesNotExist:
            selected_document_id = None
    
    context = {
        'document_details': document_details,
        'selected_document': selected_document,
        'selected_document_id': selected_document_id,
    }
    
    # Check if this is an AJAX request for detail grid only
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('ajax') == '1':
        # Return only the detail grid HTML
        return render(request, 'core/components/cash_document_detail_grid.html', context)
    
    return render(request, 'core/cashdocument_master_detail.html', context)


@login_required
@permission_required('core.view_cash_document', raise_exception=True)
def get_cash_documents_master(request):
    """API endpoint for cash documents master table with date range filtering"""
    try:
        # Get date range parameters
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        
        # Base query - only non-deleted records
        documents_query = Cash_Document.objects.select_related(
            'AccountId', 'ClientId', 'CurrencyId', 'DocumentTypeId', 'TemplateId', 'CreatedBy'
        ).filter(IsDelete=False)
        
        # Apply date range filter
        if start_date:
            documents_query = documents_query.filter(DocumentDate__gte=start_date)
        if end_date:
            documents_query = documents_query.filter(DocumentDate__lte=end_date)
        
        # Order by document date (newest first)
        documents_query = documents_query.order_by('-DocumentDate')
        
        # Build response data
        documents_data = []
        for doc in documents_query:
            documents_data.append({
                'DocumentId': doc.DocumentId,
                'DocumentNo': doc.DocumentNo,
                'DocumentTypeCode': doc.DocumentTypeId.DocumentTypeCode if doc.DocumentTypeId else '',
                'ClientName': doc.ClientId.ClientName if doc.ClientId else '',
                'DocumentDate': doc.DocumentDate.strftime('%Y-%m-%d') if doc.DocumentDate else '',
                'Description': doc.Description or '',
                'IsVat': doc.IsVat,
                'AccountCode': doc.AccountId.AccountCode if doc.AccountId else '',
                'AccountName': doc.AccountId.AccountName if doc.AccountId else '',
                'CurrencyName': doc.CurrencyId.Currency_name if doc.CurrencyId else '',
                'CurrencyAmount': float(doc.CurrencyAmount) if doc.CurrencyAmount else 0,
                'CurrencyExchange': float(doc.CurrencyExchange) if doc.CurrencyExchange else 0,
                'CurrencyMNT': float(doc.CurrencyMNT) if doc.CurrencyMNT else 0,
                'CreatedByUsername': doc.CreatedBy.username if doc.CreatedBy else '',
                'CreatedById': doc.CreatedBy.id if doc.CreatedBy else None,
            })
        
        return JsonResponse({
            'success': True,
            'documents': documents_data,
            'count': len(documents_data)
        })
        
    except Exception as e:
        logger.error(f"Error in get_cash_documents_master: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def api_check_period_lock(request):
    """Fast API to check if date is in locked period"""
    date_str = request.GET.get('date')
    
    if not date_str:
        return JsonResponse({'is_locked': False})
    
    try:
        from datetime import datetime
        from .models import Ref_Period
        
        doc_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Single fast query
        is_locked = Ref_Period.objects.filter(
            IsLock=True,
            BeginDate__lte=doc_date,
            EndDate__gte=doc_date
        ).exists()
        
        return JsonResponse({
            'is_locked': is_locked,
            'message': 'Тухайн сар түшжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.' if is_locked else ''
        })
        
    except:
        return JsonResponse({'is_locked': False})


@login_required
@permission_required('core.view_cash_document', raise_exception=True)
def api_cashdocument_search(request):
    """API endpoint for server-side search and filtering of cash documents"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method allowed'}, status=405)
    
    try:
        # Get search parameters
        search_term = request.GET.get('search', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        
        # Base query with select_related for performance
        documents_list = Cash_Document.objects.select_related(
            'AccountId', 'ClientId', 'CurrencyId', 'DocumentTypeId', 'TemplateId'
        ).filter(IsDelete=False)
        
        # Apply search filter if provided
        if search_term:
            documents_list = documents_list.filter(
                Q(DocumentNo__icontains=search_term) |
                Q(Description__icontains=search_term) |
                Q(ClientId__ClientName__icontains=search_term) |
                Q(AccountId__AccountName__icontains=search_term)
            )
        
        # Order by document date (newest first)
        documents_list = documents_list.order_by('-DocumentDate')
        
        # Pagination
        paginator = Paginator(documents_list, page_size)
        
        try:
            documents_page = paginator.page(page)
        except PageNotAnInteger:
            documents_page = paginator.page(1)
        except EmptyPage:
            documents_page = paginator.page(paginator.num_pages)
        
        # Serialize documents data
        documents_data = []
        for doc in documents_page:
            documents_data.append({
                'DocumentId': doc.DocumentId,
                'DocumentNo': doc.DocumentNo,
                'DocumentDate': doc.DocumentDate.strftime('%Y-%m-%d'),
                'Description': doc.Description,
                'IsVat': doc.IsVat,
                'CurrencyAmount': float(doc.CurrencyAmount) if doc.CurrencyAmount else 0,
                'CurrencyExchange': float(doc.CurrencyExchange) if doc.CurrencyExchange else 0,
                'CurrencyMNT': float(doc.CurrencyMNT) if doc.CurrencyMNT else 0,
                'CreatedBy': doc.CreatedBy.username if doc.CreatedBy else '',
                'DocumentTypeCode': doc.DocumentTypeId.DocumentTypeCode if doc.DocumentTypeId else '',
                'ClientName': doc.ClientId.ClientName if doc.ClientId else '',
                'AccountCode': doc.AccountId.AccountCode if doc.AccountId else '',
                'AccountName': doc.AccountId.AccountName if doc.AccountId else '',
                'CurrencyName': doc.CurrencyId.Currency_name if doc.CurrencyId else '',
            })
        
        return JsonResponse({
            'success': True,
            'documents': documents_data,
            'pagination': {
                'current_page': documents_page.number,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_previous': documents_page.has_previous(),
                'has_next': documents_page.has_next(),
                'previous_page': documents_page.previous_page_number() if documents_page.has_previous() else None,
                'next_page': documents_page.next_page_number() if documents_page.has_next() else None,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@permission_required('core.add_cash_document', raise_exception=True)
def cashdocument_create(request):
    """Create new cash document"""
    if request.method == 'POST':
        try:
            # Ensure proper encoding for POST data
            import sys
            if sys.platform.startswith('win'):
                # Handle Windows encoding issues
                for key, value in request.POST.items():
                    if isinstance(value, str):
                        # Ensure the value is properly encoded
                        try:
                            value.encode('utf-8')
                        except UnicodeEncodeError:
                            # If encoding fails, skip this field or handle it
                            continue
            
            print(f"POST data: {request.POST}")
            form = CashDocumentForm(request.POST)
            print(f"Form is valid: {form.is_valid()}")
            if not form.is_valid():
                print(f"Form errors: {form.errors}")
            if form.is_valid():
                try:
                    cash_document = form.save(commit=False)
                    
                    # Check period lock (server-side validation)
                    if Ref_Period.objects.filter(IsLock=True, BeginDate__lte=cash_document.DocumentDate, EndDate__gte=cash_document.DocumentDate).exists():
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            # AJAX request - return JSON for modal
                            return JsonResponse({
                                'success': False,
                                'error': 'Тухайн сар түшжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.'
                            })
                        else:
                            # Regular form submission - show Django message
                            messages.error(request, 'Тухайн сар түшжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.')
                            form = CashDocumentForm(request.POST)
                            vat_accounts = {}
                            try:
                                from .models import Ref_Constant, Ref_Account
                                vat_sale = Ref_Constant.objects.filter(ConstantName='VAT_Sale').first()
                                vat_purchase = Ref_Constant.objects.filter(ConstantName='VAT_Purchase').first()
                                if vat_sale:
                                    vat_sale_account = Ref_Account.objects.filter(AccountId=vat_sale.ConstantValue).first()
                                    vat_accounts['vat_sale_code'] = vat_sale_account.AccountCode if vat_sale_account else ''
                                if vat_purchase:
                                    vat_purchase_account = Ref_Account.objects.filter(AccountId=vat_purchase.ConstantValue).first()
                                    vat_accounts['vat_purchase_code'] = vat_purchase_account.AccountCode if vat_purchase_account else ''
                            except:
                                pass
                            return render(request, 'core/cashdocument_form.html', {
                                'form': form,
                                'vat_accounts': vat_accounts,
                                'timestamp': int(time.time())
                            })
                    
                    cash_document.CreatedBy = request.user
                    cash_document.ModifiedBy = request.user
                    
                    # Ensure all text fields are properly encoded
                    if hasattr(cash_document, 'Description') and cash_document.Description:
                        cash_document.Description = cash_document.Description.encode('utf-8').decode('utf-8')
                    
                    cash_document.save()
                    
                    # Save DocumentNo to Ref_Document_Counter table
                    Ref_Document_Counter.objects.create(
                        DocumentNo=cash_document.DocumentNo,
                        DocumentTypeId=cash_document.DocumentTypeId,
                        CreatedBy=request.user
                    )
                    
                    messages.success(request, 'Cash document created successfully.')
                    
                    # Check if AJAX request and return JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'redirect_url': f'/core/cashdocuments/?selected_document={cash_document.DocumentId}'
                        })
                    
                    return redirect(f'/core/cashdocuments/?selected_document={cash_document.DocumentId}')
                except UnicodeEncodeError as e:
                    messages.error(request, f'Unicode encoding error: {str(e)}. Please check your input for special characters.')
                except Exception as e:
                    messages.error(request, f'Error creating cash document: {str(e)}')
            else:
                # Handle form validation errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        except Exception as e:
            messages.error(request, f'Unexpected error: {str(e)}')
    else:
        form = CashDocumentForm()
    
    # Get VAT account IDs from ref_constant table and fetch actual account codes
    vat_accounts = {}
    try:
        from .models import Ref_Constant, Ref_Account
        vat_constant_9 = Ref_Constant.objects.get(ConstantID=9)
        vat_constant_10 = Ref_Constant.objects.get(ConstantID=10)
        
        # Get actual account codes for VAT accounts
        vat_account_8 = Ref_Account.objects.get(AccountId=8)
        vat_account_9 = Ref_Account.objects.get(AccountId=9)
        
        vat_accounts = {
            'vat_account_1_id': 8,  # ConstantID=9 maps to VatAccountId=8
            'vat_account_2_id': 9,  # ConstantID=10 maps to VatAccountId=9
            'vat_account_1_display': vat_account_8.AccountCode,
            'vat_account_2_display': vat_account_9.AccountCode,
        }
    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
        # Fallback values
        vat_accounts = {
            'vat_account_1_id': 8,  # ConstantID=9 maps to VatAccountId=8
            'vat_account_2_id': 9,  # ConstantID=10 maps to VatAccountId=9
            'vat_account_1_display': '3403-01',
            'vat_account_2_display': '3403-02',
        }
    
    return render(request, 'core/cashdocument_form.html', {
        'form': form,
        'item': None,
        'vat_accounts': vat_accounts,
        'timestamp': int(time.time())
    })


@login_required
@permission_required('core.change_cash_document', raise_exception=True)
def cashdocument_update(request, pk):
    """Update existing cash document"""
    document = get_object_or_404(Cash_Document, pk=pk)
    
    # Check if user owns this document
    if document.CreatedBy != request.user:
        messages.error(request, 'You do not have permission to edit this document.')
        return redirect('core:cashdocument_master_detail')
    
    if request.method == 'POST':
        form = CashDocumentForm(request.POST, instance=document)
        if form.is_valid():
            cash_document = form.save(commit=False)
            
            # Check period lock (server-side validation)
            if Ref_Period.objects.filter(IsLock=True, BeginDate__lte=cash_document.DocumentDate, EndDate__gte=cash_document.DocumentDate).exists():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    # AJAX request - return JSON for modal
                    return JsonResponse({
                        'success': False,
                        'error': 'Тухайн сар түшжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.'
                    })
                else:
                    # Regular form submission - show Django message
                    messages.error(request, 'Тухайн сар түшжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.')
                    form = CashDocumentForm(request.POST, instance=document)
                    vat_accounts = {}
                    try:
                        from .models import Ref_Constant, Ref_Account
                        vat_sale = Ref_Constant.objects.filter(ConstantName='VAT_Sale').first()
                        vat_purchase = Ref_Constant.objects.filter(ConstantName='VAT_Purchase').first()
                        if vat_sale:
                            vat_sale_account = Ref_Account.objects.filter(AccountId=vat_sale.ConstantValue).first()
                            vat_accounts['vat_sale_code'] = vat_sale_account.AccountCode if vat_sale_account else ''
                        if vat_purchase:
                            vat_purchase_account = Ref_Account.objects.filter(AccountId=vat_purchase.ConstantValue).first()
                            vat_accounts['vat_purchase_code'] = vat_purchase_account.AccountCode if vat_purchase_account else ''
                    except:
                        pass
                    return render(request, 'core/cashdocument_form.html', {
                        'form': form,
                        'item': document,
                        'vat_accounts': vat_accounts,
                        'timestamp': int(time.time())
                    })
            
            cash_document.ModifiedBy = request.user
            cash_document.save()
            messages.success(request, 'Cash document updated successfully.')
            
            # Check if AJAX request and return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': f'/core/cashdocuments/?selected_document={pk}'
                })
            
            # Preserve the selected document when redirecting
            return redirect(f'/core/cashdocuments/?selected_document={pk}')
        else:
            # Debug: Print form errors
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        # Check if document date is in locked period BEFORE showing form
        if Ref_Period.objects.filter(
            IsLock=True, 
            BeginDate__lte=document.DocumentDate, 
            EndDate__gte=document.DocumentDate
        ).exists():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX request - return JSON for modal
                return JsonResponse({
                    'success': False,
                    'error': 'Тухайн сар түшжигдсэн байна. Засварлах боломжгүй. Админы зөвшөөрлөөр эрх нээгдэнэ.',
                    'redirect': True
                })
            else:
                # Regular request - show Django message and redirect
                messages.error(request, 'Тухайн сар түшжигдсэн байна. Засварлах боломжгүй. Админы зөвшөөрлөөр эрх нээгдэнэ.')
                return redirect(f'/core/cashdocuments/?selected_document={pk}')
        
        form = CashDocumentForm(instance=document)
    
    # Get VAT account IDs from ref_constant table and fetch actual account codes
    vat_accounts = {}
    try:
        from .models import Ref_Constant, Ref_Account
        vat_constant_9 = Ref_Constant.objects.get(ConstantID=9)
        vat_constant_10 = Ref_Constant.objects.get(ConstantID=10)
        
        # Get actual account codes for VAT accounts
        vat_account_8 = Ref_Account.objects.get(AccountId=8)
        vat_account_9 = Ref_Account.objects.get(AccountId=9)
        
        vat_accounts = {
            'vat_account_1_id': 8,  # ConstantID=9 maps to VatAccountId=8
            'vat_account_2_id': 9,  # ConstantID=10 maps to VatAccountId=9
            'vat_account_1_display': vat_account_8.AccountCode,
            'vat_account_2_display': vat_account_9.AccountCode,
        }
    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
        # Fallback values
        vat_accounts = {
            'vat_account_1_id': 8,  # ConstantID=9 maps to VatAccountId=8
            'vat_account_2_id': 9,  # ConstantID=10 maps to VatAccountId=9
            'vat_account_1_display': '3403-01',
            'vat_account_2_display': '3403-02',
        }
    
    return render(request, 'core/cashdocument_form.html', {
        'form': form,
        'item': document,
        'vat_accounts': vat_accounts,
        'timestamp': int(time.time())
    })


@login_required
@permission_required('core.delete_cash_document', raise_exception=True)
def cashdocument_delete(request, pk):
    """Delete cash document with soft delete"""
    document = get_object_or_404(Cash_Document, pk=pk)
    
    # Check if user owns this document
    if document.CreatedBy != request.user:
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to delete this document.'
            })
        messages.error(request, 'You do not have permission to delete this document.')
        return redirect('core:cashdocument_master_detail')
    
    # Check if this is a modal request
    if request.GET.get('modal'):
        # Return modal content
        return render(request, 'core/components/delete_modal.html', {
            'item_name': f"{document.DocumentNo} - {document.Description}",
            'delete_url': reverse('core:cashdocument_delete', args=[pk])
        })
    
    # Handle API request (JSON)
    if request.method == 'POST' and ('application/json' in request.headers.get('Content-Type', '') or request.headers.get('Content-Type') == 'application/json'):
        try:
            import json
            data = json.loads(request.body)
            
            # Check if already deleted
            if document.IsDelete:
                return JsonResponse({
                    'success': False,
                    'message': f'Cash document "{document.DocumentNo}" is already deleted.'
                })
            
            # Perform soft delete
            document.IsDelete = True
            if hasattr(document, 'ModifiedBy'):
                document.ModifiedBy = request.user
            document.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Cash document "{document.DocumentNo}" has been deleted successfully.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting cash document: {str(e)}'
            })
    
    # Handle regular form POST
    if request.method == 'POST':
        try:
            # Check if already deleted
            if document.IsDelete:
                messages.warning(request, f'Cash document "{document.DocumentNo}" is already deleted.')
                return redirect('core:cashdocument_master_detail')
            
            # Perform soft delete
            document.IsDelete = True
            if hasattr(document, 'ModifiedBy'):
                document.ModifiedBy = request.user
            document.save()
            messages.success(request, f'Cash document "{document.DocumentNo}" has been deleted successfully.')
            
        except Exception as e:
            messages.error(request, f'Error deleting cash document: {str(e)}')
        
        return redirect('core:cashdocument_master_detail')
    
    # GET request without modal parameter - redirect to list
    return redirect('core:cashdocument_master_detail')


@login_required
@permission_required('core.view_cash_documentdetail', raise_exception=True)
def cashdocumentdetail_list(request):
    """List all cash document details with pagination and inline filtering"""
    details_list = Cash_DocumentDetail.objects.select_related('DocumentId', 'AccountId', 'ClientId', 'CurrencyId').all()
    
    # Apply filters
    document_filter = request.GET.get('document', '')
    account_filter = request.GET.get('account', '')
    client_filter = request.GET.get('client', '')
    currency_filter = request.GET.get('currency', '')
    debit_filter = request.GET.get('debit', '')
    
    if document_filter:
        details_list = details_list.filter(DocumentId__DocumentNo__icontains=document_filter)
    
    if account_filter:
        details_list = details_list.filter(AccountId__AccountName__icontains=account_filter)
    
    if client_filter:
        details_list = details_list.filter(ClientId__ClientName__icontains=client_filter)
    
    if currency_filter:
        details_list = details_list.filter(CurrencyId__Currency_name__icontains=currency_filter)
    
    if debit_filter:
        if debit_filter == 'debit':
            details_list = details_list.filter(IsDebit=True)
        elif debit_filter == 'credit':
            details_list = details_list.filter(IsDebit=False)
    
    # Order by document and account
    details_list = details_list.order_by('DocumentId', 'AccountId')
    
    # Pagination
    paginator = Paginator(details_list, 20)  # Show 20 items per page
    page = request.GET.get('page')
    
    try:
        details = paginator.page(page)
    except PageNotAnInteger:
        details = paginator.page(1)
    except EmptyPage:
        details = paginator.page(paginator.num_pages)
    
    return render(request, 'core/cashdocumentdetail_list.html', {
        'details': details,
        'paginator': paginator,
        'filters': {
            'document': document_filter,
            'account': account_filter,
            'client': client_filter,
            'currency': currency_filter,
            'debit': debit_filter,
        }
    })



@login_required
@permission_required('core.delete_cash_documentdetail', raise_exception=True)
def cashdocumentdetail_delete(request, pk):
    """Delete cash document detail"""
    detail = get_object_or_404(Cash_DocumentDetail, pk=pk)
    
    # Check if this is a modal request
    if request.GET.get('modal'):
        # Return modal content
        return render(request, 'core/components/delete_modal.html', {
            'item_name': f"{detail.DocumentId.DocumentNo} - {detail.AccountId.AccountName}",
            'delete_url': reverse('core:cashdocumentdetail_delete', args=[pk])
        })
    
    # Handle actual delete
    if request.method == 'POST':
        try:
            detail.delete()
            messages.success(request, 'Cash document detail deleted successfully.')
        except ProtectedError as e:
            messages.error(request, f'Cannot delete cash document detail because it is referenced by other records. Please remove all references first.')
        return redirect('core:cashdocument_master_detail')
    
    # GET request without modal parameter - redirect to list
    return redirect('core:cashdocument_master_detail')





@login_required
@permission_required('core.add_cash_documentdetail', raise_exception=True)
def bulk_manage_details(request, document_id):
    """Unified view for managing cash document details - add, update, and delete"""
    document = get_object_or_404(Cash_Document, pk=document_id)
    
    # Get existing details
    document_details = Cash_DocumentDetail.objects.filter(DocumentId=document).select_related(
        'AccountId', 'ClientId', 'CurrencyId', 'CashFlowId', 'ContractId'
    ).order_by('DocumentDetailId')
    
    # Check if document has existing details
    has_existing_details = document_details.exists()
    
    # If no existing details, create a pre-populated detail record from master document
    if not has_existing_details:
        # Create a temporary detail object with data from master document
        temp_detail = Cash_DocumentDetail()
        temp_detail.DocumentId = document
        temp_detail.AccountId = document.AccountId
        temp_detail.ClientId = document.ClientId
        temp_detail.CurrencyId = document.CurrencyId
        temp_detail.CurrencyAmount = document.CurrencyAmount
        temp_detail.CurrencyExchange = document.CurrencyExchange
        temp_detail.IsDebit = True  # Default to debit
        temp_detail.DebitAmount = document.CurrencyMNT if document.CurrencyMNT else 0
        temp_detail.CreditAmount = 0
        temp_detail.Description = document.Description
        
        # Add the temporary detail to the list for template rendering
        document_details = [temp_detail]
        
        # If IsVat is True, add a VAT detail row
        if document.IsVat and document.VatAccountId:
            # Get VAT percentage from ref_constant table (ConstantId = 2)
            try:
                from core.models import Ref_Constant
                from decimal import Decimal
                vat_constant = Ref_Constant.objects.get(ConstantID=2)
                # Convert to Decimal(10,4) format
                vat_percentage = Decimal(vat_constant.ConstantName).quantize(Decimal('0.0001'))
            except (Ref_Constant.DoesNotExist, ValueError):
                vat_percentage = Decimal('10.0000')  # Default fallback in Decimal(10,4) format
            
            mnt_amount = document.CurrencyMNT if document.CurrencyMNT else 0
            
            if mnt_amount > 0:
                # Calculate VAT amount: VAT = MNT - (MNT / (1 + VAT% / 100))
                vat_amount = mnt_amount - (mnt_amount / (Decimal('1') + vat_percentage / Decimal('100')))
                
                # Create VAT detail row
                vat_detail = Cash_DocumentDetail()
                vat_detail.DocumentId = document
                vat_detail.AccountId = document.VatAccountId
                vat_detail.ClientId = document.ClientId
                vat_detail.CurrencyId = document.CurrencyId
                vat_detail.CurrencyAmount = vat_amount / document.CurrencyExchange if document.CurrencyExchange else 0
                vat_detail.CurrencyExchange = document.CurrencyExchange
                vat_detail.IsDebit = False  # VAT is typically credit
                vat_detail.DebitAmount = 0
                vat_detail.CreditAmount = vat_amount
                vat_detail.Description = f"VAT ({vat_percentage}%)"
                
                # Add VAT detail to the list
                document_details.append(vat_detail)
    
    if request.method == 'POST':
        print("=== POST REQUEST RECEIVED IN BULK MANAGE ===")
        print(f"Request method: {request.method}")
        print(f"Request path: {request.path}")
        print(f"Request POST keys count: {len(request.POST.keys())}")
        try:
            # Debug: Print all POST data
            print("=== CASH DOCUMENT BULK MANAGE POST DATA ===")
            for key, value in request.POST.items():
                if 'currency_exchange' in key or 'currency_amount' in key:
                    print(f"{key}: {value}")
            print("=== END POST DATA ===")
            
            # Debug: Print document exchange rate
            print(f"=== DOCUMENT EXCHANGE RATE DEBUG ===")
            print(f"Document ID: {document.DocumentId}")
            print(f"Document Exchange Rate: {document.CurrencyExchange}")
            print(f"Document Exchange Rate Type: {type(document.CurrencyExchange)}")
            print("=== END DOCUMENT DEBUG ===")
            
            created_count = 0
            deleted_count = 0
            
            # STEP 1: Delete ALL existing details for this document first
            existing_details = Cash_DocumentDetail.objects.filter(DocumentId=document)
            deleted_count = existing_details.count()
            print(f"=== DELETING ALL EXISTING DETAILS ===")
            print(f"Deleting {deleted_count} existing detail records for document {document.DocumentId}")
            existing_details.delete()
            print(f"Successfully deleted {deleted_count} existing detail records")
            print("=== END DELETE OPERATION ===")
            
            # STEP 2: Create new detail records from form data
            print(f"=== CREATING NEW DETAIL RECORDS ===")
            
            # Process existing rows (those with actual detail IDs from the form)
            detail_ids_processed = set()
            
            # First, process existing rows that have detail IDs
            for key, value in request.POST.items():
                if key.startswith('account_id_') and value and not key.endswith('_None'):
                    detail_id = key.replace('account_id_', '')
                    if detail_id.startswith('new_'):
                        continue  # Skip new rows for now
                    
                    detail_ids_processed.add(detail_id)
                    
                    # Get form data for this detail
                    account_id = request.POST.get(f'account_id_{detail_id}')
                    client_id = request.POST.get(f'client_id_{detail_id}')
                    currency_id = request.POST.get(f'currency_id_{detail_id}')
                    currency_exchange = request.POST.get(f'currency_exchange_{detail_id}')
                    currency_amount = request.POST.get(f'currency_amount_{detail_id}')
                    is_debit = request.POST.get(f'is_debit_{detail_id}')
                    cashflow_id = request.POST.get(f'cashflow_id_{detail_id}')
                    contract_id = request.POST.get(f'contract_id_{detail_id}')
                    
                    # Skip if required fields are empty
                    if not account_id or not client_id or not currency_id or not currency_amount or not currency_exchange or not is_debit:
                        print(f"Skipping detail {detail_id} - missing required fields")
                        continue
                    
                    # Create new detail object
                    detail = Cash_DocumentDetail()
                    detail.DocumentId = document
                    detail.AccountId = Ref_Account.objects.get(AccountId=account_id)
                    detail.ClientId = RefClient.objects.get(ClientId=client_id)
                    detail.CurrencyId = Ref_Currency.objects.get(CurrencyId=currency_id)
                    
                    # Use the exchange rate from the form (user input)
                    print(f"=== EXCHANGE RATE PROCESSING DEBUG ===")
                    print(f"Detail ID: {detail_id}")
                    print(f"Form currency_exchange value: '{currency_exchange}'")
                    print(f"Form currency_exchange as float: {float(currency_exchange)}")
                    print(f"Document exchange rate: {document.CurrencyExchange}")
                    
                    # Always use the form value - don't override with document rate
                    detail.CurrencyExchange = float(currency_exchange)
                    print(f"USING: Form exchange rate: {float(currency_exchange)}")
                    print(f"Final detail.CurrencyExchange: {detail.CurrencyExchange}")
                    print("=== END EXCHANGE RATE DEBUG ===")
                    
                    detail.CurrencyAmount = float(currency_amount)
                    detail.IsDebit = is_debit == 'true'
                    
                    # Update CashFlowId and ContractId using ForeignKey assignment
                    if cashflow_id:
                        detail.CashFlowId_id = int(cashflow_id)
                    else:
                        detail.CashFlowId = None
                        
                    if contract_id:
                        detail.ContractId_id = int(contract_id)
                    else:
                        detail.ContractId = None
                    
                    # Amount calculations are now done in frontend - store raw values
                    # DebitAmount and CreditAmount are kept for historical data but not calculated here
                    detail.DebitAmount = 0.0
                    detail.CreditAmount = 0.0
                    
                    print(f"=== SAVING NEW DETAIL (from existing row) ===")
                    print(f"Detail before save - CurrencyExchange: {detail.CurrencyExchange}")
                    print(f"Detail before save - CurrencyAmount: {detail.CurrencyAmount}")
                    print(f"Detail before save - DebitAmount: {detail.DebitAmount}")
                    print(f"Detail before save - CreditAmount: {detail.CreditAmount}")
                    
                    detail.save()
                    print(f"Detail saved successfully with new ID: {detail.DocumentDetailId}")
                    created_count += 1
            
            # Handle prepopulated data (when DocumentDetailId is None)
            # This happens when no existing details exist and data is prepopulated from master document
            # Since multiple prepopulated rows can have the same field names, we need to handle them differently
            
            # Check if we have prepopulated data by looking for account_id_None
            if request.POST.get('account_id_None'):
                # For prepopulated data, we need to recreate the same logic that was used to create the prepopulated rows
                # This ensures we save all the rows that were displayed
                
                # First, create the main detail record (from master document)
                if document.AccountId and document.ClientId and document.CurrencyId and document.CurrencyAmount:
                    detail = Cash_DocumentDetail()
                    detail.DocumentId = document
                    detail.AccountId = document.AccountId
                    detail.ClientId = document.ClientId
                    detail.CurrencyId = document.CurrencyId
                    detail.CurrencyExchange = document.CurrencyExchange
                    detail.CurrencyAmount = document.CurrencyAmount
                    detail.IsDebit = True  # Main entry is typically debit
                    
                    # Amount calculations are now done in frontend - store raw values
                    detail.DebitAmount = 0.0
                    detail.CreditAmount = 0.0
                    
                    detail.save()
                    created_count += 1
                
                # Second, create VAT detail record if IsVat is True
                if document.IsVat and document.VatAccountId:
                    try:
                        from core.models import Ref_Constant
                        from decimal import Decimal
                        vat_constant = Ref_Constant.objects.get(ConstantID=2)
                        vat_percentage = Decimal(vat_constant.ConstantName).quantize(Decimal('0.0001'))
                    except (Ref_Constant.DoesNotExist, ValueError):
                        vat_percentage = Decimal('10.0000')  # Default fallback
                    
                    mnt_amount = document.CurrencyMNT if document.CurrencyMNT else 0
                    
                    if mnt_amount > 0:
                        # Calculate VAT amount: VAT = MNT - (MNT / (1 + VAT% / 100))
                        vat_amount = mnt_amount - (mnt_amount / (Decimal('1') + vat_percentage / Decimal('100')))
                        
                        # Create VAT detail row
                        vat_detail = Cash_DocumentDetail()
                        vat_detail.DocumentId = document
                        vat_detail.AccountId = document.VatAccountId
                        vat_detail.ClientId = document.ClientId
                        vat_detail.CurrencyId = document.CurrencyId
                        vat_detail.CurrencyAmount = vat_amount / document.CurrencyExchange if document.CurrencyExchange else 0
                        vat_detail.CurrencyExchange = document.CurrencyExchange
                        vat_detail.IsDebit = False  # VAT is typically credit
                        vat_detail.DebitAmount = 0
                        vat_detail.CreditAmount = vat_amount
                        
                        vat_detail.save()
                        created_count += 1
            
            # Handle new rows (create)
            # STEP 3: Process new rows (created by user clicking "Add New Row")
            new_row_count = int(request.POST.get('new_row_count', 0))
            print(f"Processing {new_row_count} new rows")
            
            for i in range(new_row_count):
                # Get form data for each new row
                account_id = request.POST.get(f'new_account_id_{i}')
                client_id = request.POST.get(f'new_client_id_{i}')
                currency_id = request.POST.get(f'new_currency_id_{i}')
                currency_exchange = request.POST.get(f'new_currency_exchange_{i}')
                currency_amount = request.POST.get(f'new_currency_amount_{i}')
                is_debit = request.POST.get(f'new_is_debit_{i}')
                cashflow_id = request.POST.get(f'new_cashflow_id_{i}')
                contract_id = request.POST.get(f'new_contract_id_{i}')
                
                # Skip empty rows
                if not account_id or not client_id or not currency_id or not currency_amount or not currency_exchange or not is_debit:
                    print(f"Skipping new row {i} - missing required fields")
                    continue
                
                # Create detail object
                detail = Cash_DocumentDetail()
                detail.DocumentId = document
                detail.AccountId = Ref_Account.objects.get(AccountId=account_id)
                detail.ClientId = RefClient.objects.get(ClientId=client_id)
                detail.CurrencyId = Ref_Currency.objects.get(CurrencyId=currency_id)
                
                # Use the exchange rate from the form (user input)
                detail.CurrencyExchange = float(currency_exchange)
                print(f"New detail using form exchange rate: {float(currency_exchange)}")
                
                detail.CurrencyAmount = float(currency_amount)
                detail.IsDebit = is_debit == 'true'
                
                # Handle CashFlowId and ContractId using ForeignKey assignment
                if cashflow_id:
                    detail.CashFlowId_id = int(cashflow_id)
                else:
                    detail.CashFlowId = None
                    
                if contract_id:
                    detail.ContractId_id = int(contract_id)
                else:
                    detail.ContractId = None
                
                # Amount calculations are now done in frontend - store raw values
                detail.DebitAmount = 0.0
                detail.CreditAmount = 0.0
                
                print(f"=== SAVING NEW DETAIL (from new row) ===")
                print(f"New detail before save - CurrencyExchange: {detail.CurrencyExchange}")
                print(f"New detail before save - CurrencyAmount: {detail.CurrencyAmount}")
                print(f"New detail before save - DebitAmount: {detail.DebitAmount}")
                print(f"New detail before save - CreditAmount: {detail.CreditAmount}")
                
                detail.save()
                print(f"New detail saved successfully with ID: {detail.DocumentDetailId}")
                created_count += 1
            
            # Prepare success message
            message_parts = []
            if deleted_count > 0:
                message_parts.append(f'deleted {deleted_count}')
            if created_count > 0:
                message_parts.append(f'created {created_count}')
            
            if message_parts:
                message = f'Successfully {" and ".join(message_parts)} detail records.'
            else:
                message = 'No changes were made.'
            
            print(f"=== SAVE OPERATION COMPLETE ===")
            print(f"Created: {created_count}, Deleted: {deleted_count}")
            print(f"Success message: {message}")
            
            messages.success(request, message)
            return redirect(f'/core/cashdocuments/?selected_document={document_id}')
            
        except Exception as e:
            messages.error(request, f'Error managing details: {str(e)}')
            return redirect(request.path)
    
    # GET request - render the template
    accounts = Ref_Account.objects.filter(IsDelete=False).order_by('AccountCode')
    clients = RefClient.objects.filter(IsDelete=False).order_by('ClientCode')
    currencies = Ref_Currency.objects.filter(IsActive=True).order_by('CurrencyId')
    account_types = Ref_Account_Type.objects.filter(IsActive=True).order_by('AccountTypeName')
    cash_flows = Ref_CashFlow.objects.filter(IsActive=True).order_by('CashFlowId')
    contracts = Ref_Contract.objects.filter(IsActive=True).order_by('ContractId')
    
    # Get template details if TemplateId exists
    template_details = []
    if document.TemplateId:
            template_details = Ref_Template_Detail.objects.select_related('AccountId', 'CashFlowId').filter(
                TemplateId=document.TemplateId
            ).order_by('TemplateDetailId')
    
    # Calculate VatAmount and VatPercent for the template
    vat_amount = 0
    vat_percent = 0
    if document.IsVat:
        try:
            from core.models import Ref_Constant
            from decimal import Decimal
            vat_constant = Ref_Constant.objects.get(ConstantID=2)
            vat_percent = float(vat_constant.ConstantName)
            
            # Calculate VatAmount using the same formula as the form
            # VAT = MNT Amount * (VAT Rate / (100 + VAT Rate))
            total_amount = float(document.CurrencyAmount * document.CurrencyExchange)
            vat_amount = (total_amount * vat_percent) / (100 + vat_percent)
            
        except (Ref_Constant.DoesNotExist, ValueError, AttributeError):
            vat_percent = 10.0  # Default fallback
            vat_amount = 0
    
    return render(request, 'core/cashdocumentdetail_bulk_manage.html', {
        'document': document,
        'document_details': document_details,
        'has_existing_details': has_existing_details,
        'accounts': accounts,
        'clients': clients,
        'currencies': currencies,
        'account_types': account_types,
        'cash_flows': cash_flows,
        'contracts': contracts,
        'template_details': template_details,
        'vat_amount': vat_amount,
        'vat_percent': vat_percent,
        'timestamp': int(time.time()),
    })


@login_required
@permission_required('core.add_cash_documentdetail', raise_exception=True)
@require_http_methods(["POST"])
def api_bulk_manage_details(request, document_id):
    """API endpoint for bulk managing cash document details"""
    try:
        document = get_object_or_404(Cash_Document, pk=document_id)
        
        print("=== API BULK MANAGE DETAILS ===")
        print(f"Document ID: {document_id}")
        print(f"Request method: {request.method}")
        print(f"Content type: {request.content_type}")
        
        # Parse JSON data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            # Handle form data
            data = request.POST.dict()
        
        print(f"Data keys: {list(data.keys())}")
        
        # Check if using new inventory-style approach
        if 'details' in data:
            print("=== USING INVENTORY-STYLE APPROACH ===")
            details = data.get('details', [])
            print(f"Received {len(details)} detail records")
            
            updated_count = 0
            created_count = 0
            deleted_count = 0
            
            # Process all details as new records (delete all and insert approach)
            try:
                # Delete existing details for this document
                existing_details = Cash_DocumentDetail.objects.filter(DocumentId=document)
                deleted_count = existing_details.count()
                existing_details.delete()
                print(f"Deleted {deleted_count} existing details")
                
                # Create new details
                new_details_to_create = []
                for i, detail_data in enumerate(details):
                    print(f"Processing detail {i}: {detail_data}")
                    
                    try:
                        detail = Cash_DocumentDetail()
                        detail.DocumentId = document
                        detail.AccountId_id = detail_data.get('account_id')
                        detail.ClientId_id = detail_data.get('client_id')
                        detail.CurrencyId_id = detail_data.get('currency_id')
                        detail.CurrencyExchange = float(detail_data.get('currency_exchange', 1.0))
                        detail.CurrencyAmount = float(detail_data.get('currency_amount', 0))
                        detail.IsDebit = detail_data.get('is_debit') == 'true'
                        
                        # Handle CashFlowId and ContractId
                        cashflow_id = detail_data.get('cashflow_id')
                        contract_id = detail_data.get('contract_id')
                        
                        if cashflow_id:
                            detail.CashFlowId_id = int(cashflow_id)
                        else:
                            detail.CashFlowId = None
                            
                        if contract_id:
                            detail.ContractId_id = int(contract_id)
                        else:
                            detail.ContractId = None
                        
                        # Calculate DebitAmount and CreditAmount based on IsDebit and CurrencyAmount
                        calculated_amount = detail.CurrencyAmount * detail.CurrencyExchange
                        if detail.IsDebit:
                            detail.DebitAmount = calculated_amount
                            detail.CreditAmount = 0.0
                        else:
                            detail.DebitAmount = 0.0
                            detail.CreditAmount = calculated_amount
                        
                        new_details_to_create.append(detail)
                        
                    except Exception as e:
                        print(f"Error preparing detail {i}: {str(e)}")
                        return JsonResponse({
                            'success': False,
                            'error': f'Error preparing detail {i}: {str(e)}',
                            'message': f'Error managing details: {str(e)}'
                        })
                
                # Bulk create all new details
                if new_details_to_create:
                    Cash_DocumentDetail.objects.bulk_create(new_details_to_create)
                    created_count = len(new_details_to_create)
                    print(f"Successfully created {created_count} new details")
                
                # Prepare response
                message = f'Successfully deleted {deleted_count} and created {created_count} detail records.'
                
                print(f"=== API SAVE OPERATION COMPLETE ===")
                print(f"Deleted: {deleted_count}, Created: {created_count}")
                
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'deleted_count': deleted_count,
                    'created_count': created_count
                })
                
            except Exception as e:
                print(f"Error in inventory-style processing: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'error': f'Error processing details: {str(e)}',
                    'message': f'Error managing details: {str(e)}'
                })
        
        # If no 'details' key found, return error
        return JsonResponse({
            'success': False,
            'error': 'Invalid data format. Expected "details" array.',
            'message': 'Error managing details: Invalid data format'
        })
        
    except Exception as e:
        print(f"=== API ERROR ===")
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e)}")
        
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': f'Error managing details: {str(e)}'
        }, status=500)


# ==================== INVENTORY DOCUMENT VIEWS ====================

@login_required
@permission_required('core.view_inv_document', raise_exception=True)
def invdocument_master_detail(request):
    """Master-detail view for inventory documents
    
    Master table data is loaded via API endpoint (get_inventory_documents_master).
    This view handles the initial page load and AJAX requests for detail grids.
    """
    
    # Get selected document ID for detail grids (AJAX request)
    selected_document_id = request.GET.get('selected_document')
    selected_document = None
    document_items = []
    document_details = []
    
    if selected_document_id:
        try:
            selected_document = Inv_Document.objects.select_related(
                'DocumentTypeId', 'ClientId', 'AccountId', 'WarehouseId'
            ).filter(IsDelete=False).get(DocumentId=selected_document_id)
            
            document_items = Inv_Document_Item.objects.select_related('InventoryId').filter(
                DocumentId=selected_document
            ).order_by('DocumentItemId')
            
            # Get document details (accounting details)
            document_details = Inv_Document_Detail.objects.select_related(
                'AccountId', 'ClientId', 'CurrencyId'
            ).filter(DocumentId=selected_document).order_by('DocumentDetailId')
            
        except Inv_Document.DoesNotExist:
            selected_document = None
    
    context = {
        'selected_document': selected_document,
        'selected_document_id': selected_document_id,
        'document_items': document_items,
        'document_details': document_details,
    }
    
    # Check if this is an AJAX request for detail grids only
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('ajax') == '1':
        # Return only the detail grids HTML
        return render(request, 'core/components/inv_document_detail_grid.html', context)
    
    return render(request, 'core/invdocument_master_detail.html', context)


@login_required
@permission_required('core.add_inv_document', raise_exception=True)
def invdocument_create(request, parentid=None):
    """Create a new inventory document"""
    if request.method == 'POST':
        form = InvDocumentForm(request.POST, parentid=parentid)
        if form.is_valid():
            document = form.save(commit=False)
            document.CreatedBy = request.user
            
            # Check period lock (server-side validation)
            if Ref_Period.objects.filter(IsLock=True, BeginDate__lte=document.DocumentDate, EndDate__gte=document.DocumentDate).exists():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Тухайн сар түшжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.'
                    })
                else:
                    messages.error(request, 'Тухайн сар түшжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.')
                    # Get required context data for re-rendering
                    inventory_account_types = Ref_Account_Type.objects.filter(
                        AccountTypeId__in=[8, 9, 10, 11], 
                        IsActive=True
                    ).order_by('AccountTypeId')
                    
                    vat_accounts = {}
                    try:
                        from .models import Ref_Constant, Ref_Account
                        vat_account_8 = Ref_Account.objects.get(AccountId=8)
                        vat_account_9 = Ref_Account.objects.get(AccountId=9)
                        vat_accounts = {
                            'vat_account_1_id': 8,
                            'vat_account_2_id': 9,
                            'vat_account_1_display': vat_account_8.AccountCode,
                            'vat_account_2_display': vat_account_9.AccountCode,
                        }
                    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
                        vat_accounts = {
                            'vat_account_1_id': 8,
                            'vat_account_2_id': 9,
                            'vat_account_1_display': '3403-01',
                            'vat_account_2_display': '3403-02',
                        }
                    
                    return render(request, 'core/invdocument_form.html', {
                        'form': form,
                        'item': None,
                        'parentid': parentid,
                        'inventory_account_types': inventory_account_types,
                        'vat_accounts': vat_accounts,
                        'timestamp': int(time.time())
                    })
            
            document.save()
            
            # Save DocumentNo to Ref_Document_Counter table
            Ref_Document_Counter.objects.create(
                DocumentNo=document.DocumentNo,
                DocumentTypeId=document.DocumentTypeId,
                CreatedBy=request.user
            )
            
            messages.success(request, 'Inventory document created successfully.')
            
            # Check if AJAX request and return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('core:invdocument_master_detail')
                })
            
            return redirect('core:invdocument_master_detail')
    else:
        form = InvDocumentForm(parentid=parentid)
    
    # Get accounts with AccountTypeId 8, 9, 10, 11 for inventory documents
    inventory_account_types = Ref_Account_Type.objects.filter(
        AccountTypeId__in=[8, 9, 10, 11], 
        IsActive=True
    ).order_by('AccountTypeId')
    
    # Get VAT account IDs from ref_constant table and fetch actual account codes
    vat_accounts = {}
    try:
        from .models import Ref_Constant, Ref_Account
        vat_constant_9 = Ref_Constant.objects.get(ConstantID=9)
        vat_constant_10 = Ref_Constant.objects.get(ConstantID=10)
        
        # Get actual account codes for VAT accounts
        vat_account_8 = Ref_Account.objects.get(AccountId=8)
        vat_account_9 = Ref_Account.objects.get(AccountId=9)
        
        vat_accounts = {
            'vat_account_1_id': 8,  # ConstantID=9 maps to VatAccountId=8
            'vat_account_2_id': 9,  # ConstantID=10 maps to VatAccountId=9
            'vat_account_1_display': vat_account_8.AccountCode,
            'vat_account_2_display': vat_account_9.AccountCode,
        }
    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
        # Fallback values
        vat_accounts = {
            'vat_account_1_id': 8,  # ConstantID=9 maps to VatAccountId=8
            'vat_account_2_id': 9,  # ConstantID=10 maps to VatAccountId=9
            'vat_account_1_display': '3403-01',
            'vat_account_2_display': '3403-02',
        }
    
    return render(request, 'core/invdocument_form.html', {
        'form': form,
        'item': None,
        'parentid': parentid,
        'inventory_account_types': inventory_account_types,
        'vat_accounts': vat_accounts
    })


@login_required
@permission_required('core.change_inv_document', raise_exception=True)
def invdocument_update(request, pk, parentid=None):
    """Update an existing inventory document"""
    document = get_object_or_404(Inv_Document, pk=pk, IsDelete=False)
    
    # Check if user owns this document
    if document.CreatedBy != request.user:
        messages.error(request, 'You do not have permission to edit this document.')
        return redirect('core:invdocument_master_detail')
    
    if request.method == 'POST':
        form = InvDocumentForm(request.POST, instance=document, parentid=parentid)
        if form.is_valid():
            document = form.save(commit=False)
            document.ModifiedBy = request.user
            
            # Check period lock (server-side validation)
            if Ref_Period.objects.filter(IsLock=True, BeginDate__lte=document.DocumentDate, EndDate__gte=document.DocumentDate).exists():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Тухайн сар түшжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.'
                    })
                else:
                    messages.error(request, 'Тухайн сар түшжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.')
                    # Get required context data for re-rendering
                    inventory_account_types = Ref_Account_Type.objects.filter(
                        AccountTypeId__in=[8, 9, 10, 11], 
                        IsActive=True
                    ).order_by('AccountTypeId')
                    
                    vat_accounts = {}
                    try:
                        from .models import Ref_Constant, Ref_Account
                        vat_account_8 = Ref_Account.objects.get(AccountId=8)
                        vat_account_9 = Ref_Account.objects.get(AccountId=9)
                        vat_accounts = {
                            'vat_account_1_id': 8,
                            'vat_account_2_id': 9,
                            'vat_account_1_display': vat_account_8.AccountCode,
                            'vat_account_2_display': vat_account_9.AccountCode,
                        }
                    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
                        vat_accounts = {
                            'vat_account_1_id': 8,
                            'vat_account_2_id': 9,
                            'vat_account_1_display': '3403-01',
                            'vat_account_2_display': '3403-02',
                        }
                    
                    return render(request, 'core/invdocument_form.html', {
                        'form': form,
                        'item': document,
                        'parentid': parentid,
                        'inventory_account_types': inventory_account_types,
                        'vat_accounts': vat_accounts,
                        'timestamp': int(time.time())
                    })
            
            document.save()
            messages.success(request, 'Inventory document updated successfully.')
            
            # Check if AJAX request and return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('core:invdocument_master_detail')
                })
            
            return redirect('core:invdocument_master_detail')
    else:
        # Pre-edit check for GET requests
        if Ref_Period.objects.filter(
            IsLock=True, 
            BeginDate__lte=document.DocumentDate, 
            EndDate__gte=document.DocumentDate
        ).exists():
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Тухайн сар түшжигдсэн байна. Засварлах боломжгүй. Админы зөвшөөрлөөр эрх нээгдэнэ.',
                    'redirect': True
                })
            else:
                messages.error(request, 'Тухайн сар түшжигдсэн байна. Засварлах боломжгүй. Админы зөвшөөрлөөр эрх нээгдэнэ.')
                return redirect(f'/core/invdocuments/?selected_document={pk}')
        
        form = InvDocumentForm(instance=document, parentid=parentid)
    
    # Get accounts with AccountTypeId 8, 9, 10, 11 for inventory documents
    inventory_account_types = Ref_Account_Type.objects.filter(
        AccountTypeId__in=[8, 9, 10, 11], 
        IsActive=True
    ).order_by('AccountTypeId')
    
    # Get VAT account IDs from ref_constant table and fetch actual account codes
    vat_accounts = {}
    try:
        from .models import Ref_Constant, Ref_Account
        vat_constant_9 = Ref_Constant.objects.get(ConstantID=9)
        vat_constant_10 = Ref_Constant.objects.get(ConstantID=10)
        
        # Get actual account codes for VAT accounts
        vat_account_8 = Ref_Account.objects.get(AccountId=8)
        vat_account_9 = Ref_Account.objects.get(AccountId=9)
        
        vat_accounts = {
            'vat_account_1_id': 8,  # ConstantID=9 maps to VatAccountId=8
            'vat_account_2_id': 9,  # ConstantID=10 maps to VatAccountId=9
            'vat_account_1_display': vat_account_8.AccountCode,
            'vat_account_2_display': vat_account_9.AccountCode,
        }
    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
        # Fallback values
        vat_accounts = {
            'vat_account_1_id': 8,  # ConstantID=9 maps to VatAccountId=8
            'vat_account_2_id': 9,  # ConstantID=10 maps to VatAccountId=9
            'vat_account_1_display': '3403-01',
            'vat_account_2_display': '3403-02',
        }
    
    return render(request, 'core/invdocument_form.html', {
        'form': form,
        'item': document,
        'parentid': parentid,
        'inventory_account_types': inventory_account_types,
        'vat_accounts': vat_accounts
    })


@login_required
@permission_required('core.delete_inv_document', raise_exception=True)
def invdocument_delete(request, pk):
    """Delete an inventory document with soft delete"""
    document = get_object_or_404(Inv_Document, pk=pk)
    
    # Check if user owns this document
    if document.CreatedBy != request.user:
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to delete this document.'
            })
        messages.error(request, 'You do not have permission to delete this document.')
        return redirect('core:invdocument_master_detail')
    
    # Check if this is a modal request
    if request.GET.get('modal'):
        # Return modal content
        return render(request, 'core/components/delete_modal.html', {
            'item_name': f"{document.DocumentNo} - {document.Description}",
            'delete_url': reverse('core:invdocument_delete', args=[pk])
        })
    
    # Handle API request (JSON)
    if request.method == 'POST' and ('application/json' in request.headers.get('Content-Type', '') or request.headers.get('Content-Type') == 'application/json'):
        try:
            import json
            data = json.loads(request.body)
            
            # Check if already deleted
            if document.IsDelete:
                return JsonResponse({
                    'success': False,
                    'message': f'Inventory document "{document.DocumentNo}" is already deleted.'
                })
            
            # Perform soft delete
            document.IsDelete = True
            if hasattr(document, 'ModifiedBy'):
                document.ModifiedBy = request.user
            document.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Inventory document "{document.DocumentNo}" has been deleted successfully.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting inventory document: {str(e)}'
            })
    
    # Handle regular form submission
    if request.method == 'POST':
        try:
            document.IsDelete = True
            document.ModifiedBy = request.user
            document.save()
            messages.success(request, f'Inventory document {document.DocumentNo} has been deleted.')
        except ProtectedError as e:
            messages.error(request, f'Cannot delete inventory document {document.DocumentNo} because it is referenced by other records. Please remove all references first.')
        return redirect('core:invdocument_master_detail')
    
    return render(request, 'core/components/delete_modal.html', {
        'object': document,
        'object_name': f'Inventory Document {document.DocumentNo}',
        'delete_url': reverse('core:invdocument_delete', args=[document.pk])
    })




@login_required
@permission_required('core.view_inv_document', raise_exception=True)
def bulk_manage_inv_details_api(request, document_id):
    """API endpoint for bulk managing inventory document items and details"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        document = get_object_or_404(Inv_Document, pk=document_id, IsDelete=False)
        import json
        data = json.loads(request.body)
        
        # Process inventory items (first table)
        
        # Handle existing inventory items (update/delete)
        existing_items = Inv_Document_Item.objects.filter(DocumentId=document)
        
        for item in existing_items:
            item_id = item.DocumentItemId
            
            # Check if this item should be deleted
            if str(item_id) in data.get('deleted_items', []):
                item.delete()
                continue
            
            # Get form data for this item
            item_data = data.get('items', {}).get(str(item_id))
            if item_data:
                # Skip if required fields are empty
                if not item_data.get('inventory_id') or not item_data.get('quantity') or not item_data.get('unit_cost') or not item_data.get('unit_price'):
                    continue
                
                # Update item object
                item.InventoryId = RefInventory.objects.get(InventoryId=item_data['inventory_id'])
                item.Quantity = float(item_data['quantity'])
                item.UnitCost = float(item_data['unit_cost'])
                item.UnitPrice = float(item_data['unit_price'])
                
                item.save()
        
        # Handle new inventory items (create)
        for new_item_data in data.get('new_items', []):
            # Skip if required fields are empty
            if not new_item_data.get('inventory_id') or not new_item_data.get('quantity') or not new_item_data.get('unit_cost') or not new_item_data.get('unit_price'):
                continue
            
            # Create item object
            item = Inv_Document_Item()
            item.DocumentId = document
            item.InventoryId = RefInventory.objects.get(InventoryId=new_item_data['inventory_id'])
            item.Quantity = float(new_item_data['quantity'])
            item.UnitCost = float(new_item_data['unit_cost'])
            item.UnitPrice = float(new_item_data['unit_price'])
            
            item.save()
        
        # Document totals are now calculated in frontend - no backend calculation needed
        # The CostAmount and PriceAmount fields are kept for historical data but not updated here
        
        # Process accounting details (second table)
        
        # Delete all existing detail records
        existing_details = Inv_Document_Detail.objects.filter(DocumentId=document)
        existing_details.delete()
        
        # Create new detail records
        for detail_data in data.get('details', []):
            detail = Inv_Document_Detail()
            detail.DocumentId = document
            detail.AccountId = Ref_Account.objects.get(AccountId=detail_data['account_id'])
            detail.ClientId = RefClient.objects.get(ClientId=detail_data['client_id']) if detail_data.get('client_id') else None
            detail.CurrencyId = Ref_Currency.objects.get(CurrencyId=detail_data['currency_id']) if detail_data.get('currency_id') else None
            
            # Parse values
            currency_exchange = float(detail_data['currency_exchange'])
            currency_amount = float(detail_data['currency_amount'])
            is_debit = detail_data['is_debit'] == 'true'
            debit_amount = float(detail_data.get('debit_amount', 0))
            credit_amount = float(detail_data.get('credit_amount', 0))
            
            detail.CurrencyExchange = currency_exchange
            detail.CurrencyAmount = currency_amount
            detail.IsDebit = is_debit
            detail.DebitAmount = debit_amount
            detail.CreditAmount = credit_amount
            
            detail.save()
        
        return JsonResponse({
            'success': True
        })
        
    except Exception as e:
        print(f"API Error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@permission_required('core.view_inv_document', raise_exception=True)
def bulk_manage_inv_details(request, document_id):
    """Bulk manage inventory document items - GET request only (renders template)"""
    document = get_object_or_404(Inv_Document, pk=document_id, IsDelete=False)
    
    # Get existing document items
    document_items = Inv_Document_Item.objects.select_related('InventoryId').filter(
        DocumentId=document
    ).order_by('DocumentItemId')
    
    # Get existing document details (for the second section)
    document_details = Inv_Document_Detail.objects.select_related(
        'AccountId', 'ClientId', 'CurrencyId'
    ).filter(DocumentId=document).order_by('DocumentDetailId')
    
    # Get filter options
    currencies = Ref_Currency.objects.filter(IsActive=True).order_by('CurrencyId')
    
    # Get template details if TemplateId exists
    template_details = []
    if document.TemplateId:
        template_details = Ref_Template_Detail.objects.select_related('AccountId', 'AccountId__AccountTypeId').filter(
            TemplateId=document.TemplateId
        ).order_by('TemplateDetailId')
    
    return render(request, 'core/invdocumentdetail_bulk_manage.html', {
        'document': document,
        'document_items': document_items,
        'document_details': document_details,
        'currencies': currencies,
        'template_details': template_details,
    })


# ==================== ASSET MANAGEMENT VIEWS ====================

@login_required
@permission_required('core.view_refasset', raise_exception=True)
def asset_master_detail_modal(request):
    """Modal version of asset master detail view"""
    # Get filter parameters
    selected_asset_type_id = request.GET.get('asset_type', '')
    selected_asset_id = request.GET.get('selected_asset', '')
    page = request.GET.get('page', 1)
    
    # Get all asset types for dropdown
    asset_types = Ref_Asset_Type.objects.filter(IsActive=True).order_by('AssetTypeName')
    
    # Get all assets with related data
    assets = RefAsset.objects.select_related('AssetTypeId').order_by('AssetCode')
    
    # Apply asset type filter if provided
    if selected_asset_type_id:
        assets = assets.filter(AssetTypeId__AssetTypeId=selected_asset_type_id)
    
    # Apply additional filters
    asset_code_filter = request.GET.get('asset_code', '')
    asset_name_filter = request.GET.get('asset_name', '')
    status_filter = request.GET.get('status', '')
    
    if asset_code_filter:
        assets = assets.filter(AssetCode__icontains=asset_code_filter)
    
    if asset_name_filter:
        assets = assets.filter(AssetName__icontains=asset_name_filter)
    
    if status_filter:
        if status_filter == 'active':
            assets = assets.filter(IsDelete=False)
        elif status_filter == 'inactive':
            assets = assets.filter(IsDelete=True)
    
    # Pagination
    paginator = Paginator(assets, 20)  # Show 20 assets per page
    try:
        assets = paginator.page(page)
    except PageNotAnInteger:
        assets = paginator.page(1)
    except EmptyPage:
        assets = paginator.page(paginator.num_pages)
    
    # Get selected asset and its cards
    selected_asset = None
    asset_cards = []
    
    if selected_asset_id:
        try:
            selected_asset = RefAsset.objects.select_related('AssetTypeId').get(AssetId=selected_asset_id)
            asset_cards = Ref_Asset_Card.objects.select_related('AssetId', 'EmployeeId').filter(
                AssetId=selected_asset
            ).order_by('AssetCardId')
        except RefAsset.DoesNotExist:
            selected_asset = None
    
    return render(request, 'core/refasset_master_detail_modal.html', {
        'asset_types': asset_types,
        'assets': assets,
        'selected_asset_type_id': selected_asset_type_id,
        'selected_asset': selected_asset,
        'selected_asset_id': selected_asset_id,
        'asset_cards': asset_cards,
        'paginator': paginator,
        'filters': {
            'asset_code': asset_code_filter,
            'asset_name': asset_name_filter,
            'status': status_filter,
        }
    })


@login_required
@permission_required('core.view_refasset', raise_exception=True)
def asset_master_detail(request):
    """Master-detail view for asset management with dropdown filtering"""
    # Get filter parameters
    selected_asset_type_id = request.GET.get('asset_type', '')
    selected_asset_id = request.GET.get('selected_asset', '')
    page = request.GET.get('page', 1)
    
    # Get all asset types for dropdown
    asset_types = Ref_Asset_Type.objects.filter(IsActive=True).order_by('AssetTypeName')
    
    # Get all assets with related data
    assets = RefAsset.objects.select_related('AssetTypeId').order_by('AssetCode')
    
    # Apply asset type filter if provided
    if selected_asset_type_id:
        assets = assets.filter(AssetTypeId__AssetTypeId=selected_asset_type_id)
    
    # Apply additional filters
    asset_code_filter = request.GET.get('asset_code', '')
    asset_name_filter = request.GET.get('asset_name', '')
    status_filter = request.GET.get('status', '')
    
    if asset_code_filter:
        assets = assets.filter(AssetCode__icontains=asset_code_filter)
    
    if asset_name_filter:
        assets = assets.filter(AssetName__icontains=asset_name_filter)
    
    if status_filter:
        if status_filter == 'active':
            assets = assets.filter(IsDelete=False)
        elif status_filter == 'inactive':
            assets = assets.filter(IsDelete=True)
    
    # Pagination
    paginator = Paginator(assets, 20)  # Show 20 assets per page
    try:
        assets = paginator.page(page)
    except PageNotAnInteger:
        assets = paginator.page(1)
    except EmptyPage:
        assets = paginator.page(paginator.num_pages)
    
    # Get selected asset and its cards
    selected_asset = None
    asset_cards = []
    
    if selected_asset_id:
        try:
            selected_asset = RefAsset.objects.select_related('AssetTypeId').get(AssetId=selected_asset_id)
            asset_cards = Ref_Asset_Card.objects.select_related('AssetId', 'EmployeeId').filter(
                AssetId=selected_asset
            ).order_by('AssetCardId')
        except RefAsset.DoesNotExist:
            selected_asset = None
    
    return render(request, 'core/refasset_master_detail.html', {
        'asset_types': asset_types,
        'assets': assets,
        'selected_asset_type_id': selected_asset_type_id,
        'selected_asset': selected_asset,
        'selected_asset_id': selected_asset_id,
        'asset_cards': asset_cards,
        'paginator': paginator,
        'filters': {
            'asset_code': asset_code_filter,
            'asset_name': asset_name_filter,
            'status': status_filter,
        }
    })


@login_required
@permission_required('core.add_refasset', raise_exception=True)
def refasset_create(request):
    """Create a new asset"""
    if request.method == 'POST':
        form = RefAssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.CreatedBy = request.user
            asset.save()
            messages.success(request, 'Asset created successfully.')
            return redirect('core:asset_master_detail')
    else:
        form = RefAssetForm()
    
    return render(request, 'core/refasset_form.html', {
        'form': form,
        'title': 'Create Asset'
    })


@login_required
@permission_required('core.change_refasset', raise_exception=True)
def refasset_update(request, pk):
    """Update an existing asset"""
    asset = get_object_or_404(RefAsset, pk=pk)
    
    if request.method == 'POST':
        form = RefAssetForm(request.POST, instance=asset)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.ModifiedBy = request.user
            asset.save()
            messages.success(request, 'Asset updated successfully.')
            return redirect('core:asset_master_detail')
    else:
        form = RefAssetForm(instance=asset)
    
    return render(request, 'core/refasset_form.html', {
        'form': form,
        'title': 'Update Asset',
        'asset': asset
    })


@login_required
@permission_required('core.delete_refasset', raise_exception=True)
def refasset_delete(request, pk):
    """Delete an asset"""
    asset = get_object_or_404(RefAsset, pk=pk)
    
    # Check if this is a modal request
    if request.GET.get('modal'):
        # Return modal content
        return render(request, 'core/components/delete_modal.html', {
            'item_name': f"{asset.AssetCode} - {asset.AssetName}",
            'delete_url': reverse('core:refasset_delete', args=[pk])
        })
    
    # Handle actual delete
    if request.method == 'POST':
        try:
            asset.delete()
            messages.success(request, 'Asset deleted successfully.')
        except ProtectedError as e:
            messages.error(request, f'Cannot delete asset "{asset.AssetCode} - {asset.AssetName}" because it is referenced by other records. Please remove all references first.')
        return redirect('core:asset_master_detail')
    
    # GET request without modal parameter - redirect to list
    return redirect('core:asset_master_detail')


@login_required
@permission_required('core.view_ref_asset_card', raise_exception=True)
def ref_asset_card_list(request):
    """List all asset cards with filtering and pagination"""
    # Get filter parameters
    asset_filter = request.GET.get('asset', '')
    asset_code_filter = request.GET.get('asset_code', '')
    asset_name_filter = request.GET.get('asset_name', '')
    status_filter = request.GET.get('status', '')
    page = request.GET.get('page', 1)
    
    # Get all asset cards with related data
    asset_cards = Ref_Asset_Card.objects.select_related('AssetId', 'ClientId').order_by('AssetCardId')
    
    # Apply filters
    if asset_filter:
        asset_cards = asset_cards.filter(AssetId__AssetId=asset_filter)
    
    if asset_code_filter:
        asset_cards = asset_cards.filter(AssetCardCode__icontains=asset_code_filter)
    
    if asset_name_filter:
        asset_cards = asset_cards.filter(AssetCardName__icontains=asset_name_filter)
    
    if status_filter:
        if status_filter == 'active':
            asset_cards = asset_cards.filter(IsDelete=False)
        elif status_filter == 'inactive':
            asset_cards = asset_cards.filter(IsDelete=True)
    
    # Pagination
    paginator = Paginator(asset_cards, 20)  # Show 20 asset cards per page
    try:
        asset_cards = paginator.page(page)
    except PageNotAnInteger:
        asset_cards = paginator.page(1)
    except EmptyPage:
        asset_cards = paginator.page(paginator.num_pages)
    
    # Get all assets for dropdown filter
    assets = RefAsset.objects.filter(IsDelete=False).order_by('AssetName')
    
    # Check if this is a modal request
    if request.GET.get('modal'):
        return render(request, 'core/refassetcard_list.html', {
            'asset_cards': asset_cards,
            'assets': assets,
            'filters': {
                'asset': asset_filter,
                'asset_code': asset_code_filter,
                'asset_name': asset_name_filter,
                'status': status_filter,
            },
            'paginator': paginator,
            'is_modal': True
        })
    
    return render(request, 'core/refassetcard_list.html', {
        'asset_cards': asset_cards,
        'assets': assets,
        'filters': {
            'asset': asset_filter,
            'asset_code': asset_code_filter,
            'asset_name': asset_name_filter,
            'status': status_filter,
        },
        'paginator': paginator,
        'is_modal': False
    })


@login_required
@permission_required('core.add_ref_asset_card', raise_exception=True)
def ref_asset_card_create(request):
    """Create a new asset card"""
    if request.method == 'POST':
        form = Ref_Asset_CardForm(request.POST)
        if form.is_valid():
            asset_card = form.save(commit=False)
            asset_card.CreatedBy = request.user
            asset_card.ModifiedBy = request.user
            asset_card.save()
            
            # Check if this is an AJAX request (from modal)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Asset card created successfully.',
                    'asset_card': {
                        'AssetCardId': asset_card.AssetCardId,
                        'AssetCardCode': asset_card.AssetCardCode,
                        'AssetCardName': asset_card.AssetCardName,
                        'AssetName': asset_card.AssetId.AssetName,
                        'UnitCost': str(asset_card.UnitCost),
                        'UnitPrice': str(asset_card.UnitPrice)
                    }
                })
            else:
                messages.success(request, 'Asset card created successfully.')
                return redirect('core:asset_master_detail')
        else:
            # Check if this is an AJAX request (from modal)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Please correct the errors below.',
                    'errors': form.errors
                }, status=400)
    else:
        form = Ref_Asset_CardForm()
    
    return render(request, 'core/refassetcard_form.html', {
        'form': form,
        'title': 'Create Asset Card'
    })


@login_required
@permission_required('core.change_ref_asset_card', raise_exception=True)
def ref_asset_card_update(request, pk):
    """Update an existing asset card"""
    asset_card = get_object_or_404(Ref_Asset_Card, pk=pk)
    
    if request.method == 'POST':
        form = Ref_Asset_CardForm(request.POST, instance=asset_card)
        if form.is_valid():
            asset_card = form.save(commit=False)
            asset_card.ModifiedBy = request.user
            asset_card.save()
            
            # Check if this is an AJAX request (from modal)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Asset card updated successfully.',
                    'asset_card': {
                        'AssetCardId': asset_card.AssetCardId,
                        'AssetCardCode': asset_card.AssetCardCode,
                        'AssetCardName': asset_card.AssetCardName,
                        'AssetName': asset_card.AssetId.AssetName,
                        'UnitCost': str(asset_card.UnitCost),
                        'UnitPrice': str(asset_card.UnitPrice)
                    }
                })
            else:
                messages.success(request, 'Asset card updated successfully.')
                return redirect('core:asset_master_detail')
        else:
            # Check if this is an AJAX request (from modal)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Please correct the errors below.',
                    'errors': form.errors
                }, status=400)
    else:
        form = Ref_Asset_CardForm(instance=asset_card)
    
    return render(request, 'core/refassetcard_form.html', {
        'form': form,
        'title': 'Update Asset Card',
        'asset_card': asset_card
    })


@login_required
@permission_required('core.delete_ref_asset_card', raise_exception=True)
def ref_asset_card_delete(request, pk):
    """Delete an asset card"""
    asset_card = get_object_or_404(Ref_Asset_Card, pk=pk)
    
    # Check if this is a modal request
    if request.GET.get('modal'):
        # Return modal content
        return render(request, 'core/components/delete_modal.html', {
            'item_name': f"{asset_card.AssetCardCode} - {asset_card.AssetId.AssetName}",
            'delete_url': reverse('core:ref_asset_card_delete', args=[pk])
        })
    
    # Handle actual delete
    if request.method == 'POST':
        try:
            asset_card.delete()
            messages.success(request, 'Asset card deleted successfully.')
        except ProtectedError as e:
            messages.error(request, f'Cannot delete asset card "{asset_card.AssetCardCode}" because it is referenced by other records. Please remove all references first.')
        return redirect('core:asset_master_detail')
    
    # GET request without modal parameter - redirect to list
    return redirect('core:asset_master_detail')


@login_required
@require_http_methods(["GET"])
def get_next_document_number(request):
    """API endpoint to get the next document number for a given DocumentTypeId"""
    document_type_id = request.GET.get('document_type_id')
    
    if not document_type_id:
        return JsonResponse({'error': 'DocumentTypeId is required'}, status=400)
    
    try:
        # Get the highest DocumentNo for this DocumentTypeId
        last_counter = Ref_Document_Counter.objects.filter(
            DocumentTypeId=document_type_id
        ).order_by('-DocumentNo').first()
        
        if last_counter:
            # Extract numeric part and increment
            try:
                # Assuming DocumentNo format is like "CASH0001", "INV0001", etc.
                import re
                match = re.search(r'(\d+)$', last_counter.DocumentNo)
                if match:
                    next_number = int(match.group(1)) + 1
                    # Get the prefix (non-numeric part)
                    prefix = last_counter.DocumentNo[:match.start()]
                    next_document_no = f"{prefix}{next_number:04d}"
                else:
                    # If no numeric part found, start with 1
                    next_document_no = f"{last_counter.DocumentNo}001"
            except (ValueError, AttributeError):
                # Fallback: append 001
                next_document_no = f"{last_counter.DocumentNo}001"
        else:
            # No previous documents, start with 1
            # Get document type to determine prefix
            try:
                doc_type = Ref_Document_Type.objects.get(DocumentTypeId=document_type_id)
                # Use first 4 characters of DocumentTypeCode as prefix, or "DOC" as fallback
                prefix = doc_type.DocumentTypeCode[:4] if doc_type.DocumentTypeCode else "DOC"
                next_document_no = f"{prefix}0001"
            except Ref_Document_Type.DoesNotExist:
                next_document_no = "DOC0001"
        
        return JsonResponse({
            'next_document_no': next_document_no,
            'document_type_id': document_type_id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@login_required
@permission_required('core.view_cashbeginningbalance', raise_exception=True)
def cashbeginningbalance_list(request, balance_type='cash'):
    """Display the beginning balance management page for different balance types"""
    try:
        # Define balance type configurations
        balance_configs = {
            'cash': {
                'title': 'Cash Beginning Balance',
                'subtitle': 'Manage initial cash balances for accounts',
                'page_title': 'Cash Beginning Balance Management',
                'section_name': 'Мөнгөн хөрөнгө'
            },
            'receivable': {
                'title': 'Receivable Beginning Balance',
                'subtitle': 'Manage initial receivable balances for accounts',
                'page_title': 'Receivable Beginning Balance Management',
                'section_name': 'Авлага, өглөг'
            }
        }
        
        # Get configuration for the balance type
        config = balance_configs.get(balance_type, balance_configs['cash'])
        
        # For now, we'll use the same CashBeginningBalance model for all types
        # In the future, you can create separate models for different balance types
        balances = CashBeginningBalance.objects.select_related(
            'AccountID', 'ClientID', 'CurrencyID', 'CreatedBy', 'ModifiedBy'
        ).filter(IsDelete=False).order_by('-CreatedDate')
        
        return render(request, 'core/cashbeginningbalance_list.html', {
            'balances': balances,
            'balance_type': balance_type,
            'config': config
        })
        
    except Exception as e:
        messages.error(request, f'Error loading beginning balances: {str(e)}')
        return render(request, 'core/cashbeginningbalance_list.html', {
            'balances': [],
            'balance_type': balance_type,
            'config': balance_configs.get(balance_type, balance_configs['cash'])
        })


@login_required
@permission_required('core.add_cashbeginningbalance', raise_exception=True)
def cashbeginningbalance_create(request, balance_type=None):
    """Create a new cash beginning balance"""
    if request.method == 'POST':
        try:
            # Get form data
            account_id = request.POST.get('AccountID')
            client_id = request.POST.get('ClientID')
            currency_id = request.POST.get('CurrencyID')
            currency_exchange = request.POST.get('CurrencyExchange')
            currency_amount = request.POST.get('CurrencyAmount')
            
            # Validate required fields
            if not all([account_id, client_id, currency_id, currency_exchange, currency_amount]):
                messages.error(request, 'All required fields must be filled')
                return redirect('core:cashbeginningbalance_list')
            
            # Get related objects
            account = get_object_or_404(Ref_Account, AccountId=account_id)
            client = get_object_or_404(RefClient, ClientId=client_id)
            currency = get_object_or_404(Ref_Currency, CurrencyId=currency_id)
            
            # Create the balance
            balance = CashBeginningBalance.objects.create(
                AccountID=account,
                ClientID=client,
                CurrencyID=currency,
                CurrencyExchange=currency_exchange,
                CurrencyAmount=currency_amount,
                CreatedBy=request.user,
                ModifiedBy=request.user
            )
            
            messages.success(request, 'Beginning balance created successfully')
            return redirect('core:cashbeginningbalance_list')
            
        except Exception as e:
            messages.error(request, f'Error creating balance: {str(e)}')
            return redirect('core:cashbeginningbalance_list')
    
    return redirect('core:cashbeginningbalance_list')


@login_required
@permission_required('core.change_cashbeginningbalance', raise_exception=True)
def cashbeginningbalance_update(request, balance_id, balance_type=None):
    """Update an existing cash beginning balance"""
    if request.method == 'POST':
        try:
            balance = get_object_or_404(CashBeginningBalance, BeginningBalanceID=balance_id)
            
            # Get form data
            account_id = request.POST.get('AccountID')
            client_id = request.POST.get('ClientID')
            currency_id = request.POST.get('CurrencyID')
            currency_exchange = request.POST.get('CurrencyExchange')
            currency_amount = request.POST.get('CurrencyAmount')
            
            # Validate required fields
            if not all([account_id, client_id, currency_id, currency_exchange, currency_amount]):
                messages.error(request, 'All required fields must be filled')
                return redirect('core:cashbeginningbalance_list')
            
            # Get related objects
            account = get_object_or_404(Ref_Account, AccountId=account_id)
            client = get_object_or_404(RefClient, ClientId=client_id)
            currency = get_object_or_404(Ref_Currency, CurrencyId=currency_id)
            
            # Update the balance
            balance.AccountID = account
            balance.ClientID = client
            balance.CurrencyID = currency
            balance.CurrencyExchange = currency_exchange
            balance.CurrencyAmount = currency_amount
            balance.ModifiedBy = request.user
            balance.save()
            
            messages.success(request, 'Beginning balance updated successfully')
            return redirect('core:cashbeginningbalance_list')
            
        except Exception as e:
            messages.error(request, f'Error updating balance: {str(e)}')
            return redirect('core:cashbeginningbalance_list')
    
    return redirect('core:cashbeginningbalance_list')


@login_required
@permission_required('core.delete_cashbeginningbalance', raise_exception=True)
def cashbeginningbalance_delete(request, balance_id, balance_type=None):
    """Delete a cash beginning balance (soft delete)"""
    if request.method == 'POST':
        try:
            balance = get_object_or_404(CashBeginningBalance, BeginningBalanceID=balance_id)
            balance.IsDelete = True
            balance.ModifiedBy = request.user
            balance.save()
            
            messages.success(request, 'Beginning balance deleted successfully')
            return redirect('core:cashbeginningbalance_list')
            
        except Exception as e:
            messages.error(request, f'Error deleting balance: {str(e)}')
            return redirect('core:cashbeginningbalance_list')
    
    return redirect('core:cashbeginningbalance_list')


# Inventory Beginning Balance Views
@login_required
@permission_required('core.view_invbeginningbalance', raise_exception=True)
def invbeginningbalance_list(request):
    """Display the inventory beginning balance management page"""
    try:
        # Get all inventory beginning balances with related data
        balances = Inv_Beginning_Balance.objects.select_related(
            'AccountId', 'InventoryId', 'WarehouseId', 'CreatedBy'
        ).filter(IsDelete=False).order_by('-CreatedDate')
        
        # Get warehouses for the form
        warehouses = Ref_Warehouse.objects.filter(IsDelete=False).order_by('WarehouseCode')
        
        context = {
            'balances': balances,
            'warehouses': warehouses,
            'config': {
                'title': 'Inventory Beginning Balances',
                'subtitle': 'Manage initial inventory balances for accounts',
                'page_title': 'Inventory Beginning Balance Management'
            }
        }
        
        return render(request, 'core/invbeginningbalance_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading inventory beginning balances: {str(e)}')
        return render(request, 'core/invbeginningbalance_list.html', {
            'balances': [],
            'warehouses': [],
            'config': {
                'title': 'Inventory Beginning Balances',
                'subtitle': 'Manage initial inventory balances for accounts',
                'page_title': 'Inventory Beginning Balance Management'
            }
        })


@login_required
@permission_required('core.add_invbeginningbalance', raise_exception=True)
def invbeginningbalance_create(request):
    """Create a new inventory beginning balance"""
    if request.method == 'POST':
        try:
            # Get form data
            account_id = request.POST.get('AccountId')
            inventory_id = request.POST.get('InventoryId')
            quantity = request.POST.get('Quantity')
            unit_cost = request.POST.get('UnitCost')
            unit_price = request.POST.get('UnitPrice')
            warehouse_id = request.POST.get('WarehouseId')
            employee_id = request.POST.get('EmployeeId')
            
            # Validate required fields
            if not all([account_id, inventory_id, quantity, unit_cost, unit_price, warehouse_id]):
                messages.error(request, 'All required fields must be filled.')
                return redirect('core:invbeginningbalance_list')
            
            # Create the balance
            balance = Inv_Beginning_Balance.objects.create(
                AccountId_id=account_id,
                InventoryId_id=inventory_id,
                Quantity=quantity,
                UnitCost=unit_cost,
                UnitPrice=unit_price,
                WarehouseId_id=warehouse_id,
                EmployeeId=employee_id if employee_id else None,
                CreatedBy=request.user
            )
            
            messages.success(request, 'Inventory beginning balance created successfully')
            return redirect('core:invbeginningbalance_list')
            
        except Exception as e:
            messages.error(request, f'Error creating inventory beginning balance: {str(e)}')
            return redirect('core:invbeginningbalance_list')
    
    return redirect('core:invbeginningbalance_list')


@login_required
@permission_required('core.change_invbeginningbalance', raise_exception=True)
def invbeginningbalance_update(request, balance_id):
    """Update an existing inventory beginning balance"""
    if request.method == 'POST':
        try:
            balance = get_object_or_404(Inv_Beginning_Balance, BeginningBalanceId=balance_id)
            
            # Get form data
            account_id = request.POST.get('AccountId')
            inventory_id = request.POST.get('InventoryId')
            quantity = request.POST.get('Quantity')
            unit_cost = request.POST.get('UnitCost')
            unit_price = request.POST.get('UnitPrice')
            warehouse_id = request.POST.get('WarehouseId')
            employee_id = request.POST.get('EmployeeId')
            
            # Validate required fields
            if not all([account_id, inventory_id, quantity, unit_cost, unit_price, warehouse_id]):
                messages.error(request, 'All required fields must be filled.')
                return redirect('core:invbeginningbalance_list')
            
            # Update the balance
            balance.AccountId_id = account_id
            balance.InventoryId_id = inventory_id
            balance.Quantity = quantity
            balance.UnitCost = unit_cost
            balance.UnitPrice = unit_price
            balance.WarehouseId_id = warehouse_id
            balance.EmployeeId = employee_id if employee_id else None
            balance.ModifiedBy = request.user
            balance.save()
            
            messages.success(request, 'Inventory beginning balance updated successfully')
            return redirect('core:invbeginningbalance_list')
            
        except Exception as e:
            messages.error(request, f'Error updating inventory beginning balance: {str(e)}')
            return redirect('core:invbeginningbalance_list')
    
    return redirect('core:invbeginningbalance_list')


@login_required
@permission_required('core.delete_invbeginningbalance', raise_exception=True)
def invbeginningbalance_delete(request, balance_id):
    """Delete an inventory beginning balance (soft delete)"""
    if request.method == 'POST':
        try:
            balance = get_object_or_404(Inv_Beginning_Balance, BeginningBalanceId=balance_id)
            balance.IsDelete = True
            balance.ModifiedBy = request.user
            balance.save()
            
            messages.success(request, 'Inventory beginning balance deleted successfully')
            return redirect('core:invbeginningbalance_list')
            
        except Exception as e:
            messages.error(request, f'Error deleting inventory beginning balance: {str(e)}')
            return redirect('core:invbeginningbalance_list')
    
    return redirect('core:invbeginningbalance_list')


# ==================== JSON API ENDPOINTS ====================

@login_required
def assets_json(request):
    """JSON endpoint for assets data"""
    assets = RefAsset.objects.filter(IsDelete=False).order_by('AssetName')
    data = {
        'assets': [
            {
                'AssetId': asset.AssetId,
                'AssetName': asset.AssetName,
                'AssetCode': asset.AssetCode,
                'AssetTypeName': asset.AssetTypeId.AssetTypeName if asset.AssetTypeId else ''
            }
            for asset in assets
        ]
    }
    return JsonResponse(data)


@login_required
def clients_json(request):
    """JSON endpoint for clients data"""
    clients = RefClient.objects.filter(IsDelete=False).order_by('ClientName')
    data = {
        'clients': [
            {
                'ClientId': client.ClientId,
                'ClientName': client.ClientName,
                'ClientCode': client.ClientCode
            }
            for client in clients
        ]
    }
    return JsonResponse(data)


@login_required
@permission_required('core.view_refclienttype', raise_exception=True)
def refclient_types_json(request):
    """Return client types as JSON for populating selects in modals"""
    types = RefClientType.objects.filter(IsActive=True).order_by('ClientTypeName')
    return JsonResponse({
        'results': [
            {
                'id': getattr(t, 'ClientTypeId', getattr(t, 'id', None)),
                'clienttypename': t.ClientTypeName,
            }
            for t in types
        ]
    })


# ==================== PERIOD LOCK MANAGEMENT VIEWS ====================

@login_required
@permission_required('core.view_refperiod', raise_exception=True)
def period_lock_list(request):
    """Display the period lock management page"""
    try:
        periods = Ref_Period.objects.all().order_by('PeriodId')
        return render(request, 'core/period_lock_list.html', {
            'periods': periods
        })
    except Exception as e:
        messages.error(request, f'Error loading periods: {str(e)}')
        return render(request, 'core/period_lock_list.html', {
            'periods': []
        })


@login_required
@permission_required('core.change_refperiod', raise_exception=True)
@require_http_methods(["POST"])
def period_lock_toggle(request, period_id):
    """Toggle the lock status of a period via AJAX"""
    try:
        period = get_object_or_404(Ref_Period, PeriodId=period_id)
        
        # Toggle the lock status
        period.IsLock = not period.IsLock
        period.save()
        
        return JsonResponse({
            'success': True,
            'isLock': period.IsLock,
            'message': f'Period {period.PeriodName} {"locked" if period.IsLock else "unlocked"} successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error toggling period lock: {str(e)}'
        }, status=500)



# ==================== ASSET BEGINNING BALANCE VIEWS ====================

@login_required
def astbeginningbalance_list(request):
    """Display the asset beginning balance management page"""
    try:
        # Get all asset beginning balances with related data
        balances = Ast_Beginning_Balance.objects.select_related(
            'AccountId', 'AssetCardId__AssetId', 'ClientId', 'CreatedBy'
        ).filter(IsDelete=False).order_by('-CreatedDate')
        
        context = {
            'balances': balances,
            'config': {
                'title': 'Asset Beginning Balances',
                'subtitle': 'Manage initial asset balances for accounts',
                'page_title': 'Asset Beginning Balance Management'
            }
        }
        
        return render(request, 'core/astbeginningbalance_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading asset beginning balances: {str(e)}')
        return render(request, 'core/astbeginningbalance_list.html', {
            'balances': [],
            'config': {
                'title': 'Asset Beginning Balances',
                'subtitle': 'Manage initial asset balances for accounts',
                'page_title': 'Asset Beginning Balance Management'
            }
        })


@login_required
def astbeginningbalance_create(request):
    """Create a new asset beginning balance"""
    if request.method == 'POST':
        try:
            # Get form data
            account_id = request.POST.get('AccountId')
            asset_card_id = request.POST.get('AssetCardId')
            quantity = request.POST.get('Quantity')
            unit_cost = request.POST.get('UnitCost')
            unit_price = request.POST.get('UnitPrice')
            client_id = request.POST.get('ClientId')
            
            print(f"DEBUG: Form data received - AccountId: {account_id}, AssetCardId: {asset_card_id}, Quantity: {quantity}, UnitCost: {unit_cost}, UnitPrice: {unit_price}, ClientId: {client_id}")
            
            # Validate required fields
            if not all([account_id, asset_card_id, quantity, unit_cost, unit_price]):
                messages.error(request, 'All required fields must be filled.')
                print("DEBUG: Missing required fields")
                return redirect('core:astbeginningbalance_list')
            
            # Create the balance
            balance = Ast_Beginning_Balance.objects.create(
                AccountId_id=account_id,
                AssetCardId_id=asset_card_id,
                Quantity=quantity,
                UnitCost=unit_cost,
                UnitPrice=unit_price,
                ClientId_id=client_id if client_id else None,
                CreatedBy=request.user
            )
            
            print(f"DEBUG: Created balance with ID: {balance.BeginningBalanceId}")
            messages.success(request, 'Asset beginning balance created successfully')
            return redirect('core:astbeginningbalance_list')
            
        except Exception as e:
            print(f"DEBUG: Error creating balance: {str(e)}")
            messages.error(request, f'Error creating asset beginning balance: {str(e)}')
            return redirect('core:astbeginningbalance_list')
    
    print("DEBUG: Not a POST request")
    return redirect('core:astbeginningbalance_list')


@login_required
def astbeginningbalance_update(request, balance_id):
    """Update an existing asset beginning balance"""
    if request.method == 'POST':
        try:
            balance = get_object_or_404(Ast_Beginning_Balance, BeginningBalanceId=balance_id)
            
            # Get form data
            account_id = request.POST.get('AccountId')
            asset_card_id = request.POST.get('AssetCardId')
            quantity = request.POST.get('Quantity')
            unit_cost = request.POST.get('UnitCost')
            unit_price = request.POST.get('UnitPrice')
            employee_id = request.POST.get('EmployeeId')
            
            # Validate required fields
            if not all([account_id, asset_card_id, quantity, unit_cost, unit_price]):
                messages.error(request, 'All required fields must be filled.')
                return redirect('core:astbeginningbalance_list')
            
            # Update the balance
            balance.AccountId_id = account_id
            balance.AssetCardId_id = asset_card_id
            balance.Quantity = quantity
            balance.UnitCost = unit_cost
            balance.UnitPrice = unit_price
            balance.EmployeeId_id = employee_id if employee_id else None
            balance.ModifiedBy = request.user
            balance.save()
            
            messages.success(request, 'Asset beginning balance updated successfully')
            return redirect('core:astbeginningbalance_list')
            
        except Exception as e:
            messages.error(request, f'Error updating asset beginning balance: {str(e)}')
            return redirect('core:astbeginningbalance_list')
    
    return redirect('core:astbeginningbalance_list')


@login_required
def astbeginningbalance_delete(request, balance_id):
    """Delete an asset beginning balance"""
    if request.method == 'POST':
        try:
            balance = get_object_or_404(Ast_Beginning_Balance, BeginningBalanceId=balance_id)
            balance.delete()
            
            messages.success(request, 'Asset beginning balance deleted successfully')
            return redirect('core:astbeginningbalance_list')
            
        except Exception as e:
            messages.error(request, f'Error deleting asset beginning balance: {str(e)}')
            return redirect('core:astbeginningbalance_list')
    
    return redirect('core:astbeginningbalance_list')


@login_required
@permission_required('core.view_cash_document', raise_exception=True)
def cash_documents(request):
    """View for displaying cash documents with new template"""
    # Get cash documents with related data (including deleted ones)
    cash_documents = Cash_Document.objects.select_related(
        'DocumentTypeId', 'ClientId', 'AccountId', 'CurrencyId', 'TemplateId'
    ).order_by('-DocumentDate')
    
    context = {
        'cash_documents': cash_documents,
    }
    
    return render(request, 'core/cash_journal_new.html', context)


@login_required
@permission_required('core.view_cash_document', raise_exception=True)
def get_cash_documents_filtered(request):
    """API endpoint to get ALL cash documents and details for all tabs in one call"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method allowed'}, status=405)
    
    try:
        # Get filter parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        document_type_id = request.GET.get('document_type_id')  # NEW PARAMETER for filtering by DocumentTypeId
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 1000))  # Large page size to get all records
        
        # Limit page size to prevent abuse
        if page_size > 2000:
            page_size = 2000
        
        # Get ALL cash documents (both active and deleted) with related data
        all_documents = Cash_Document.objects.select_related(
            'DocumentTypeId', 'AccountId', 'ClientId', 'CurrencyId', 'TemplateId', 'CreatedBy'
        ).order_by('-DocumentDate').distinct()
        
        # Apply date filtering if provided
        if start_date:
            all_documents = all_documents.filter(DocumentDate__gte=start_date)
        if end_date:
            all_documents = all_documents.filter(DocumentDate__lte=end_date)
        
        # Apply DocumentTypeId filter if provided
        if document_type_id:
            all_documents = all_documents.filter(DocumentTypeId=document_type_id)
        else:
            # Default behavior: exclude depreciation (13) and closing (14) entries
            all_documents = all_documents.exclude(DocumentTypeId__in=[13, 14])
        
        # Get ALL cash document details for ЖУРНАЛ tab
        all_details = Cash_DocumentDetail.objects.select_related(
            'DocumentId__DocumentTypeId', 'AccountId', 'ClientId', 'CurrencyId', 'DocumentId__CreatedBy'
        ).order_by('DocumentId__DocumentNo')
        
        # Apply date filtering to details if provided
        if start_date:
            all_details = all_details.filter(DocumentId__DocumentDate__gte=start_date)
        if end_date:
            all_details = all_details.filter(DocumentId__DocumentDate__lte=end_date)
        
        # Apply DocumentTypeId filter to details if provided
        if document_type_id:
            all_details = all_details.filter(DocumentId__DocumentTypeId=document_type_id)
        else:
            # Default behavior: exclude depreciation (13) and closing (14) entries
            all_details = all_details.exclude(DocumentId__DocumentTypeId__in=[13, 14])
        
        # Format documents data for БАРИМТ and УСТГАСАН БАРИМТ tabs
        documents_data = []
        seen_documents = set()
        
        for doc in all_documents:
            # Create a unique key for this document
            doc_key = f"{doc.DocumentId}_{doc.DocumentNo}_{doc.DocumentDate}"
            
            # Skip if we've already seen this document
            if doc_key in seen_documents:
                continue
                
            seen_documents.add(doc_key)
            
            documents_data.append({
                'DocumentId': doc.DocumentId,
                'DocumentNo': doc.DocumentNo,
                'DocumentDate': doc.DocumentDate.strftime('%Y-%m-%d'),
                'DocumentTypeCode': doc.DocumentTypeId.DocumentTypeCode if doc.DocumentTypeId else '',
                'ClientName': doc.ClientId.ClientName if doc.ClientId else '',
                'Description': doc.Description,
                'IsVat': doc.IsVat,
                'AccountCode': doc.AccountId.AccountCode if doc.AccountId else '',
                'CurrencyId': doc.CurrencyId.CurrencyId if doc.CurrencyId else '',
                'CurrencyName': doc.CurrencyId.Currency_name if doc.CurrencyId else '',
                'CurrencyAmount': float(doc.CurrencyAmount) if doc.CurrencyAmount else 0.0,
                'CurrencyExchange': float(doc.CurrencyExchange) if doc.CurrencyExchange else 0.0,
                'CurrencyMNT': float(doc.CurrencyMNT) if doc.CurrencyMNT else 0.0,
                'UserName': doc.CreatedBy.username if doc.CreatedBy else '',
                'IsDelete': doc.IsDelete,  # Include delete status for frontend filtering
            })
        
        # Format details data for ЖУРНАЛ tab
        details_data = []
        for detail in all_details:
            details_data.append({
                'document_no': detail.DocumentId.DocumentNo,
                'document_date': detail.DocumentId.DocumentDate.strftime('%Y-%m-%d'),
                'account_code': detail.AccountId.AccountCode if detail.AccountId else '',
                'account_name': detail.AccountId.AccountName if detail.AccountId else '',
                'client_name': detail.ClientId.ClientName if detail.ClientId else '',
                'description': detail.DocumentId.Description,
                'currency_code': detail.CurrencyId.CurrencyId if detail.CurrencyId else '',
                'currency_name': detail.CurrencyId.Currency_name if detail.CurrencyId else '',
                'currency_amount': float(detail.CurrencyAmount) if detail.CurrencyAmount else 0.0,
                'currency_exchange': float(detail.CurrencyExchange) if detail.CurrencyExchange else 0.0,
                'debit_amount': float(detail.DebitAmount) if detail.DebitAmount else 0.0,
                'credit_amount': float(detail.CreditAmount) if detail.CreditAmount else 0.0,
                'user_name': detail.DocumentId.CreatedBy.username if detail.DocumentId.CreatedBy else '',
            })
        
        
        return JsonResponse({
            'success': True,
            'documents': documents_data,  # For БАРИМТ and УСТГАСАН БАРИМТ tabs
            'details': details_data,     # For ЖУРНАЛ tab
            'documents_count': len(documents_data),
            'details_count': len(details_data),
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error loading comprehensive data: {str(e)}'
        }, status=500)




# ==================== TRIAL CLOSING ENTRY VIEWS ====================

@login_required
@permission_required('core.view_astdepreciationexpense', raise_exception=True)
def trial_closing_entry(request):
    """Display trial closing entry page with 3 tabs"""
    return render(request, 'core/trial_closing_entry.html')


@login_required
@permission_required('core.view_astdepreciationexpense', raise_exception=True)
def api_depreciation_summary(request):
    """Returns depreciation expenses as summary (1 row per record)"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method allowed'}, status=405)
    
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            return JsonResponse({
                'success': False,
                'error': 'start_date and end_date parameters are required'
            }, status=400)
        
        # Query depreciation expenses
        expenses = AstDepreciationExpense.objects.filter(
            DepreciationDate__range=[start_date, end_date]
        ).select_related(
            'AssetCardId', 'DebitAccountId', 'CreditAccountId',
            'AccountId', 'PeriodId', 'CreatedBy', 'DocumentId'
        ).order_by('DepreciationDate', 'AstDepExpId')
        
        # Return 1 row per expense (not split into debit/credit)
        entries = []
        for exp in expenses:
            entries.append({
                'document_no': exp.DocumentId.DocumentNo if exp.DocumentId else f'DEP-{exp.AstDepExpId}',
                'document_date': exp.DepreciationDate.strftime('%Y-%m-%d') if exp.DepreciationDate else '',
                'account_code': exp.AccountId.AccountCode if exp.AccountId else '',
                'account_name': exp.AccountId.AccountName if exp.AccountId else '',
                'client_name': exp.AssetCardId.AssetCardName if exp.AssetCardId else '',
                'description': f'{exp.AssetCardId.AssetCardName} ({exp.PeriodId.PeriodName})' if exp.AssetCardId and exp.PeriodId else 'Depreciation',
                'currency_name': 'MNT',
                'currency_amount': float(exp.ExpenseAmount) if exp.ExpenseAmount else 0.0,
                'currency_exchange': 1.0,
                'debit_amount': float(exp.ExpenseAmount) if exp.ExpenseAmount else 0.0,
                'credit_amount': 0.0,
                'user_name': exp.CreatedBy.username if exp.CreatedBy else ''
            })
        
        return JsonResponse({
            'success': True,
            'details': entries,  # Use 'details' key for consistency with get_cash_documents_filtered
            'total': len(entries),
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error loading depreciation summary: {str(e)}'
        }, status=500)


def api_asset_depreciation_expenses(request):
    """Returns asset depreciation expenses with detailed asset card information"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method allowed'}, status=405)
    
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            return JsonResponse({
                'success': False,
                'error': 'start_date and end_date parameters are required'
            }, status=400)
        
        # Query depreciation expenses with all related data
        expenses = AstDepreciationExpense.objects.filter(
            DepreciationDate__range=[start_date, end_date]
        ).select_related(
            'AssetCardId', 'DebitAccountId', 'CreditAccountId',
            'AccountId', 'PeriodId', 'CreatedBy', 'DocumentId'
        ).order_by('DepreciationDate', 'AstDepExpId')
        
        # Build response data
        entries = []
        for exp in expenses:
            entries.append({
                'account_id': exp.AccountId.AccountId if exp.AccountId else None,
                'account_code': exp.AccountId.AccountCode if exp.AccountId else '',
                'asset_card_id': exp.AssetCardId.AssetCardId if exp.AssetCardId else None,
                'asset_card_name': exp.AssetCardId.AssetCardName if exp.AssetCardId else '',
                'daily_expense': float(exp.AssetCardId.DailyExpense) if exp.AssetCardId and exp.AssetCardId.DailyExpense else 0.0,
                'expense_day': exp.ExpenseDay,
                'expense_amount': float(exp.ExpenseAmount) if exp.ExpenseAmount else 0.0,
                'created_date': exp.CreatedDate.strftime('%Y-%m-%d') if exp.CreatedDate else '',
                'created_by': exp.CreatedBy.username if exp.CreatedBy else '',
                'debit_account_code': exp.DebitAccountId.AccountCode if exp.DebitAccountId else '',
                'credit_account_id': exp.CreditAccountId.AccountId if exp.CreditAccountId else None,
                'credit_account_code': exp.CreditAccountId.AccountCode if exp.CreditAccountId else '',
                'document_id': exp.DocumentId.DocumentId if exp.DocumentId else None,
                'document_no': exp.DocumentId.DocumentNo if exp.DocumentId else ''
            })
        
        return JsonResponse({
            'success': True,
            'details': entries,
            'total': len(entries),
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error loading asset depreciation expenses: {str(e)}'
        }, status=500)


# ==================== ASSET DOCUMENT VIEWS ====================

@login_required
@permission_required('core.view_ast_document', raise_exception=True)
def astdocument_master_detail(request):
    """Master-detail view for asset documents"""
    # Get filter parameters
    selected_document_id = request.GET.get('selected_document')
    page = request.GET.get('page', 1)
    
    # Get all documents with related data (exclude deleted records)
    documents = Ast_Document.objects.select_related(
        'DocumentTypeId', 'ClientId', 'AccountId'
    ).filter(IsDelete=False).order_by('-DocumentDate', '-DocumentId')
    
    # Apply filters if provided
    document_no_filter = request.GET.get('document_no')
    if document_no_filter:
        documents = documents.filter(DocumentNo__icontains=document_no_filter)
    
    document_type_filter = request.GET.get('document_type')
    if document_type_filter:
        documents = documents.filter(DocumentTypeId__DocumentTypeId=document_type_filter)
    
    client_filter = request.GET.get('client')
    if client_filter:
        documents = documents.filter(ClientId__ClientId=client_filter)
    
    date_filter = request.GET.get('date')
    if date_filter:
        documents = documents.filter(DocumentDate__date=date_filter)
    
    description_filter = request.GET.get('description')
    if description_filter:
        documents = documents.filter(Description__icontains=description_filter)
    
    account_filter = request.GET.get('account')
    if account_filter:
        documents = documents.filter(AccountId__AccountId=account_filter)
    
    created_by_filter = request.GET.get('created_by')
    if created_by_filter:
        documents = documents.filter(CreatedBy__username__icontains=created_by_filter)
    
    # Pagination - load all records for client-side processing
    paginator = Paginator(documents, 5000)  # Load all records for instant client-side filtering/pagination
    try:
        documents = paginator.page(page)
    except PageNotAnInteger:
        documents = paginator.page(1)
    except EmptyPage:
        documents = paginator.page(paginator.num_pages)
    
    # Get selected document and its items
    selected_document = None
    document_items = []
    document_details = []
    
    if selected_document_id:
        try:
            selected_document = Ast_Document.objects.select_related(
                'DocumentTypeId', 'ClientId', 'AccountId'
            ).filter(IsDelete=False).get(DocumentId=selected_document_id)
            
            document_items = Ast_Document_Item.objects.select_related('AssetCardId').filter(
                DocumentId=selected_document
            ).order_by('DocumentItemId')
            
            # Get document details (accounting details)
            document_details = Ast_Document_Detail.objects.select_related(
                'AccountId', 'ClientId', 'CurrencyId'
            ).filter(DocumentId=selected_document).order_by('DocumentDetailId')
            
        except Ast_Document.DoesNotExist:
            selected_document = None
    else:
        # No document selected
        selected_document = None
        document_items = []
        document_details = []
    
    context = {
        'documents': documents,
        'selected_document': selected_document,
        'selected_document_id': selected_document_id,
        'document_items': document_items,
        'document_details': document_details,
        'paginator': paginator,
    }
    
    # Check if this is an AJAX request for detail grid only
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('ajax') == '1':
        # Return only the detail grid HTML
        return render(request, 'core/components/ast_document_detail_grid.html', context)
    
    return render(request, 'core/astdocument_master_detail.html', context)


@login_required
@permission_required('core.add_ast_document', raise_exception=True)
def astdocument_create(request, parentid=None):
    """Create a new asset document"""
    if request.method == 'POST':
        form = AstDocumentForm(request.POST, parentid=parentid)
        if form.is_valid():
            document = form.save(commit=False)
            document.CreatedBy = request.user
            document.save()
            
            # Save DocumentNo to Ref_Document_Counter table
            Ref_Document_Counter.objects.create(
                DocumentNo=document.DocumentNo,
                DocumentTypeId=document.DocumentTypeId,
                CreatedBy=request.user
            )
            
            messages.success(request, 'Asset document created successfully.')
            return redirect('core:astdocument_master_detail')
    else:
        form = AstDocumentForm(parentid=parentid)
    
    # Get VAT account IDs from ref_constant table and fetch actual account codes
    vat_accounts = {}
    try:
        from .models import Ref_Constant, Ref_Account
        vat_constant_9 = Ref_Constant.objects.get(ConstantID=9)
        vat_constant_10 = Ref_Constant.objects.get(ConstantID=10)
        
        # Get actual account codes for VAT accounts
        vat_account_8 = Ref_Account.objects.get(AccountId=8)
        vat_account_9 = Ref_Account.objects.get(AccountId=9)
        
        vat_accounts = {
            'vat_account_1_id': 8,  # ConstantID=9 maps to VatAccountId=8
            'vat_account_2_id': 9,  # ConstantID=10 maps to VatAccountId=9
            'vat_account_1_display': vat_account_8.AccountCode,
            'vat_account_2_display': vat_account_9.AccountCode,
        }
    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
        # Fallback values
        vat_accounts = {
            'vat_account_1_id': 8,  # ConstantID=9 maps to VatAccountId=8
            'vat_account_2_id': 9,  # ConstantID=10 maps to VatAccountId=9
            'vat_account_1_display': '3403-01',
            'vat_account_2_display': '3403-02',
        }
    
    return render(request, 'core/astdocument_form.html', {
        'form': form,
        'item': None,
        'parentid': parentid,
        'vat_accounts': vat_accounts
    })


@login_required
@permission_required('core.change_ast_document', raise_exception=True)
def astdocument_update(request, pk, parentid=None):
    """Update an existing asset document"""
    document = get_object_or_404(Ast_Document, pk=pk, IsDelete=False)
    
    # Check if user owns this document
    if document.CreatedBy != request.user:
        messages.error(request, 'You do not have permission to edit this document.')
        return redirect('core:astdocument_master_detail')
    
    if request.method == 'POST':
        form = AstDocumentForm(request.POST, instance=document, parentid=parentid)
        if form.is_valid():
            document = form.save(commit=False)
            document.ModifiedBy = request.user
            document.save()
            messages.success(request, 'Asset document updated successfully.')
            return redirect('core:astdocument_master_detail')
    else:
        form = AstDocumentForm(instance=document, parentid=parentid)
    
    # Get VAT account IDs from ref_constant table and fetch actual account codes
    vat_accounts = {}
    try:
        from .models import Ref_Constant, Ref_Account
        vat_constant_9 = Ref_Constant.objects.get(ConstantID=9)
        vat_constant_10 = Ref_Constant.objects.get(ConstantID=10)
        
        # Get actual account codes for VAT accounts
        vat_account_8 = Ref_Account.objects.get(AccountId=8)
        vat_account_9 = Ref_Account.objects.get(AccountId=9)
        
        vat_accounts = {
            'vat_account_1_id': 8,  # ConstantID=9 maps to VatAccountId=8
            'vat_account_2_id': 9,  # ConstantID=10 maps to VatAccountId=9
            'vat_account_1_display': vat_account_8.AccountCode,
            'vat_account_2_display': vat_account_9.AccountCode,
        }
    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
        # Fallback values
        vat_accounts = {
            'vat_account_1_id': 8,  # ConstantID=9 maps to VatAccountId=8
            'vat_account_2_id': 9,  # ConstantID=10 maps to VatAccountId=9
            'vat_account_1_display': '3403-01',
            'vat_account_2_display': '3403-02',
        }
    
    return render(request, 'core/astdocument_form.html', {
        'form': form,
        'item': document,
        'parentid': parentid,
        'vat_accounts': vat_accounts
    })


@login_required
@permission_required('core.delete_ast_document', raise_exception=True)
def astdocument_delete(request, pk):
    """Delete an asset document"""
    document = get_object_or_404(Ast_Document, pk=pk)
    
    # Check if user owns this document
    if document.CreatedBy != request.user:
        messages.error(request, 'You do not have permission to delete this document.')
        return redirect('core:astdocument_master_detail')
    
    if request.method == 'POST':
        try:
            # Soft delete the document
            document.IsDelete = True
            document.save()
            messages.success(request, 'Asset document deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting asset document: {str(e)}')
    
    return redirect('core:astdocument_master_detail')


@login_required
@permission_required('core.view_ast_document_detail', raise_exception=True)
def bulk_manage_ast_details(request, document_id):
    """Bulk manage asset document details"""
    document = get_object_or_404(Ast_Document, pk=document_id, IsDelete=False)
    
    # Get document items and details
    document_items = Ast_Document_Item.objects.select_related('AssetCardId').filter(
        DocumentId=document
    ).order_by('DocumentItemId')
    
    document_details = Ast_Document_Detail.objects.select_related(
        'AccountId', 'ClientId', 'CurrencyId'
    ).filter(DocumentId=document).order_by('DocumentDetailId')
    
    # Get currencies for the form
    currencies = Ref_Currency.objects.filter(IsActive=True).order_by('CurrencyId')
    
    # VAT rate is available globally via context processor (VAT_RATE_PERCENT)
    # No need to pass it explicitly in context
    
    context = {
        'document': document,
        'document_items': document_items,
        'document_details': document_details,
        'currencies': currencies,
    }
    
    return render(request, 'core/astdocumentdetail_bulk_manage.html', context)


@login_required
@permission_required('core.add_ast_documentdetail', raise_exception=True)
@require_http_methods(["POST"])
def api_bulk_manage_ast_details(request, document_id):
    """API endpoint for bulk managing asset document details"""
    try:
        document = get_object_or_404(Ast_Document, pk=document_id, IsDelete=False)
        data = json.loads(request.body)
        
        # Process asset items
        items = data.get('items', {})
        new_items = data.get('new_items', [])
        deleted_items = data.get('deleted_items', [])
        
        # Update existing items
        for item_id, item_data in items.items():
            try:
                item = Ast_Document_Item.objects.get(DocumentItemId=item_id, DocumentId=document)
                item.AssetCardId_id = item_data['asset_card_id']
                item.Quantity = item_data['quantity']
                item.UnitCost = item_data['unit_cost']
                item.UnitPrice = item_data['unit_price']
                item.save()
            except Ast_Document_Item.DoesNotExist:
                continue
        
        # Create new items
        for item_data in new_items:
            Ast_Document_Item.objects.create(
                DocumentId=document,
                AssetCardId_id=item_data['asset_card_id'],
                Quantity=item_data['quantity'],
                UnitCost=item_data['unit_cost'],
                UnitPrice=item_data['unit_price']
            )
        
        # Delete items
        for item_id in deleted_items:
            try:
                item = Ast_Document_Item.objects.get(DocumentItemId=item_id, DocumentId=document)
                item.delete()
            except Ast_Document_Item.DoesNotExist:
                continue
        
        # Process accounting details
        details = data.get('details', [])
        
        # Clear existing details
        Ast_Document_Detail.objects.filter(DocumentId=document).delete()
        
        # Create new details
        for detail_data in details:
            Ast_Document_Detail.objects.create(
                DocumentId=document,
                AccountId_id=detail_data['account_id'],
                ClientId_id=detail_data.get('client_id'),
                CurrencyId_id=detail_data['currency_id'],
                CurrencyExchange=detail_data.get('currency_exchange', 1.0),
                CurrencyAmount=detail_data['currency_amount'],
                IsDebit=detail_data['is_debit'],
                DebitAmount=detail_data.get('debit_amount', 0),
                CreditAmount=detail_data.get('credit_amount', 0)
            )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== API ENDPOINTS FOR MODALS ====================

@login_required
def assets_json(request):
    """API endpoint to return assets as JSON for modal dropdowns"""
    try:
        assets = RefAsset.objects.filter(IsDelete=False).order_by('AssetName')
        assets_data = []
        
        for asset in assets:
            assets_data.append({
                'AssetId': asset.AssetId,
                'AssetName': asset.AssetName,
                'AssetCode': asset.AssetCode
            })
        
        return JsonResponse({
            'success': True,
            'assets': assets_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def clients_json(request):
    """API endpoint to return clients as JSON for modal dropdowns"""
    try:
        clients = RefClient.objects.filter(IsDelete=False).order_by('ClientName')
        clients_data = []
        
        for client in clients:
            clients_data.append({
                'ClientId': client.ClientId,
                'ClientName': client.ClientName,
                'ClientCode': client.ClientCode
            })
        
        return JsonResponse({
            'success': True,
            'clients': clients_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def refclient_types_json(request):
    """API endpoint to return client types as JSON for modal dropdowns"""
    try:
        client_types = RefClientType.objects.filter(IsActive=True).order_by('ClientTypeName')
        types_data = []
        
        for client_type in client_types:
            types_data.append({
                'ClientTypeId': client_type.ClientTypeId,
                'ClientTypeName': client_type.ClientTypeName
            })
        
        return JsonResponse({
            'success': True,
            'client_types': types_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def trial_balance(request):
    """Trial Balance Report View"""
    try:
        # Get date parameters from request
        begin_date = request.GET.get('begin_date', '')
        end_date = request.GET.get('end_date', '')
        
        trial_balance_data = []
        error_message = None
        
        if begin_date and end_date:
            # Execute the trial balance function
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM calculate_trial_balance(%s, %s)",
                    [begin_date, end_date]
                )
                
                # Get column names
                columns = [col[0] for col in cursor.description]
                
                # Fetch all results
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                trial_balance_data = [
                    dict(zip(columns, row)) for row in results
                ]
        
        context = {
            'trial_balance_data': trial_balance_data,
            'begin_date': begin_date,
            'end_date': end_date,
            'error_message': error_message,
        }
        
        return render(request, 'core/trial_balance.html', context)
        
    except Exception as e:
        context = {
            'trial_balance_data': [],
            'begin_date': begin_date if 'begin_date' in locals() else '',
            'end_date': end_date if 'end_date' in locals() else '',
            'error_message': f'Error generating trial balance: {str(e)}',
        }
        return render(request, 'core/trial_balance.html', context)


@login_required
def recpay_balance(request):
    """Receivable and Payable Balance Report View"""
    try:
        # Get date parameters from request
        begin_date = request.GET.get('begin_date', '')
        end_date = request.GET.get('end_date', '')
        
        recpay_balance_data = []
        error_message = None
        
        if begin_date and end_date:
            # Execute the recpay balance function
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM calculate_recpay_balance(%s, %s)",
                    [begin_date, end_date]
                )
                
                # Get column names
                columns = [col[0] for col in cursor.description]
                
                # Fetch all results
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                recpay_balance_data = [
                    dict(zip(columns, row)) for row in results
                ]
        
        context = {
            'recpay_balance_data': recpay_balance_data,
            'begin_date': begin_date,
            'end_date': end_date,
            'error_message': error_message,
        }
        
        return render(request, 'core/trial_recpay_balance.html', context)
        
    except Exception as e:
        context = {
            'recpay_balance_data': [],
            'begin_date': begin_date if 'begin_date' in locals() else '',
            'end_date': end_date if 'end_date' in locals() else '',
            'error_message': f'Error generating receivable/payable balance: {str(e)}',
        }
        return render(request, 'core/trial_recpay_balance.html', context)


@csrf_exempt
@login_required
def account_statement_detail(request):
    """Account Statement Detail API endpoint"""
    try:
        # Get parameters from request
        account_id = request.GET.get('account_id')
        begin_date = request.GET.get('begin_date')
        end_date = request.GET.get('end_date')
        
        # Convert account_id to integer
        try:
            account_id = int(account_id)
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': 'Invalid account_id parameter'
            }, status=400)
        
        if not all([account_id, begin_date, end_date]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required parameters: account_id, begin_date, end_date'
            }, status=400)
        
        # Get account information
        try:
            account = Ref_Account.objects.select_related('AccountTypeId').get(AccountId=account_id, IsDelete=False)
            account_type = account.AccountTypeId
        except Ref_Account.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Account not found'
            }, status=404)
        
        # Get documents with all their details where at least one detail matches the account
        try:
            with connection.cursor() as cursor:
                # First, get all cash documents with their details
                cursor.execute("""
                SELECT 
                    cd."DocumentId",
                    cd."DocumentDate",
                    cd."DocumentNo",
                    dt."Description" as DocumentType,
                    COALESCE(cd."Description", '') as DocumentDescription,
                    cdd."DocumentDetailId",
                    a."AccountCode",
                    a."AccountName",
                    COALESCE(c."ClientCode", '') as ClientCode,
                    COALESCE(c."ClientName", '') as ClientName,
                    cdd."CurrencyAmount",
                    cdd."DebitAmount",
                    cdd."CreditAmount",
                    cdd."IsDebit",
                    'Cash' as DocumentCategory
                FROM cash_document cd
                INNER JOIN cash_document_detail cdd ON cd."DocumentId" = cdd."DocumentId"
                INNER JOIN ref_account a ON cdd."AccountId" = a."AccountId"
                LEFT JOIN ref_client c ON cdd."ClientId" = c."ClientId"
                INNER JOIN ref_document_type dt ON cd."DocumentTypeId" = dt."DocumentTypeId"
                WHERE cd."DocumentId" IN (
                    SELECT DISTINCT "DocumentId" 
                    FROM cash_document_detail 
                    WHERE "AccountId" = %s
                )
                AND cd."DocumentDate" >= %s 
                AND cd."DocumentDate" <= %s 
                AND cd."IsDelete" = false
                
                UNION ALL
                
                SELECT 
                    id."DocumentId",
                    id."DocumentDate",
                    id."DocumentNo",
                    dt."Description" as DocumentType,
                    COALESCE(id."Description", '') as DocumentDescription,
                    idd."DocumentDetailId",
                    a."AccountCode",
                    a."AccountName",
                    COALESCE(c."ClientCode", '') as ClientCode,
                    COALESCE(c."ClientName", '') as ClientName,
                    idd."CurrencyAmount",
                    idd."DebitAmount",
                    idd."CreditAmount",
                    idd."IsDebit",
                    'Inventory' as DocumentCategory
                FROM inv_document id
                INNER JOIN inv_document_detail idd ON id."DocumentId" = idd."DocumentId"
                INNER JOIN ref_account a ON idd."AccountId" = a."AccountId"
                LEFT JOIN ref_client c ON idd."ClientId" = c."ClientId"
                INNER JOIN ref_document_type dt ON id."DocumentTypeId" = dt."DocumentTypeId"
                WHERE id."DocumentId" IN (
                    SELECT DISTINCT "DocumentId" 
                    FROM inv_document_detail 
                    WHERE "AccountId" = %s
                )
                AND id."DocumentDate" >= %s 
                AND id."DocumentDate" <= %s 
                AND id."IsDelete" = false
                
                UNION ALL
                
                SELECT 
                    ad."DocumentId",
                    ad."DocumentDate",
                    ad."DocumentNo",
                    dt."Description" as DocumentType,
                    COALESCE(ad."Description", '') as DocumentDescription,
                    add."DocumentDetailId",
                    a."AccountCode",
                    a."AccountName",
                    COALESCE(c."ClientCode", '') as ClientCode,
                    COALESCE(c."ClientName", '') as ClientName,
                    add."CurrencyAmount",
                    add."DebitAmount",
                    add."CreditAmount",
                    add."IsDebit",
                    'Asset' as DocumentCategory
                FROM ast_document ad
                INNER JOIN ast_document_detail add ON ad."DocumentId" = add."DocumentId"
                INNER JOIN ref_account a ON add."AccountId" = a."AccountId"
                LEFT JOIN ref_client c ON add."ClientId" = c."ClientId"
                INNER JOIN ref_document_type dt ON ad."DocumentTypeId" = dt."DocumentTypeId"
                WHERE ad."DocumentId" IN (
                    SELECT DISTINCT "DocumentId" 
                    FROM ast_document_detail 
                    WHERE "AccountId" = %s
                )
                AND ad."DocumentDate" >= %s 
                AND ad."DocumentDate" <= %s 
                AND ad."IsDelete" = false
                
                ORDER BY "DocumentDate", "DocumentNo", "DocumentDetailId"
            """, [account_id, begin_date, end_date, account_id, begin_date, end_date, account_id, begin_date, end_date])
                
                # Get column names
                columns = [col[0] for col in cursor.description]
                
                # Fetch all results
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                all_details = [
                    dict(zip(columns, row)) for row in results
                ]
            
                # Group details by document
                documents = {}
                total_debit = 0
                total_credit = 0
                
                for detail in all_details:
                    doc_id = detail['DocumentId']
                    
                    if doc_id not in documents:
                        documents[doc_id] = {
                            'DocumentId': doc_id,
                            'DocumentNo': detail['DocumentNo'],
                            'DocumentDate': detail['DocumentDate'],
                            'DocumentType': detail['documenttype'],
                            'DocumentDescription': detail['documentdescription'],
                            'DocumentCategory': detail['documentcategory'],
                            'TotalAmount': 0,
                            'details': []
                        }
                    
                    # Add detail to document
                    detail_info = {
                        'DetailId': detail['DocumentDetailId'],
                        'AccountCode': detail['AccountCode'],
                        'AccountName': detail['AccountName'],
                        'ClientCode': detail['clientcode'],
                        'ClientName': detail['clientname'],
                        'CurrencyAmount': float(detail['CurrencyAmount'] or 0),
                        'DebitAmount': float(detail['DebitAmount'] or 0),
                        'CreditAmount': float(detail['CreditAmount'] or 0),
                        'IsDebit': detail['IsDebit'],
                        'IsMatchingAccount': detail['AccountCode'] == account.AccountCode
                    }
                    
                    documents[doc_id]['details'].append(detail_info)
                    
                    # Add to totals (only for matching account details)
                    if detail_info['IsMatchingAccount']:
                        total_debit += detail_info['DebitAmount']
                        total_credit += detail_info['CreditAmount']
                
                # Calculate document totals after processing all details
                for doc_id, doc in documents.items():
                    doc['TotalAmount'] = sum(
                        detail['DebitAmount'] + detail['CreditAmount'] 
                        for detail in doc['details'] 
                        if detail['IsMatchingAccount']
                    )
                
                # Convert to list and sort by date
                documents_list = list(documents.values())
                documents_list.sort(key=lambda x: (x['DocumentDate'], x['DocumentNo']))
                
                
                return JsonResponse({
                    'success': True,
                    'account': {
                        'AccountId': account.AccountId,
                        'AccountCode': account.AccountCode,
                        'AccountName': account.AccountName,
                        'AccountType': account_type.AccountTypeName,
                        'IsActive': account_type.IsActive
                    },
                    'total_debit': float(total_debit),
                    'total_credit': float(total_credit),
                    'documents': documents_list,
                    'date_range': {
                        'begin_date': begin_date,
                        'end_date': end_date
                    }
                })
                
        except Exception as e:
            print(f"SQL Error in account_statement_detail: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Database error: {str(e)}'
            }, status=500)
        
    except Exception as e:
        print(f"Error in account_statement_detail: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error generating account statement: {str(e)}'
        }, status=500)


@csrf_exempt
@login_required
def ref_asset_depreciation_account_list(request):
    """List all asset depreciation accounts with pagination"""
    depreciation_accounts = Ref_Asset_Depreciation_Account.objects.select_related(
        'AssetAccountId', 'DepreciationAccountId', 'ExpenseAccountId', 'CreatedBy', 'ModifiedBy'
    ).all()
    
    # Pagination
    paginator = Paginator(depreciation_accounts, 20)
    page_number = request.GET.get('page')
    depreciation_accounts = paginator.get_page(page_number)
    
    context = {
        'depreciation_accounts': depreciation_accounts,
    }
    
    return render(request, 'core/refasset_depreciation_account_list.html', context)


def ref_asset_depreciation_account_form(request, ast_dep_id=None):
    """Form for creating or editing asset depreciation accounts"""
    if ast_dep_id:
        depreciation_account = get_object_or_404(Ref_Asset_Depreciation_Account, AstDepId=ast_dep_id)
        form = Ref_Asset_Depreciation_AccountForm(instance=depreciation_account)
        title = f"Edit Asset Depreciation Account - {depreciation_account.AstDepId}"
    else:
        depreciation_account = None
        form = Ref_Asset_Depreciation_AccountForm()
        title = "Create New Asset Depreciation Account"
    
    if request.method == 'POST':
        if ast_dep_id:
            form = Ref_Asset_Depreciation_AccountForm(request.POST, instance=depreciation_account)
        else:
            form = Ref_Asset_Depreciation_AccountForm(request.POST)
        
        if form.is_valid():
            depreciation_account = form.save(commit=False)
            if not ast_dep_id:  # New record
                depreciation_account.CreatedBy = request.user
            depreciation_account.ModifiedBy = request.user
            depreciation_account.save()
            
            messages.success(request, f"Asset depreciation account {'updated' if ast_dep_id else 'created'} successfully.")
            return redirect('core:ref_asset_depreciation_account_list')
        else:
            messages.error(request, "Please correct the errors below.")
    
    context = {
        'form': form,
        'title': title,
        'depreciation_account': depreciation_account,
        'is_edit': ast_dep_id is not None
    }
    
    return render(request, 'core/refasset_depreciation_account_form.html', context)


def ref_asset_depreciation_account_delete(request, ast_dep_id):
    """Delete asset depreciation account (soft delete)"""
    depreciation_account = get_object_or_404(Ref_Asset_Depreciation_Account, AstDepId=ast_dep_id)
    
    if request.method == 'POST':
        depreciation_account.IsDelete = True
        depreciation_account.ModifiedBy = request.user
        depreciation_account.save()
        
        messages.success(request, f"Asset depreciation account {ast_dep_id} has been deleted.")
        return redirect('core:ref_asset_depreciation_account_list')
    
    # For GET requests, redirect to list with error message
    messages.error(request, "Invalid request method for deletion.")
    return redirect('core:ref_asset_depreciation_account_list')


@login_required
def calculate_depreciation_view(request):
    """Calculate depreciation expenses for a selected period"""
    if request.method == 'POST':
        period_id = request.POST.get('period_id')
        
        if not period_id:
            messages.error(request, "Please select a period.")
            return redirect('core:calculate_depreciation')
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM calculate_depreciation(%s)", [period_id])
                columns = [col[0] for col in cursor.description]
                results = [
                    dict(zip(columns, row))
                    for row in cursor.fetchall()
                ]
            
            if results:
                messages.success(request, f"Successfully calculated {len(results)} depreciation expense records.")
            else:
                messages.warning(request, "No depreciation expenses calculated. Please check if assets have DailyExpense values and positive quantities.")
            
            context = {
                'results': results,
                'period': Ref_Period.objects.get(PeriodId=period_id),
                'periods': Ref_Period.objects.all().order_by('-PeriodId')
            }
            return render(request, 'core/calculate_depreciation_results.html', context)
            
        except Exception as e:
            messages.error(request, f"Error calculating depreciation: {str(e)}")
            return redirect('core:calculate_depreciation')
    
    # GET request - show form
    periods = Ref_Period.objects.all().order_by('-PeriodId')
    context = {
        'periods': periods
    }
    return render(request, 'core/calculate_depreciation_form.html', context)


def test_api(request):
    """Simple test API endpoint"""
    return JsonResponse({
        'success': True,
        'message': 'API is working',
        'user': request.user.username
    })


@login_required
@permission_required('core.view_ref_template', raise_exception=True)
def api_templates_list(request):
    """API endpoint to get templates filtered by AccountId and DocumentTypeId"""
    try:
        account_id = request.GET.get('account_id')
        document_type_id = request.GET.get('document_type_id')
        
        if not account_id or not document_type_id:
            return JsonResponse({
                'success': False,
                'message': 'Both account_id and document_type_id are required'
            }, status=400)
        
        # Filter templates by AccountId and DocumentTypeId
        templates = Ref_Template.objects.filter(
            AccountId=account_id,
            DocumentTypeId=document_type_id,
            IsDelete=False
        ).select_related('AccountId', 'DocumentTypeId').order_by('TemplateName')
        
        templates_data = []
        for template in templates:
            templates_data.append({
                'TemplateId': template.TemplateId,
                'TemplateName': template.TemplateName,
                'AccountId': template.AccountId.AccountId if template.AccountId else None,
                'AccountName': template.AccountId.AccountName if template.AccountId else None,
                'DocumentTypeId': template.DocumentTypeId.DocumentTypeId,
                'DocumentTypeName': template.DocumentTypeId.Description,
                'IsVat': template.IsVat
            })
        
        return JsonResponse({
            'success': True,
            'templates': templates_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error fetching templates: {str(e)}'
        }, status=500)


@login_required
@permission_required('core.view_ref_template', raise_exception=True)
def api_template_details(request, template_id):
    """API endpoint to get template details for a specific template"""
    try:
        template = get_object_or_404(Ref_Template, TemplateId=template_id, IsDelete=False)
        
        # Get template details
        template_details = Ref_Template_Detail.objects.filter(
            TemplateId=template
        ).select_related('AccountId', 'AccountId__AccountTypeId').order_by('TemplateDetailId')
        
        details_data = []
        for detail in template_details:
            details_data.append({
                'TemplateDetailId': detail.TemplateDetailId,
                'AccountId': detail.AccountId.AccountId,
                'AccountCode': detail.AccountId.AccountCode,
                'AccountName': detail.AccountId.AccountName,
                'AccountTypeId': detail.AccountId.AccountTypeId.AccountTypeId,
                'IsDebit': detail.IsDebit
            })
        
        return JsonResponse({
            'success': True,
            'template': {
                'TemplateId': template.TemplateId,
                'TemplateName': template.TemplateName,
                'AccountId': template.AccountId.AccountId if template.AccountId else None,
                'AccountName': template.AccountId.AccountName if template.AccountId else None,
                'DocumentTypeId': template.DocumentTypeId.DocumentTypeId,
                'DocumentTypeName': template.DocumentTypeId.Description,
                'CashFlowId': template.CashFlowId.CashFlowId if template.CashFlowId else None,
                'CashFlowDescription': template.CashFlowId.Description if template.CashFlowId else None,
                'IsVat': template.IsVat
            },
            'template_details': details_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error fetching template details: {str(e)}'
        }, status=500)


@login_required
@permission_required('core.view_ref_account', raise_exception=True)
def api_account_details(request, account_id):
    """API endpoint to get account details by ID"""
    try:
        account = get_object_or_404(Ref_Account, AccountId=account_id, IsDelete=False)
        
        return JsonResponse({
            'success': True,
            'account': {
                'AccountId': account.AccountId,
                'AccountCode': account.AccountCode,
                'AccountName': account.AccountName,
                'AccountType': account.AccountTypeId.AccountTypeName if account.AccountTypeId else None
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error fetching account details: {str(e)}'
        }, status=500)


@login_required
@permission_required('core.view_inv_document', raise_exception=True)
def get_inventory_documents_master(request):
    """API endpoint for inventory documents master table with date range filtering"""
    try:
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        
        documents_query = Inv_Document.objects.select_related(
            'DocumentTypeId', 'ClientId', 'AccountId', 'WarehouseId', 'CreatedBy'
        ).filter(IsDelete=False)
        
        if start_date:
            documents_query = documents_query.filter(DocumentDate__gte=start_date)
        if end_date:
            documents_query = documents_query.filter(DocumentDate__lte=end_date)
        
        documents_query = documents_query.order_by('-DocumentDate')
        
        documents_data = []
        for doc in documents_query:
            documents_data.append({
                'DocumentId': doc.DocumentId,
                'DocumentNo': doc.DocumentNo,
                'DocumentTypeCode': doc.DocumentTypeId.DocumentTypeCode if doc.DocumentTypeId else '',
                'ClientName': doc.ClientId.ClientName if doc.ClientId else '',
                'DocumentDate': doc.DocumentDate.strftime('%Y-%m-%d') if doc.DocumentDate else '',
                'Description': doc.Description or '',
                'AccountCode': doc.AccountId.AccountCode if doc.AccountId else '',
                'AccountName': doc.AccountId.AccountName if doc.AccountId else '',
                'IsVat': doc.IsVat,
                'WarehouseCode': doc.WarehouseId.WarehouseCode if doc.WarehouseId else '',
                'WarehouseName': doc.WarehouseId.WarehouseName if doc.WarehouseId else '',
                'CostAmount': float(doc.CostAmount) if doc.CostAmount else 0,
                'PriceAmount': float(doc.PriceAmount) if doc.PriceAmount else 0,
                'CreatedByUsername': doc.CreatedBy.username if doc.CreatedBy else '',
                'CreatedById': doc.CreatedBy.id if doc.CreatedBy else None,
            })
        
        return JsonResponse({
            'success': True,
            'documents': documents_data,
            'count': len(documents_data)
        })
        
    except Exception as e:
        logger.error(f"Error in get_inventory_documents_master: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== TEMPLATE MANAGEMENT VIEWS ====================

@login_required
@permission_required('core.view_ref_template', raise_exception=True)
def template_master_detail(request):
    """Master-detail view for template management"""
    
    # Get all templates for the master table
    templates = Ref_Template.objects.select_related(
        'DocumentTypeId', 'AccountId', 'CashFlowId', 'CreatedBy'
    ).filter(IsDelete=False).order_by('-CreatedDate')
    
    # Get selected template ID for detail grids (AJAX request)
    selected_template_id = request.GET.get('selected_template')
    selected_template = None
    template_details = []
    
    if selected_template_id:
        try:
            selected_template = Ref_Template.objects.select_related(
                'DocumentTypeId', 'AccountId', 'CashFlowId', 'CreatedBy'
            ).filter(IsDelete=False).get(TemplateId=selected_template_id)
            
            template_details = Ref_Template_Detail.objects.select_related(
                'AccountId', 'TemplateId'
            ).filter(TemplateId=selected_template).order_by('TemplateDetailId')
            
        except Ref_Template.DoesNotExist:
            selected_template = None
    
    context = {
        'templates': templates,
        'selected_template': selected_template,
        'selected_template_id': selected_template_id,
        'template_details': template_details,
    }
    
    # Check if this is an AJAX request for detail grids only
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.GET.get('ajax') == '1':
        # Return only the detail grids HTML
        return render(request, 'core/components/template_detail_grid.html', context)
    
    return render(request, 'core/template_master_detail.html', context)


@login_required
@permission_required('core.add_ref_template', raise_exception=True)
def template_create(request):
    """Create a new template"""
    if request.method == 'POST':
        form = Ref_TemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.CreatedBy = request.user
            template.save()
            
            messages.success(request, 'Template created successfully.')
            return redirect('core:template_master_detail')
    else:
        form = Ref_TemplateForm()
    
    return render(request, 'core/template_form.html', {
        'form': form,
        'title': 'Create Template',
        'submit_text': 'Create Template'
    })


@login_required
@permission_required('core.change_ref_template', raise_exception=True)
def template_update(request, pk):
    """Update an existing template"""
    template = get_object_or_404(Ref_Template, pk=pk, IsDelete=False)
    
    # Check if user owns this template
    if template.CreatedBy != request.user:
        messages.error(request, 'You do not have permission to edit this template.')
        return redirect('core:template_master_detail')
    
    if request.method == 'POST':
        form = Ref_TemplateForm(request.POST, instance=template)
        if form.is_valid():
            template = form.save(commit=False)
            template.save()
            messages.success(request, 'Template updated successfully.')
            return redirect('core:template_master_detail')
    else:
        form = Ref_TemplateForm(instance=template)
    
    return render(request, 'core/template_form.html', {
        'form': form,
        'title': 'Update Template',
        'submit_text': 'Update Template'
    })


@login_required
@permission_required('core.delete_ref_template', raise_exception=True)
def template_delete(request, pk):
    """Delete a template"""
    template = get_object_or_404(Ref_Template, pk=pk, IsDelete=False)
    
    # Check if user owns this template
    if template.CreatedBy != request.user:
        messages.error(request, 'You do not have permission to delete this template.')
    else:
        template.IsDelete = True
        template.save()
        messages.success(request, 'Template deleted successfully.')
    
    return redirect('core:template_master_detail')


@login_required
@permission_required('core.add_ref_template', raise_exception=True)
def template_detail_create(request, template_id):
    """Create a new template detail"""
    template = get_object_or_404(Ref_Template, pk=template_id, IsDelete=False)
    
    # Check if user owns this template
    if template.CreatedBy != request.user:
        messages.error(request, 'You do not have permission to edit this template.')
        return redirect('core:template_master_detail')
    
    if request.method == 'POST':
        form = Ref_Template_DetailForm(request.POST)
        if form.is_valid():
            template_detail = form.save(commit=False)
            template_detail.TemplateId = template
            template_detail.save()
            
            messages.success(request, 'Template detail added successfully.')
            return redirect('core:template_master_detail')
    else:
        form = Ref_Template_DetailForm()
    
    return render(request, 'core/template_detail_form.html', {
        'form': form,
        'template': template,
        'title': 'Add Template Detail',
        'submit_text': 'Add Detail'
    })


@login_required
@permission_required('core.change_ref_template', raise_exception=True)
def template_detail_update(request, pk):
    """Update an existing template detail"""
    template_detail = get_object_or_404(Ref_Template_Detail, pk=pk)
    template = template_detail.TemplateId
    
    # Check if user owns this template
    if template.CreatedBy != request.user:
        messages.error(request, 'You do not have permission to edit this template.')
        return redirect('core:template_master_detail')
    
    if request.method == 'POST':
        form = Ref_Template_DetailForm(request.POST, instance=template_detail)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template detail updated successfully.')
            return redirect('core:template_master_detail')
    else:
        form = Ref_Template_DetailForm(instance=template_detail)
    
    return render(request, 'core/template_detail_form.html', {
        'form': form,
        'template': template,
        'title': 'Update Template Detail',
        'submit_text': 'Update Detail'
    })


@login_required
@permission_required('core.delete_ref_template', raise_exception=True)
def template_detail_delete(request, pk):
    """Delete a template detail"""
    template_detail = get_object_or_404(Ref_Template_Detail, pk=pk)
    template = template_detail.TemplateId
    
    # Check if user owns this template
    if template.CreatedBy != request.user:
        messages.error(request, 'You do not have permission to delete this template.')
    else:
        template_detail.delete()
        messages.success(request, 'Template detail deleted successfully.')
    
    return redirect('core:template_master_detail')


