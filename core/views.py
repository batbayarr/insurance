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
import logging
from decimal import Decimal
from django.utils import timezone
from .models import Ref_Account_Type, Ref_Account, RefClientType, RefClient, Ref_Client_Bank, Ref_Currency, RefInventory, Ref_Document_Type, Ref_Document_Counter, Ref_CashFlow, Ref_Contract, Ref_Warehouse, Cash_Document, Cash_DocumentDetail, Inv_Document, Inv_Document_Item, Inv_Document_Detail, Ref_Asset_Type, RefAsset, Ref_Asset_Card, CashBeginningBalance, Inv_Beginning_Balance, Ast_Beginning_Balance, Ast_Document, Ast_Document_Detail, Ast_Document_Item, Ref_Asset_Depreciation_Account, Ref_Period, Ref_Template, Ref_Template_Detail, AstDepreciationExpense, St_Balance, St_Income, St_CashFlow

logger = logging.getLogger(__name__)
from django.db import connection, connections, transaction
from .forms import Ref_AccountForm, RefClientForm, Ref_Client_BankForm, RefInventoryForm, CashDocumentForm, InvDocumentForm, RefAssetForm, Ref_Asset_CardForm, InvBeginningBalanceForm, AstDocumentForm, Ref_Asset_Depreciation_AccountForm, Ref_TemplateForm, Ref_Template_DetailForm
from .utils import get_available_databases, set_database
from .thread_local import get_current_db
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
                # Explicitly save session to default database BEFORE switching
                request.session.save()
                
                # Set the database name in settings
                set_database(selected_db)
                
                # Use the selected database for authentication
                from django.contrib.auth import authenticate
                
                # Authenticate using the selected database
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    # Save session again after login
                    request.session.save()
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
    # - Otherwise → account types 1,2,3,5,42,43,44,51,55,67,68,45,46,47,48
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
                    account_type_filter = '1,2,3,5,42,43,44,51,55,67,68,45,46,47,48'
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
    
    # Get page size from request, default to 15
    page_size = request.GET.get('page_size', '15')
    try:
        page_size = int(page_size)
        # Validate page size (allow 10, 15, 20, 25, 50)
        if page_size not in [10, 15, 20, 25, 50]:
            page_size = 15
    except (ValueError, TypeError):
        page_size = 15
    
    # For modal/select mode, show more items and no pagination
    if is_modal or is_select_mode:
        accounts = accounts_list
        paginator = None
    else:
        # Pagination
        paginator = Paginator(accounts_list, page_size)
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
        'page_size': page_size,
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
        # If form is invalid, it will be passed to template with errors
    else:
        form = Ref_AccountForm()
    
    account_types = Ref_Account_Type.objects.all().order_by('AccountTypeCode')
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
    
    account_types = Ref_Account_Type.objects.all().order_by('AccountTypeCode')
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
            
            # Check if account is used in Cash_Document (AccountId or VatAccountId)
            if Cash_Document.objects.filter(AccountId=account, IsDelete=False).exists() or \
               Cash_Document.objects.filter(VatAccountId=account, IsDelete=False).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ дансаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if account is used in Cash_DocumentDetail
            if Cash_DocumentDetail.objects.filter(AccountId=account).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ дансаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if account is used in Inv_Document (AccountId or VatAccountId)
            if Inv_Document.objects.filter(AccountId=account, IsDelete=False).exists() or \
               Inv_Document.objects.filter(VatAccountId=account, IsDelete=False).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ дансаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if account is used in Inv_Document_Detail
            if Inv_Document_Detail.objects.filter(AccountId=account).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ дансаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if account is used in Ast_Document (AccountId or VatAccountId)
            if Ast_Document.objects.filter(AccountId=account, IsDelete=False).exists() or \
               Ast_Document.objects.filter(VatAccountId=account, IsDelete=False).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ дансаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if account is used in Ast_Document_Detail
            if Ast_Document_Detail.objects.filter(AccountId=account).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ дансаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if account is used in CashBeginningBalance
            if CashBeginningBalance.objects.filter(AccountID=account, IsDelete=False).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ дансаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if account is used in Inv_Beginning_Balance
            if Inv_Beginning_Balance.objects.filter(AccountId=account, IsDelete=False).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ дансаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if account is used in Ast_Beginning_Balance
            if Ast_Beginning_Balance.objects.filter(AccountId=account, IsDelete=False).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ дансаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if account is used in Ref_Asset_Depreciation_Account (AssetAccountId, DepreciationAccountId, ExpenseAccountId)
            if Ref_Asset_Depreciation_Account.objects.filter(AssetAccountId=account, IsDelete=False).exists() or \
               Ref_Asset_Depreciation_Account.objects.filter(DepreciationAccountId=account, IsDelete=False).exists() or \
               Ref_Asset_Depreciation_Account.objects.filter(ExpenseAccountId=account, IsDelete=False).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ дансаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if account is used in AstDepreciationExpense (DebitAccountId, CreditAccountId, AccountId)
            # Note: AstDepreciationExpense doesn't have IsDelete field, so check all records
            if AstDepreciationExpense.objects.filter(DebitAccountId=account).exists() or \
               AstDepreciationExpense.objects.filter(CreditAccountId=account).exists() or \
               AstDepreciationExpense.objects.filter(AccountId=account).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ дансаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
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
            
            error_message = 'Энэ дансаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
            
            # Check if account is used in Cash_Document (AccountId or VatAccountId)
            if Cash_Document.objects.filter(AccountId=account, IsDelete=False).exists() or \
               Cash_Document.objects.filter(VatAccountId=account, IsDelete=False).exists():
                messages.error(request, error_message)
                return redirect('core:refaccount_list')
            
            # Check if account is used in Cash_DocumentDetail
            if Cash_DocumentDetail.objects.filter(AccountId=account).exists():
                messages.error(request, error_message)
                return redirect('core:refaccount_list')
            
            # Check if account is used in Inv_Document (AccountId or VatAccountId)
            if Inv_Document.objects.filter(AccountId=account, IsDelete=False).exists() or \
               Inv_Document.objects.filter(VatAccountId=account, IsDelete=False).exists():
                messages.error(request, error_message)
                return redirect('core:refaccount_list')
            
            # Check if account is used in Inv_Document_Detail
            if Inv_Document_Detail.objects.filter(AccountId=account).exists():
                messages.error(request, error_message)
                return redirect('core:refaccount_list')
            
            # Check if account is used in Ast_Document (AccountId or VatAccountId)
            if Ast_Document.objects.filter(AccountId=account, IsDelete=False).exists() or \
               Ast_Document.objects.filter(VatAccountId=account, IsDelete=False).exists():
                messages.error(request, error_message)
                return redirect('core:refaccount_list')
            
            # Check if account is used in Ast_Document_Detail
            if Ast_Document_Detail.objects.filter(AccountId=account).exists():
                messages.error(request, error_message)
                return redirect('core:refaccount_list')
            
            # Check if account is used in CashBeginningBalance
            if CashBeginningBalance.objects.filter(AccountID=account, IsDelete=False).exists():
                messages.error(request, error_message)
                return redirect('core:refaccount_list')
            
            # Check if account is used in Inv_Beginning_Balance
            if Inv_Beginning_Balance.objects.filter(AccountId=account, IsDelete=False).exists():
                messages.error(request, error_message)
                return redirect('core:refaccount_list')
            
            # Check if account is used in Ast_Beginning_Balance
            if Ast_Beginning_Balance.objects.filter(AccountId=account, IsDelete=False).exists():
                messages.error(request, error_message)
                return redirect('core:refaccount_list')
            
            # Check if account is used in Ref_Asset_Depreciation_Account (AssetAccountId, DepreciationAccountId, ExpenseAccountId)
            if Ref_Asset_Depreciation_Account.objects.filter(AssetAccountId=account, IsDelete=False).exists() or \
               Ref_Asset_Depreciation_Account.objects.filter(DepreciationAccountId=account, IsDelete=False).exists() or \
               Ref_Asset_Depreciation_Account.objects.filter(ExpenseAccountId=account, IsDelete=False).exists():
                messages.error(request, error_message)
                return redirect('core:refaccount_list')
            
            # Check if account is used in AstDepreciationExpense (DebitAccountId, CreditAccountId, AccountId)
            # Note: AstDepreciationExpense doesn't have IsDelete field, so check all records
            if AstDepreciationExpense.objects.filter(DebitAccountId=account).exists() or \
               AstDepreciationExpense.objects.filter(CreditAccountId=account).exists() or \
               AstDepreciationExpense.objects.filter(AccountId=account).exists():
                messages.error(request, error_message)
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
    client_type_id = request.GET.get('client_type_id', '')
    
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
    # Filter by explicit client_type_id(s) if provided (comma-separated ids)
    if client_type_id:
        try:
            ids = [int(x) for x in client_type_id.split(',') if x.strip().isdigit()]
            if ids:
                clients_list = clients_list.filter(ClientType__ClientTypeId__in=ids)
        except Exception:
            pass
    
    clients_list = clients_list.order_by('ClientName')
    
    # Get page size from request, default to 15
    page_size = request.GET.get('page_size', '15')
    try:
        page_size = int(page_size)
        # Validate page size (allow 10, 15, 20, 25, 50)
        if page_size not in [10, 15, 20, 25, 50]:
            page_size = 15
    except (ValueError, TypeError):
        page_size = 15
    
    # For modal/select mode, show more items and no pagination
    if is_modal or is_select_mode:
        clients = clients_list
        paginator = None
    else:
        # Pagination
        paginator = Paginator(clients_list, page_size)
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
        'page_size': page_size,
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
        'title': 'Харилцагч нэмэх',
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
        'title': 'Харилцагчийн мэдээлэл шинэчлэх',
        'client': client,
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
            
            # Check if client exists in inv_document table (non-deleted records)
            if Inv_Document.objects.filter(ClientId=client, IsDelete=False).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if client exists in inv_document_detail table (non-null, non-deleted records)
            if Inv_Document_Detail.objects.filter(ClientId=client).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if client exists in cash_document table (non-deleted records)
            if Cash_Document.objects.filter(ClientId=client, IsDelete=False).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if client exists in cash_document_detail table (non-deleted records)
            if Cash_DocumentDetail.objects.filter(ClientId=client).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if client exists in ast_document table (non-deleted records)
            if Ast_Document.objects.filter(ClientId=client, IsDelete=False).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if client exists in ast_document_detail table (non-null, non-deleted records)
            if Ast_Document_Detail.objects.filter(ClientId=client).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if client exists in cash_beginning_balance table (non-deleted records)
            if CashBeginningBalance.objects.filter(ClientID=client, IsDelete=False).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
                })
            
            # Check if client exists in ast_beginning_balance table (non-null, non-deleted records)
            if Ast_Beginning_Balance.objects.filter(ClientId=client, IsDelete=False).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?'
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
            
            # Check if client exists in inv_document table (non-deleted records)
            if Inv_Document.objects.filter(ClientId=client, IsDelete=False).exists():
                messages.error(request, 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?')
                return redirect('core:refclient_list')
            
            # Check if client exists in inv_document_detail table (non-null, non-deleted records)
            if Inv_Document_Detail.objects.filter(ClientId=client).exists():
                messages.error(request, 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?')
                return redirect('core:refclient_list')
            
            # Check if client exists in cash_document table (non-deleted records)
            if Cash_Document.objects.filter(ClientId=client, IsDelete=False).exists():
                messages.error(request, 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?')
                return redirect('core:refclient_list')
            
            # Check if client exists in cash_document_detail table (non-deleted records)
            if Cash_DocumentDetail.objects.filter(ClientId=client).exists():
                messages.error(request, 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?')
                return redirect('core:refclient_list')
            
            # Check if client exists in ast_document table (non-deleted records)
            if Ast_Document.objects.filter(ClientId=client, IsDelete=False).exists():
                messages.error(request, 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?')
                return redirect('core:refclient_list')
            
            # Check if client exists in ast_document_detail table (non-null, non-deleted records)
            if Ast_Document_Detail.objects.filter(ClientId=client).exists():
                messages.error(request, 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?')
                return redirect('core:refclient_list')
            
            # Check if client exists in cash_beginning_balance table (non-deleted records)
            if CashBeginningBalance.objects.filter(ClientID=client, IsDelete=False).exists():
                messages.error(request, 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?')
                return redirect('core:refclient_list')
            
            # Check if client exists in ast_beginning_balance table (non-null, non-deleted records)
            if Ast_Beginning_Balance.objects.filter(ClientId=client, IsDelete=False).exists():
                messages.error(request, 'Энэ харилцагчаар эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн тул устгах боолмжгүй. Эхлээд шалгана уу?')
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


@login_required
@permission_required('core.view_refclient', raise_exception=True)
def client_bank_list(request, client_id):
    """AJAX view to return JSON list of bank accounts for a client"""
    try:
        client = get_object_or_404(RefClient, pk=client_id)
        banks = Ref_Client_Bank.objects.filter(ClientId=client).order_by('BankName', 'BankAccount')
        
        banks_data = []
        for bank in banks:
            banks_data.append({
                'ClientBankId': bank.ClientBankId,
                'BankName': bank.BankName,
                'BankAccount': bank.BankAccount,
                'IsActive': bank.IsActive
            })
        
        return JsonResponse({
            'success': True,
            'banks': banks_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Алдаа гарлаа: {str(e)}'
        })


@login_required
@permission_required('core.add_refclient', raise_exception=True)
def client_bank_create(request):
    """AJAX view to create new bank account"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            client_id = data.get('ClientId')
            
            if not client_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Харилцагчийн ID олдсонгүй'
                })
            
            client = get_object_or_404(RefClient, pk=client_id)
            form = Ref_Client_BankForm(data, client_id=client_id)
            
            if form.is_valid():
                bank = form.save(commit=False)
                bank.ClientId = client
                bank.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Банкны мэдээлэл амжилттай нэмэгдлээ',
                    'bank': {
                        'ClientBankId': bank.ClientBankId,
                        'BankName': bank.BankName,
                        'BankAccount': bank.BankAccount,
                        'IsActive': bank.IsActive
                    }
                })
            else:
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = error_list[0] if error_list else ''
                return JsonResponse({
                    'success': False,
                    'message': 'Баталгаажуулалт амжилтгүй',
                    'errors': errors
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Алдаа гарлаа: {str(e)}'
            })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Зөвхөн POST хүсэлт хүлээн авах боломжтой'
        })


@login_required
@permission_required('core.change_refclient', raise_exception=True)
def client_bank_update(request, pk):
    """AJAX view to update existing bank account"""
    bank = get_object_or_404(Ref_Client_Bank, pk=pk)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            form = Ref_Client_BankForm(data, instance=bank, client_id=bank.ClientId.ClientId)
            
            if form.is_valid():
                bank = form.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Банкны мэдээлэл амжилттай шинэчлэгдлээ',
                    'bank': {
                        'ClientBankId': bank.ClientBankId,
                        'BankName': bank.BankName,
                        'BankAccount': bank.BankAccount,
                        'IsActive': bank.IsActive
                    }
                })
            else:
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = error_list[0] if error_list else ''
                return JsonResponse({
                    'success': False,
                    'message': 'Баталгаажуулалт амжилтгүй',
                    'errors': errors
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Алдаа гарлаа: {str(e)}'
            })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Зөвхөн POST хүсэлт хүлээн авах боломжтой'
        })


@login_required
@permission_required('core.delete_refclient', raise_exception=True)
def client_bank_delete(request, pk):
    """AJAX view to delete bank account (soft delete by setting IsActive=False)"""
    bank = get_object_or_404(Ref_Client_Bank, pk=pk)
    
    if request.method == 'POST':
        try:
            bank.IsActive = False
            bank.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Банкны мэдээлэл амжилттай устгагдлаа'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Алдаа гарлаа: {str(e)}'
            })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Зөвхөн POST хүсэлт хүлээн авах боломжтой'
        })


# RefClientType Views


# Template views removed
@login_required
@permission_required('core.view_refinventory', raise_exception=True)
def refinventory_list(request):
    """List all inventory items with pagination and inline filtering"""
    inventory_list = RefInventory.objects.filter(IsDelete=False)
    
    # Check if this is a modal request for inventory selection
    is_modal = request.GET.get('modal') == 'true'
    is_select_mode = request.GET.get('select_mode') == 'true'
    
    # Apply filters
    code_filter = request.GET.get('code', '')
    name_filter = request.GET.get('name', '')
    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    
    if code_filter:
        inventory_list = inventory_list.filter(InventoryCode__icontains=code_filter)
    
    if name_filter:
        inventory_list = inventory_list.filter(InventoryName__icontains=name_filter)
    
    if type_filter:
        # Filter by InventoryTypeId - try to match by name if it's a related field
        inventory_list = inventory_list.filter(InventoryTypeId__InventoryTypeName__icontains=type_filter)
    
    if status_filter:
        if status_filter == 'y':
            inventory_list = inventory_list.filter(IsActive=True)
        elif status_filter == 'n':
            inventory_list = inventory_list.filter(IsActive=False)
    
    # Order by name
    inventory_list = inventory_list.order_by('InventoryName')
    
    # Get page size from request, default to 15
    page_size = request.GET.get('page_size', '15')
    try:
        page_size = int(page_size)
        # Validate page size (allow 10, 15, 20, 25, 50)
        if page_size not in [10, 15, 20, 25, 50]:
            page_size = 15
    except (ValueError, TypeError):
        page_size = 15
    
    # For modal/select mode, show more items and no pagination
    if is_modal or is_select_mode:
        inventories = inventory_list
        paginator = None
    else:
        # Pagination
        paginator = Paginator(inventory_list, page_size)
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
        'page_size': page_size,
        'code_filter': code_filter,
        'name_filter': name_filter,
        'type_filter': type_filter,
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
            
            # Check if this is an AJAX request from modal
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Inventory item created successfully!',
                    'inventory': {
                        'InventoryId': inventory.InventoryId,
                        'InventoryCode': inventory.InventoryCode,
                        'InventoryName': inventory.InventoryName,
                        'InventoryTypeId': inventory.InventoryTypeId.InventoryTypeId if inventory.InventoryTypeId else None,
                        'InventoryTypeName': inventory.InventoryTypeId.InventoryTypeName if inventory.InventoryTypeId else None,
                        'MeasurementId': inventory.MeasurementId.MeasurementId if inventory.MeasurementId else None,
                        'MeasurementName': inventory.MeasurementId.MeasurementName if inventory.MeasurementId else None,
                        'UnitCost': str(inventory.UnitCost) if inventory.UnitCost else None,
                        'UnitPrice': str(inventory.UnitPrice) if inventory.UnitPrice else None,
                        'IsActive': inventory.IsActive
                    }
                })
            
            messages.success(request, 'Inventory item created successfully.')
            return redirect('core:refinventory_list')
        else:
            # Check if this is an AJAX request from modal
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Validation failed',
                    'errors': form.errors
                }, status=400)
    else:
        form = RefInventoryForm()
    
    return render(request, 'core/refinventory_form.html', {'form': form, 'title': 'Бараа материал нэмэх'})


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
            
            # Check if this is an AJAX request from modal
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Inventory item updated successfully!',
                    'inventory': {
                        'InventoryId': inventory.InventoryId,
                        'InventoryCode': inventory.InventoryCode,
                        'InventoryName': inventory.InventoryName,
                        'InventoryTypeId': inventory.InventoryTypeId.InventoryTypeId if inventory.InventoryTypeId else None,
                        'InventoryTypeName': inventory.InventoryTypeId.InventoryTypeName if inventory.InventoryTypeId else None,
                        'MeasurementId': inventory.MeasurementId.MeasurementId if inventory.MeasurementId else None,
                        'MeasurementName': inventory.MeasurementId.MeasurementName if inventory.MeasurementId else None,
                        'UnitCost': str(inventory.UnitCost) if inventory.UnitCost else None,
                        'UnitPrice': str(inventory.UnitPrice) if inventory.UnitPrice else None,
                        'IsActive': inventory.IsActive
                    }
                })
            
            messages.success(request, 'Inventory item updated successfully.')
            return redirect('core:refinventory_list')
        else:
            # Check if this is an AJAX request from modal
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Validation failed',
                    'errors': form.errors
                }, status=400)
    else:
        form = RefInventoryForm(instance=inventory)
    
    return render(request, 'core/refinventory_form.html', {
        'form': form, 
        'title': 'Бараа материал шинэчлэх',
        'inventory': inventory
    })


@login_required
@permission_required('core.delete_refinventory', raise_exception=True)
def refinventory_delete(request, pk):
    """Delete inventory item with soft delete"""
    inventory = get_object_or_404(RefInventory, pk=pk)
    
    # Check if this is a modal request
    if request.GET.get('modal'):
        # Return modal content
        return render(request, 'core/components/delete_modal.html', {
            'item_name': f"{inventory.InventoryCode or ''} - {inventory.InventoryName}".strip(' - '),
            'delete_url': reverse('core:refinventory_delete', args=[pk])
        })
    
    # Handle API request (JSON)
    if request.method == 'POST' and request.headers.get('Content-Type') == 'application/json':
        try:
            import json
            data = json.loads(request.body)
            
            # Check if already deleted
            if inventory.IsDelete:
                return JsonResponse({
                    'success': False,
                    'message': f'Inventory item "{inventory.InventoryName}" is already deleted.'
                })
            
            # Check if inventory exists in inv_document_item table
            if Inv_Document_Item.objects.filter(InventoryId=inventory).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Тухайн материал эхний үлдэгдэлтэй эсвэл гүйлгээ хийгдсэн байна. Эхний үлдэгдэлгүй эсвэл гүйлгээ хийгдээгүй бол усгтах боломжтой'
                })
            
            # Check if inventory exists in inv_beginning_balance table (non-deleted records)
            if Inv_Beginning_Balance.objects.filter(InventoryId=inventory, IsDelete=False).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Тухайн материал эхний үлдэгдэлтэй эсвэл гүйлгээ хийгдсэн байна. Эхний үлдэгдэлгүй эсвэл гүйлгээ хийгдээгүй бол усгтах боломжтой'
                })
            
            # Perform soft delete
            inventory.IsDelete = True
            if hasattr(inventory, 'ModifiedBy'):
                inventory.ModifiedBy = request.user
            inventory.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Inventory item "{inventory.InventoryName}" has been deleted successfully.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error deleting inventory item: {str(e)}'
            })
    
    # Handle regular form POST
    if request.method == 'POST':
        try:
            # Check if already deleted
            if inventory.IsDelete:
                messages.warning(request, f'Inventory item "{inventory.InventoryName}" is already deleted.')
                return redirect('core:refinventory_list')
            
            # Check if inventory exists in inv_document_item table
            if Inv_Document_Item.objects.filter(InventoryId=inventory).exists():
                messages.error(request, 'Тухайн материал эхний үлдэгдэлтэй эсвэл гүйлгээ хийгдсэн байна. Эхний үлдэгдэлгүй эсвэл гүйлгээ хийгдээгүй бол усгтах боломжтой')
                return redirect('core:refinventory_list')
            
            # Check if inventory exists in inv_beginning_balance table (non-deleted records)
            if Inv_Beginning_Balance.objects.filter(InventoryId=inventory, IsDelete=False).exists():
                messages.error(request, 'Тухайн материал эхний үлдэгдэлтэй эсвэл гүйлгээ хийгдсэн байна. Эхний үлдэгдэлгүй эсвэл гүйлгээ хийгдээгүй бол усгтах боломжтой')
                return redirect('core:refinventory_list')
            
            # Perform soft delete
            inventory.IsDelete = True
            if hasattr(inventory, 'ModifiedBy'):
                inventory.ModifiedBy = request.user
            inventory.save()
            messages.success(request, f'Inventory item "{inventory.InventoryName}" has been deleted successfully.')
        except ProtectedError as e:
            messages.error(request, f'Cannot delete inventory item "{inventory.InventoryName}" because it is referenced by other records. Please remove all references first.')
        return redirect('core:refinventory_list')
    
    context = {
        'inventory': inventory,
        'item_name': f"{inventory.InventoryCode or ''} - {inventory.InventoryName}".strip(' - '),
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
        selected_document = request.GET.get('selected_document', '')
        
        # Base query - only non-deleted records
        documents_query = Cash_Document.objects.select_related(
            'AccountId', 'ClientId', 'CurrencyId', 'DocumentTypeId', 'TemplateId', 'CreatedBy'
        ).filter(IsDelete=False)
        
        # If selected_document is provided, filter to only that document
        # This is more efficient than fetching all documents and filtering on frontend
        if selected_document and selected_document.strip():
            try:
                document_id = int(selected_document)
                # Filter by document ID - this takes priority over date range
                documents_query = documents_query.filter(DocumentId=document_id)
                # When filtering by specific document, skip date range filter
                # (we want to show the document even if it's outside the date range)
                start_date = ''  # Clear date filters
                end_date = ''
            except (ValueError, TypeError):
                # Invalid document ID, return empty result
                documents_query = documents_query.none()
        
        # Apply date range filter (only if not filtering by specific document)
        if not (selected_document and selected_document.strip()):
            if start_date:
                documents_query = documents_query.filter(DocumentDate__gte=start_date)
            if end_date:
                documents_query = documents_query.filter(DocumentDate__lte=end_date)
        
        # Order by document ID (newest first)
        documents_query = documents_query.order_by('-DocumentId')
        
        # Build response data
        documents_data = []
        for doc in documents_query:
            documents_data.append({
                'DocumentId': doc.DocumentId,
                'DocumentNo': doc.DocumentNo,
                'DocumentTypeId': doc.DocumentTypeId.DocumentTypeId if doc.DocumentTypeId else None,
                'DocumentTypeCode': doc.DocumentTypeId.DocumentTypeCode if doc.DocumentTypeId else '',
                'DocumentTypeName': doc.DocumentTypeId.Description if doc.DocumentTypeId else '',
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
                'ClientBankId': doc.ClientBankId.ClientBankId if doc.ClientBankId else None,
                'BankAccount': doc.ClientBankId.BankAccount if doc.ClientBankId else '',
                'BankName': doc.ClientBankId.BankName if doc.ClientBankId else '',
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
            'message': 'Тухайн сар түгжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.' if is_locked else ''
        })
        
    except:
        return JsonResponse({'is_locked': False})


@login_required
@require_http_methods(["GET"])
def api_validate_period_dates(request):
    """API endpoint to validate that dates match a period from ref_period table"""
    from datetime import datetime
    from calendar import monthrange
    from .models import Ref_Period
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if not start_date_str or not end_date_str:
        return JsonResponse({
            'success': False,
            'message': 'Both start_date and end_date are required'
        }, status=400)
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Check if start date is first day of month
        is_first_day = start_date.day == 1
        
        # Check if end date is last day of month
        last_day = monthrange(end_date.year, end_date.month)[1]
        is_last_day = end_date.day == last_day
        
        # Check if dates are in the same month
        same_month = (start_date.year == end_date.year and 
                     start_date.month == end_date.month)
        
        if not is_first_day or not is_last_day or not same_month:
            # Try to find period that contains end_date
            period = Ref_Period.objects.filter(
                BeginDate__lte=end_date,
                EndDate__gte=end_date
            ).first()
            
            if period:
                # Return adjusted dates
                return JsonResponse({
                    'success': True,
                    'adjusted': True,
                    'adjusted_start': period.BeginDate.strftime('%Y-%m-%d'),
                    'adjusted_end': period.EndDate.strftime('%Y-%m-%d'),
                    'period': {
                        'period_id': period.PeriodId,
                        'period_name': period.PeriodName,
                        'begin_date': period.BeginDate.strftime('%Y-%m-%d'),
                        'end_date': period.EndDate.strftime('%Y-%m-%d'),
                        'is_locked': period.IsLock
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Dates do not match a period. Start date must be first day of month and end date must be last day of month. No period found for the selected date.'
                }, status=400)
        
        # Dates look correct, verify against period table
        period = Ref_Period.objects.filter(
            BeginDate=start_date,
            EndDate=end_date
        ).first()
        
        if not period:
            # Try to find period that contains end_date
            period = Ref_Period.objects.filter(
                BeginDate__lte=end_date,
                EndDate__gte=end_date
            ).first()
            
            if period:
                # Return adjusted dates
                return JsonResponse({
                    'success': True,
                    'adjusted': True,
                    'adjusted_start': period.BeginDate.strftime('%Y-%m-%d'),
                    'adjusted_end': period.EndDate.strftime('%Y-%m-%d'),
                    'period': {
                        'period_id': period.PeriodId,
                        'period_name': period.PeriodName,
                        'begin_date': period.BeginDate.strftime('%Y-%m-%d'),
                        'end_date': period.EndDate.strftime('%Y-%m-%d'),
                        'is_locked': period.IsLock
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No period found in ref_period table for the selected dates'
                }, status=400)
        
        # Period found and dates match
        return JsonResponse({
            'success': True,
            'adjusted': False,
            'period': {
                'period_id': period.PeriodId,
                'period_name': period.PeriodName,
                'begin_date': period.BeginDate.strftime('%Y-%m-%d'),
                'end_date': period.EndDate.strftime('%Y-%m-%d'),
                'is_locked': period.IsLock
            }
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid date format. Please use YYYY-MM-DD format.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error validating period: {str(e)}'
        }, status=500)


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


def _get_form_error_message(form):
    for field, errors in form.errors.items():
        if errors:
            return errors[0]
    return 'Формын шалгалтын алдаа гарлаа.'


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
            
            form = CashDocumentForm(request.POST)
            if form.is_valid():
                try:
                    cash_document = form.save(commit=False)
                    
                    # Check period lock (server-side validation)
                    if Ref_Period.objects.filter(IsLock=True, BeginDate__lte=cash_document.DocumentDate, EndDate__gte=cash_document.DocumentDate).exists():
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            # AJAX request - return JSON for modal
                            return JsonResponse({
                                'success': False,
                                'error': 'Тухайн сар түгжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.'
                            })
                        else:
                            # Regular form submission - show Django message
                            messages.error(request, 'Тухайн сар түгжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.')
                            form = CashDocumentForm(request.POST)
                            vat_accounts = {}
                            try:
                                from .models import Ref_Constant, Ref_Account
                                vat_sale = Ref_Constant.objects.filter(ConstantName='VAT_Sale').first()
                                vat_purchase = Ref_Constant.objects.filter(ConstantName='VAT_Purchase').first()
                                if vat_sale:
                                    vat_sale_account = Ref_Account.objects.filter(AccountId=vat_sale.ConstantName).first()
                                    vat_accounts['vat_sale_code'] = vat_sale_account.AccountCode if vat_sale_account else ''
                                if vat_purchase:
                                    vat_purchase_account = Ref_Account.objects.filter(AccountId=vat_purchase.ConstantName).first()
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
                            'redirect_url': '/core/cashdocuments/'
                        })
                    
                    return redirect('/core/cashdocuments/')
                except UnicodeEncodeError as e:
                    messages.error(request, f'Unicode encoding error: {str(e)}. Please check your input for special characters.')
                except Exception as e:
                    messages.error(request, f'Error creating cash document: {str(e)}')
            else:
                # Handle form validation errors
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': _get_form_error_message(form)
                    }, status=400)
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
        vat_constant_9 = Ref_Constant.objects.get(ConstantID=9)   # Receivable VAT
        vat_constant_10 = Ref_Constant.objects.get(ConstantID=10) # Payable VAT
        
        # Convert ConstantName to integer to get AccountId
        receivable_vat_account_id = int(vat_constant_9.ConstantName)   # Receivable (ConstantID=9)
        payable_vat_account_id = int(vat_constant_10.ConstantName)    # Payable (ConstantID=10)
        
        # Get actual account objects to retrieve account codes
        receivable_vat_account = Ref_Account.objects.get(AccountId=receivable_vat_account_id)
        payable_vat_account = Ref_Account.objects.get(AccountId=payable_vat_account_id)
        
        vat_accounts = {
            'vat_account_1_id': payable_vat_account_id,      # Payable VAT (ConstantID=10)
            'vat_account_2_id': receivable_vat_account_id,   # Receivable VAT (ConstantID=9)
            'vat_account_1_display': payable_vat_account.AccountCode,
            'vat_account_2_display': receivable_vat_account.AccountCode,
        }
    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
        # Fallback values
        vat_accounts = {
            'vat_account_1_id': 8,  # Payable VAT fallback
            'vat_account_2_id': 9,  # Receivable VAT fallback
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
                        'error': 'Тухайн сар түгжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.'
                    })
                else:
                    # Regular form submission - show Django message
                    messages.error(request, 'Тухайн сар түгжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.')
                    form = CashDocumentForm(request.POST, instance=document)
                    vat_accounts = {}
                    try:
                        from .models import Ref_Constant, Ref_Account
                        vat_sale = Ref_Constant.objects.filter(ConstantName='VAT_Sale').first()
                        vat_purchase = Ref_Constant.objects.filter(ConstantName='VAT_Purchase').first()
                        if vat_sale:
                            vat_sale_account = Ref_Account.objects.filter(AccountId=vat_sale.ConstantName).first()
                            vat_accounts['vat_sale_code'] = vat_sale_account.AccountCode if vat_sale_account else ''
                        if vat_purchase:
                            vat_purchase_account = Ref_Account.objects.filter(AccountId=vat_purchase.ConstantName).first()
                            vat_accounts['vat_purchase_code'] = vat_purchase_account.AccountCode if vat_purchase_account else ''
                    except:
                        pass
                    return render(request, 'core/cashdocument_form.html', {
                        'form': form,
                        'item': document,
                        'vat_accounts': vat_accounts,
                        'timestamp': int(time.time())
                    })
            
            deleted_count = 0
            with transaction.atomic():
                cash_document.ModifiedBy = request.user
                cash_document.save()
                deleted_count, _ = Cash_DocumentDetail.objects.filter(
                    DocumentId=cash_document
                ).delete()
            
            if deleted_count:
                message_text = f"Cash document updated successfully. {deleted_count} detail record{'s' if deleted_count != 1 else ''} cleared."
            else:
                message_text = 'Cash document updated successfully. No detail records were associated with this document.'
            messages.success(request, message_text)
            
            # Check if AJAX request and return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': f'/core/cashdocuments/?selected_document={pk}',
                    'deleted_details': deleted_count
                })
            
            # Redirect to master detail page
            return redirect(f'/core/cashdocuments/?selected_document={pk}')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': _get_form_error_message(form)
                }, status=400)
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
                    'error': 'Тухайн сар түгжигдсэн байна. Засварлах боломжгүй. Админы зөвшөөрлөөр эрх нээгдэнэ.',
                    'redirect': True
                })
            else:
                # Regular request - show Django message and redirect
                messages.error(request, 'Тухайн сар түгжигдсэн байна. Засварлах боломжгүй. Админы зөвшөөрлөөр эрх нээгдэнэ.')
                return redirect('core:cashdocument_master_detail')
        
        form = CashDocumentForm(instance=document)
    
    # Get VAT account IDs from ref_constant table and fetch actual account codes
    vat_accounts = {}
    try:
        from .models import Ref_Constant, Ref_Account
        vat_constant_9 = Ref_Constant.objects.get(ConstantID=9)   # Receivable VAT
        vat_constant_10 = Ref_Constant.objects.get(ConstantID=10) # Payable VAT
        
        # Convert ConstantName to integer to get AccountId
        receivable_vat_account_id = int(vat_constant_9.ConstantName)   # Receivable (ConstantID=9)
        payable_vat_account_id = int(vat_constant_10.ConstantName)    # Payable (ConstantID=10)
        
        # Get actual account objects to retrieve account codes
        receivable_vat_account = Ref_Account.objects.get(AccountId=receivable_vat_account_id)
        payable_vat_account = Ref_Account.objects.get(AccountId=payable_vat_account_id)
        
        vat_accounts = {
            'vat_account_1_id': payable_vat_account_id,      # Payable VAT (ConstantID=10)
            'vat_account_2_id': receivable_vat_account_id,   # Receivable VAT (ConstantID=9)
            'vat_account_1_display': payable_vat_account.AccountCode,
            'vat_account_2_display': receivable_vat_account.AccountCode,
        }
    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
        # Fallback values
        vat_accounts = {
            'vat_account_1_id': 8,  # Payable VAT fallback
            'vat_account_2_id': 9,  # Receivable VAT fallback
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
    
    # Delete all existing details when accessing via GET (Manage Detail button clicked)
    if request.method == 'GET':
        existing_details = Cash_DocumentDetail.objects.filter(DocumentId=document)
        deleted_count = existing_details.count()
        if deleted_count > 0:
            existing_details.delete()
            print(f"Deleted {deleted_count} existing detail records for document {document.DocumentId}")
    
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
            
        except (Ref_Constant.DoesNotExist, ValueError, AttributeError) as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'VAT constant lookup failed: {e}. Using fallback VAT rate.')
            vat_percent = 10.0  # Default fallback
            # Still calculate VAT amount with fallback rate
            total_amount = float(document.CurrencyAmount * document.CurrencyExchange)
            vat_amount = (total_amount * vat_percent) / (100 + vat_percent)
    
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
            
            document_items = Inv_Document_Item.objects.select_related('InventoryId__MeasurementId').filter(
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
                        'error': 'Тухайн сар түгжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.'
                    })
                else:
                    messages.error(request, 'Тухайн сар түгжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.')
                    # Get required context data for re-rendering
                    inventory_account_types = Ref_Account_Type.objects.filter(
                        AccountTypeId__in=[8, 9, 10, 11], 
                        IsActive=True
                    ).order_by('AccountTypeId')
                    
                    vat_accounts = {}
                    try:
                        from .models import Ref_Constant, Ref_Account
                        vat_constant_9 = Ref_Constant.objects.get(ConstantID=9)   # Receivable VAT
                        vat_constant_10 = Ref_Constant.objects.get(ConstantID=10) # Payable VAT
                        
                        # Convert ConstantName to integer to get AccountId
                        receivable_vat_account_id = int(vat_constant_9.ConstantName)   # Receivable (ConstantID=9)
                        payable_vat_account_id = int(vat_constant_10.ConstantName)    # Payable (ConstantID=10)
                        
                        # Get actual account objects to retrieve account codes
                        receivable_vat_account = Ref_Account.objects.get(AccountId=receivable_vat_account_id)
                        payable_vat_account = Ref_Account.objects.get(AccountId=payable_vat_account_id)
                        
                        vat_accounts = {
                            'vat_account_1_id': payable_vat_account_id,      # Payable VAT (ConstantID=10)
                            'vat_account_2_id': receivable_vat_account_id,   # Receivable VAT (ConstantID=9)
                            'vat_account_1_display': payable_vat_account.AccountCode,
                            'vat_account_2_display': receivable_vat_account.AccountCode,
                        }
                    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
                        vat_accounts = {
                            'vat_account_1_id': 8,  # Payable VAT fallback
                            'vat_account_2_id': 9,  # Receivable VAT fallback
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
        vat_constant_9 = Ref_Constant.objects.get(ConstantID=9)   # Receivable VAT
        vat_constant_10 = Ref_Constant.objects.get(ConstantID=10) # Payable VAT
        
        # Convert ConstantName to integer to get AccountId
        receivable_vat_account_id = int(vat_constant_9.ConstantName)   # Receivable (ConstantID=9)
        payable_vat_account_id = int(vat_constant_10.ConstantName)    # Payable (ConstantID=10)
        
        # Get actual account objects to retrieve account codes
        receivable_vat_account = Ref_Account.objects.get(AccountId=receivable_vat_account_id)
        payable_vat_account = Ref_Account.objects.get(AccountId=payable_vat_account_id)
        
        vat_accounts = {
            'vat_account_1_id': payable_vat_account_id,      # Payable VAT (ConstantID=10)
            'vat_account_2_id': receivable_vat_account_id,   # Receivable VAT (ConstantID=9)
            'vat_account_1_display': payable_vat_account.AccountCode,
            'vat_account_2_display': receivable_vat_account.AccountCode,
        }
    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
        # Fallback values
        vat_accounts = {
            'vat_account_1_id': 8,  # Payable VAT fallback
            'vat_account_2_id': 9,  # Receivable VAT fallback
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
                        'error': 'Тухайн сар түгжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.'
                    })
                else:
                    messages.error(request, 'Тухайн сар түгжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.')
                    # Get required context data for re-rendering
                    inventory_account_types = Ref_Account_Type.objects.filter(
                        AccountTypeId__in=[8, 9, 10, 11], 
                        IsActive=True
                    ).order_by('AccountTypeId')
                    
                    vat_accounts = {}
                    try:
                        from .models import Ref_Constant, Ref_Account
                        vat_constant_9 = Ref_Constant.objects.get(ConstantID=9)   # Receivable VAT
                        vat_constant_10 = Ref_Constant.objects.get(ConstantID=10) # Payable VAT
                        
                        # Convert ConstantName to integer to get AccountId
                        receivable_vat_account_id = int(vat_constant_9.ConstantName)   # Receivable (ConstantID=9)
                        payable_vat_account_id = int(vat_constant_10.ConstantName)    # Payable (ConstantID=10)
                        
                        # Get actual account objects to retrieve account codes
                        receivable_vat_account = Ref_Account.objects.get(AccountId=receivable_vat_account_id)
                        payable_vat_account = Ref_Account.objects.get(AccountId=payable_vat_account_id)
                        
                        vat_accounts = {
                            'vat_account_1_id': payable_vat_account_id,      # Payable VAT (ConstantID=10)
                            'vat_account_2_id': receivable_vat_account_id,   # Receivable VAT (ConstantID=9)
                            'vat_account_1_display': payable_vat_account.AccountCode,
                            'vat_account_2_display': receivable_vat_account.AccountCode,
                        }
                    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
                        vat_accounts = {
                            'vat_account_1_id': 8,  # Payable VAT fallback
                            'vat_account_2_id': 9,  # Receivable VAT fallback
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
                    'error': 'Тухайн сар түгжигдсэн байна. Засварлах боломжгүй. Админы зөвшөөрлөөр эрх нээгдэнэ.',
                    'redirect': True
                })
            else:
                messages.error(request, 'Тухайн сар түгжигдсэн байна. Засварлах боломжгүй. Админы зөвшөөрлөөр эрх нээгдэнэ.')
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
        vat_constant_9 = Ref_Constant.objects.get(ConstantID=9)   # Receivable VAT
        vat_constant_10 = Ref_Constant.objects.get(ConstantID=10) # Payable VAT
        
        # Convert ConstantName to integer to get AccountId
        receivable_vat_account_id = int(vat_constant_9.ConstantName)   # Receivable (ConstantID=9)
        payable_vat_account_id = int(vat_constant_10.ConstantName)    # Payable (ConstantID=10)
        
        # Get actual account objects to retrieve account codes
        receivable_vat_account = Ref_Account.objects.get(AccountId=receivable_vat_account_id)
        payable_vat_account = Ref_Account.objects.get(AccountId=payable_vat_account_id)
        
        vat_accounts = {
            'vat_account_1_id': payable_vat_account_id,      # Payable VAT (ConstantID=10)
            'vat_account_2_id': receivable_vat_account_id,   # Receivable VAT (ConstantID=9)
            'vat_account_1_display': payable_vat_account.AccountCode,
            'vat_account_2_display': receivable_vat_account.AccountCode,
        }
    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
        # Fallback values
        vat_accounts = {
            'vat_account_1_id': 8,  # Payable VAT fallback
            'vat_account_2_id': 9,  # Receivable VAT fallback
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
    document_items = Inv_Document_Item.objects.select_related('InventoryId__MeasurementId').filter(
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
def asset_master_detail(request):
    """Redirect to ref_asset_card_list which now includes master-detail functionality"""
    # Preserve query parameters when redirecting
    query_params = request.GET.urlencode()
    redirect_url = reverse('core:ref_asset_card_list')
    if query_params:
        redirect_url += '?' + query_params
    return redirect(redirect_url)


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
            return redirect('core:ref_asset_card_list')
    else:
        form = RefAssetForm()
    
    return render(request, 'core/refasset_form.html', {
        'form': form,
        'title': 'Үндсэн хөрөнгө нэмэх'
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
            return redirect('core:ref_asset_card_list')
    else:
        form = RefAssetForm(instance=asset)
    
    return render(request, 'core/refasset_form.html', {
        'form': form,
        'title': 'Үндсэн хөрөнгө шинэчлэх',
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
        return redirect('core:ref_asset_card_list')
    
    # GET request without modal parameter - redirect to list
    return redirect('core:ref_asset_card_list')


@login_required
@permission_required('core.view_ref_asset_card', raise_exception=True)
def ref_asset_card_list(request):
    """List all asset cards with filtering and pagination - Master-Detail view"""
    # Get filter parameters for assets (master table)
    selected_asset_type_id = request.GET.get('asset_type', '')
    selected_asset_id = request.GET.get('selected_asset', '')
    asset_page = request.GET.get('asset_page', 1)
    
    # Get filter parameters for asset cards (detail table)
    asset_filter = request.GET.get('asset', '')
    asset_code_filter = request.GET.get('asset_code', '')
    asset_name_filter = request.GET.get('asset_name', '')
    status_filter = request.GET.get('status', '')
    card_page = request.GET.get('page', 1)
    
    # Get all asset types for dropdown filter
    asset_types = Ref_Asset_Type.objects.filter(IsActive=True).order_by('AssetTypeName')
    
    # Get all assets with related data (for master table)
    assets = RefAsset.objects.select_related('AssetTypeId', 'CreatedBy', 'ModifiedBy').order_by('AssetCode')
    
    # Apply asset type filter if provided
    if selected_asset_type_id:
        assets = assets.filter(AssetTypeId__AssetTypeId=selected_asset_type_id)
    
    # Apply asset filters
    asset_code_filter_master = request.GET.get('asset_code', '')
    asset_name_filter_master = request.GET.get('asset_name', '')
    status_filter_master = request.GET.get('status', '')
    
    if asset_code_filter_master:
        assets = assets.filter(AssetCode__icontains=asset_code_filter_master)
    
    if asset_name_filter_master:
        assets = assets.filter(AssetName__icontains=asset_name_filter_master)
    
    if status_filter_master:
        if status_filter_master == 'active':
            assets = assets.filter(IsDelete=False)
        elif status_filter_master == 'inactive':
            assets = assets.filter(IsDelete=True)
    
    # Pagination for assets (master table)
    asset_paginator = Paginator(assets, 20)  # Show 20 assets per page
    try:
        assets = asset_paginator.page(asset_page)
    except PageNotAnInteger:
        assets = asset_paginator.page(1)
    except EmptyPage:
        assets = asset_paginator.page(asset_paginator.num_pages)
    
    # Get selected asset
    selected_asset = None
    if selected_asset_id:
        try:
            selected_asset = RefAsset.objects.select_related('AssetTypeId', 'CreatedBy', 'ModifiedBy').get(AssetId=selected_asset_id)
        except RefAsset.DoesNotExist:
            selected_asset = None
    
    # Get all asset cards with related data (for detail table)
    asset_cards = Ref_Asset_Card.objects.select_related('AssetId', 'ClientId', 'CreatedBy', 'ModifiedBy').order_by('AssetCardId')
    
    # Filter asset cards by selected asset if provided
    if selected_asset_id:
        asset_cards = asset_cards.filter(AssetId__AssetId=selected_asset_id)
    elif asset_filter:
        # Fallback to old asset filter if selected_asset not provided
        asset_cards = asset_cards.filter(AssetId__AssetId=asset_filter)
    
    # Apply asset card filters
    card_code_filter = request.GET.get('card_code', '')
    card_name_filter = request.GET.get('card_name', '')
    
    if card_code_filter:
        asset_cards = asset_cards.filter(AssetCardCode__icontains=card_code_filter)
    
    if card_name_filter:
        asset_cards = asset_cards.filter(AssetCardName__icontains=card_name_filter)
    
    if status_filter:
        if status_filter == 'active':
            asset_cards = asset_cards.filter(IsDelete=False)
        elif status_filter == 'inactive':
            asset_cards = asset_cards.filter(IsDelete=True)
    
    # Get page size from request, default to 15
    page_size = request.GET.get('page_size', '15')
    try:
        page_size = int(page_size)
        # Validate page size (allow 10, 15, 20, 25, 50)
        if page_size not in [10, 15, 20, 25, 50]:
            page_size = 15
    except (ValueError, TypeError):
        page_size = 15
    
    # For modal requests, show more items and no pagination
    is_modal = request.GET.get('modal')
    if is_modal:
        card_paginator = None
    else:
        # Pagination for asset cards (detail table)
        card_paginator = Paginator(asset_cards, page_size)
        try:
            asset_cards = card_paginator.page(card_page)
        except PageNotAnInteger:
            asset_cards = card_paginator.page(1)
        except EmptyPage:
            asset_cards = card_paginator.page(card_paginator.num_pages)
    
    # Get all assets for dropdown filter (for asset card filters)
    all_assets = RefAsset.objects.filter(IsDelete=False).order_by('AssetName')
    
    # Check if this is a modal request
    if is_modal:
        return render(request, 'core/refassetcard_list.html', {
            'asset_cards': asset_cards,
            'assets': all_assets,
            'filters': {
                'asset': asset_filter,
                'asset_code': asset_code_filter,
                'asset_name': asset_name_filter,
                'status': status_filter,
            },
            'paginator': card_paginator,
            'is_modal': True
        })
    
    return render(request, 'core/refassetcard_list.html', {
        'asset_cards': asset_cards,
        'assets': all_assets,  # For dropdown filter
        'master_assets': assets,  # For master table
        'asset_types': asset_types,
        'selected_asset_type_id': selected_asset_type_id,
        'selected_asset': selected_asset,
        'selected_asset_id': selected_asset_id,
        'asset_paginator': asset_paginator,
        'filters': {
            'asset': asset_filter,
            'asset_code': asset_code_filter_master,
            'asset_name': asset_name_filter_master,
            'card_code': card_code_filter,
            'card_name': card_name_filter,
            'status': status_filter_master,
        },
        'paginator': card_paginator,
        'page_size': page_size,
        'is_modal': False
    })
@login_required
@permission_required('core.add_ref_asset_card', raise_exception=True)
def ref_asset_card_create(request):
    """Create a new asset card"""
    selected_asset_id = request.GET.get('selected_asset', '')
    selected_asset = None
    
    if selected_asset_id:
        try:
            selected_asset = RefAsset.objects.get(AssetId=selected_asset_id, IsDelete=False)
        except RefAsset.DoesNotExist:
            selected_asset = None
    
    if request.method == 'POST':
        form = Ref_Asset_CardForm(request.POST)
        if form.is_valid():
            asset_card = form.save(commit=False)
            
            # Check if AssetCardCode already exists (since it's unique)
            existing_asset_card = Ref_Asset_Card.objects.filter(AssetCardCode=asset_card.AssetCardCode).first()
            if existing_asset_card:
                # AssetCardCode already exists, prevent creation
                error_message = "Энэ хөрөнгийн эхний үлдэгдэл оруулсан эсвэл гүйлгээ хийсэн байна."
                
                # Check if this is an AJAX request (from modal)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': error_message,
                        'errors': {'AssetCardCode': [error_message]}
                    }, status=400)
                else:
                    form.add_error('AssetCardCode', error_message)
                    return render(request, 'core/refassetcard_form.html', {
                        'form': form,
                        'title': 'Үндсэн хөрөнгийн карт нэмэх',
                        'selected_asset': selected_asset,
                        'selected_asset_id': selected_asset_id
                    })
            
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
                return redirect('core:ref_asset_card_list')
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
        # Pre-populate AssetId if selected_asset is provided
        if selected_asset:
            form.fields['AssetId'].initial = selected_asset.AssetId
    
    return render(request, 'core/refassetcard_form.html', {
        'form': form,
        'title': 'Үндсэн хөрөнгийн карт нэмэх',
        'selected_asset': selected_asset,
        'selected_asset_id': selected_asset_id
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
                return redirect('core:ref_asset_card_list')
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
        'title': 'Үндсэн хөрөнгийн карт шинэчлэх',
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
        return redirect('core:ref_asset_card_list')
    
    # GET request without modal parameter - redirect to list
    return redirect('core:ref_asset_card_list')
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
                'title': 'МӨНГӨН ХӨРӨНГИЙН ҮЛДЭГДЭЛ',
                'subtitle': 'Manage initial cash balances for accounts',
                'page_title': 'Cash Beginning Balance Management',
                'section_name': 'Мөнгөн хөрөнгө'
            },
            'receivable': {
                'title': 'АВЛАГА,ӨГЛӨГИЙН ҮЛДЭГДЭЛ',
                'subtitle': 'Manage initial receivable balances for accounts',
                'page_title': 'Receivable Beginning Balance Management',
                'section_name': 'Авлага, өглөг'
            },
            'genledger': {
                'title': 'ЕРӨНХИЙ ДЭВТРИЙН ДАНСНЫ ҮЛДЭГДЭЛ',
                'subtitle': 'Manage initial general ledger balances for accounts',
                'page_title': 'General Ledger Beginning Balance Management',
                'section_name': 'ЕРӨНХИЙ ДЭВТЭР'
            }
        }
        
        # Get configuration for the balance type
        config = balance_configs.get(balance_type, balance_configs['cash'])
        
        # For now, we'll use the same CashBeginningBalance model for all types
        # Filter balances by AccountType based on balance_type so the initial page shows pertinent accounts
        base_qs = CashBeginningBalance.objects.select_related(
            'AccountID', 'ClientID', 'CurrencyID', 'CreatedBy', 'ModifiedBy'
        ).filter(IsDelete=False)

        if balance_type == 'cash':
            # Cash accounts: AccountTypeId in (1, 2)
            balances = base_qs.filter(
                AccountID__AccountTypeId__AccountTypeId__in=[1, 2]
            )
        elif balance_type == 'receivable':
            # Receivable and Payable accounts: AccountTypeId between 3-6 OR 42-58
            balances = base_qs.filter(
                Q(AccountID__AccountTypeId__AccountTypeId__range=(3, 6)) |
                Q(AccountID__AccountTypeId__AccountTypeId__range=(42, 58))
            )
        elif balance_type == 'genledger':
            # General ledger accounts: 33,37,38,39,40,41 OR between 59-68
            balances = base_qs.filter(
                Q(AccountID__AccountTypeId__AccountTypeId__in=[33, 37, 38, 39, 40, 41]) |
                Q(AccountID__AccountTypeId__AccountTypeId__range=(59, 68))
            )
        else:
            # Fallback to show all if an unknown balance_type is provided
            balances = base_qs

        balances = balances.order_by('-CreatedDate')
        
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
                if balance_type:
                    return redirect('core:beginningbalance_list', balance_type=balance_type)
                else:
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
            if balance_type:
                return redirect('core:beginningbalance_list', balance_type=balance_type)
            else:
                return redirect('core:cashbeginningbalance_list')
            
        except Exception as e:
            messages.error(request, f'Error creating balance: {str(e)}')
            if balance_type:
                return redirect('core:beginningbalance_list', balance_type=balance_type)
            else:
                return redirect('core:cashbeginningbalance_list')
    
    if balance_type:
        return redirect('core:beginningbalance_list', balance_type=balance_type)
    else:
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
                if balance_type:
                    return redirect('core:beginningbalance_list', balance_type=balance_type)
                else:
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
            if balance_type:
                return redirect('core:beginningbalance_list', balance_type=balance_type)
            else:
                return redirect('core:cashbeginningbalance_list')
            
        except Exception as e:
            messages.error(request, f'Error updating balance: {str(e)}')
            if balance_type:
                return redirect('core:beginningbalance_list', balance_type=balance_type)
            else:
                return redirect('core:cashbeginningbalance_list')
    
    if balance_type:
        return redirect('core:beginningbalance_list', balance_type=balance_type)
    else:
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
            if balance_type:
                return redirect('core:beginningbalance_list', balance_type=balance_type)
            else:
                return redirect('core:cashbeginningbalance_list')
            
        except Exception as e:
            messages.error(request, f'Error deleting balance: {str(e)}')
            if balance_type:
                return redirect('core:beginningbalance_list', balance_type=balance_type)
            else:
                return redirect('core:cashbeginningbalance_list')
    
    if balance_type:
        return redirect('core:beginningbalance_list', balance_type=balance_type)
    else:
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
                'title': 'БАРАА МАТЕРИАЛЫН ҮЛДЭГДЭЛ',
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
            balance.UnitPrice = unit_price,
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
@permission_required('core.view_refclient', raise_exception=True)
def api_client_lookup_by_name(request):
    """API endpoint to lookup client by name (case-insensitive exact match)"""
    try:
        client_name = request.GET.get('client_name', '').strip()
        
        if not client_name:
            return JsonResponse({
                'success': False,
                'message': 'client_name parameter is required'
            }, status=400)
        
        # Try exact match first (case-insensitive)
        client = RefClient.objects.filter(
            ClientName__iexact=client_name,
            IsDelete=False
        ).first()
        
        if client:
            return JsonResponse({
                'success': True,
                'found': True,
                'client': {
                    'ClientId': client.ClientId,
                    'ClientName': client.ClientName,
                    'ClientCode': client.ClientCode
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'found': False,
                'client': None
            })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error looking up client: {str(e)}'
        }, status=500)


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
                'title': 'ҮНДСЭН ХӨРӨНГИЙН ҮЛДЭГДЭЛ',
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
            cumulated_depreciation = request.POST.get('CumulatedDepreciation')
            client_id = request.POST.get('ClientId')
            
            print(f"DEBUG: Form data received - AccountId: {account_id}, AssetCardId: {asset_card_id}, Quantity: {quantity}, UnitCost: {unit_cost}, UnitPrice: {unit_price}, CumulatedDepreciation: {cumulated_depreciation}, ClientId: {client_id}")
            
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
                CumulatedDepreciation=cumulated_depreciation if cumulated_depreciation else 0,
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
            cumulated_depreciation = request.POST.get('CumulatedDepreciation')
            client_id = request.POST.get('ClientId')
            
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
            balance.CumulatedDepreciation = cumulated_depreciation if cumulated_depreciation else 0
            balance.ClientId_id = client_id if client_id else None
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
    
    return render(request, 'core/cashreport.html', context)


@login_required
@permission_required('core.view_cash_document', raise_exception=True)
def cash_import(request):
    """View for cash import page"""
    return render(request, 'core/cash_import.html', {})
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
        ).order_by('-DocumentId').distinct()
        
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
        
        # Get ALL cash document details for ЖУРНАЛ tab (only from non-deleted documents)
        all_details = Cash_DocumentDetail.objects.select_related(
            'DocumentId__DocumentTypeId', 'AccountId', 'ClientId', 'CurrencyId', 'DocumentId__CreatedBy', 'CashFlowId'
        ).filter(DocumentId__IsDelete=False).order_by('-DocumentId__DocumentId')
        
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
                'document_id': detail.DocumentId.DocumentId,  # Add document_id for navigation
                'document_no': detail.DocumentId.DocumentNo,
                'document_date': detail.DocumentId.DocumentDate.strftime('%Y-%m-%d'),
                'document_id': detail.DocumentId.DocumentId,
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
                'cash_flow_name': detail.CashFlowId.Description if detail.CashFlowId else '',
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


# ==================== INVENTORY JOURNAL VIEWS ====================

@login_required
@permission_required('core.view_invdocument', raise_exception=True)
def inv_documents(request):
    """View for displaying inventory documents with new template"""
    # Get inventory documents with related data (including deleted ones)
    inv_documents = Inv_Document.objects.select_related(
        'DocumentTypeId', 'ClientId', 'AccountId', 'CurrencyId', 'TemplateId'
    ).order_by('-DocumentDate')
    
    context = {
        'inv_documents': inv_documents,
    }
    
    return render(request, 'core/invreport.html', context)


@login_required
@permission_required('core.view_cashdocument', raise_exception=True)
def currency_journal(request):
    """View for displaying currency journal with cash and receivable/payable balances"""
    # Get date parameters from request (for balance calculation)
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    currency_data = []
    if start_date and end_date:
        try:
            db_alias = get_current_db()
            try:
                # Execute the currency balance function
                with connections[db_alias].cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM calculate_currency_balance(%s, %s)",
                        [start_date, end_date]
                    )
                    
                    # Get column names
                    columns = [col[0] for col in cursor.description]
                    
                    # Fetch all results
                    results = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    currency_data = [
                        dict(zip(columns, row)) for row in results
                    ]
                    
                    # Convert Decimal values to float for JSON serialization
                    from decimal import Decimal
                    for item in currency_data:
                        for key, value in item.items():
                            if isinstance(value, Decimal):
                                item[key] = float(value)
            finally:
                connections[db_alias].close()
        except Exception as e:
            currency_data = []
    
    # Convert currency_data to JSON for JavaScript
    currency_data_json = json.dumps(currency_data) if currency_data else '[]'
    
    context = {
        'currency_data': currency_data,
        'currency_data_json': currency_data_json,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'core/currency_journal_new.html', context)


@login_required
@permission_required('core.view_invdocument', raise_exception=True)
def get_inv_documents_filtered(request):
    """API endpoint to get ALL inventory documents and details for all tabs in one call"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method allowed'}, status=405)
    
    try:
        # Get filter parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        document_type_id = request.GET.get('document_type_id')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 1000))  # Large page size to get all records
        
        # Limit page size to prevent abuse
        if page_size > 2000:
            page_size = 2000
        
        # Get ALL inventory documents (both active and deleted) with related data
        # Frontend will filter by IsDelete status for different tabs
        all_documents = Inv_Document.objects.select_related(
            'DocumentTypeId', 'AccountId', 'ClientId', 'TemplateId', 'CreatedBy', 'WarehouseId'
        ).prefetch_related('document_items__InventoryId').order_by('-DocumentDate').distinct()
        
        # Apply date filtering if provided
        if start_date:
            all_documents = all_documents.filter(DocumentDate__gte=start_date)
        if end_date:
            all_documents = all_documents.filter(DocumentDate__lte=end_date)
        
        # Apply DocumentTypeId filter if provided
        if document_type_id:
            all_documents = all_documents.filter(DocumentTypeId=document_type_id)
        
        # Get ALL inventory document details for ЖУРНАЛ tab (only from non-deleted documents)
        all_details = Inv_Document_Detail.objects.select_related(
            'DocumentId__DocumentTypeId', 'AccountId', 'ClientId', 'CurrencyId', 'DocumentId__CreatedBy'
        ).filter(DocumentId__IsDelete=False).order_by('DocumentId__DocumentNo')
        
        # Apply date filtering to details if provided
        if start_date:
            all_details = all_details.filter(DocumentId__DocumentDate__gte=start_date)
        if end_date:
            all_details = all_details.filter(DocumentId__DocumentDate__lte=end_date)
        
        # Apply DocumentTypeId filter to details if provided
        if document_type_id:
            all_details = all_details.filter(DocumentId__DocumentTypeId=document_type_id)
        
        # Pre-fetch document IDs that have items or details for efficient checking
        document_ids_with_items = set(
            Inv_Document_Item.objects.filter(
                DocumentId__in=all_documents.values_list('DocumentId', flat=True)
            ).values_list('DocumentId', flat=True).distinct()
        )
        document_ids_with_details = set(
            Inv_Document_Detail.objects.filter(
                DocumentId__in=all_documents.values_list('DocumentId', flat=True)
            ).values_list('DocumentId', flat=True).distinct()
        )
        
        # Format documents data for БАРИМТ and УСТГАСАН БАРИМТ tabs
        # Create one row per document-item combination to enable item-by-item searching
        documents_data = []
        seen_documents = set()
        
        for doc in all_documents:
            # Create a unique key for this document
            doc_key = f"{doc.DocumentId}_{doc.DocumentNo}_{doc.DocumentDate}"
            
            # Skip if we've already seen this document
            if doc_key in seen_documents:
                continue
                
            seen_documents.add(doc_key)
            
            # Get document items
            document_items = doc.document_items.all()
            
            # Check if document has items or details
            has_items = doc.DocumentId in document_ids_with_items
            has_details = doc.DocumentId in document_ids_with_details
            
            # Base document data fields
            base_doc_data = {
                'DocumentId': doc.DocumentId,
                'DocumentNo': doc.DocumentNo,
                'DocumentDate': doc.DocumentDate.strftime('%Y-%m-%d'),
                'DocumentTypeId': doc.DocumentTypeId.DocumentTypeId if doc.DocumentTypeId else None,
                'DocumentTypeCode': doc.DocumentTypeId.DocumentTypeCode if doc.DocumentTypeId else '',
                'ClientName': doc.ClientId.ClientName if doc.ClientId else '',
                'AccountCode': doc.AccountId.AccountCode if doc.AccountId else '',
                'UserName': doc.CreatedBy.username if doc.CreatedBy else '',
                'IsDelete': doc.IsDelete,  # Include delete status for frontend filtering
                'HasItems': has_items,  # Flag indicating if document has items in inv_document_item
                'HasDetails': has_details,  # Flag indicating if document has details in inv_document_detail
            }
            
            # If document has items, create one row per item
            if document_items:
                for item in document_items:
                    inventory = item.InventoryId
                    quantity = float(item.Quantity) if item.Quantity else 0.0
                    unit_cost = float(item.UnitCost) if item.UnitCost else 0.0
                    unit_price = float(item.UnitPrice) if item.UnitPrice else 0.0
                    
                    row_data = base_doc_data.copy()
                    row_data.update({
                        'InventoryId': inventory.InventoryId if inventory else None,
                        'InventoryCode': inventory.InventoryCode if inventory else '',
                        'InventoryName': inventory.InventoryName if inventory else '',
                        'Quantity': quantity,
                        'UnitCost': unit_cost,
                        'UnitPrice': unit_price,
                        'TotalCost': quantity * unit_cost,
                        'TotalPrice': quantity * unit_price,
                    })
                    documents_data.append(row_data)
            else:
                # Document has no items, create one row with empty inventory fields
                row_data = base_doc_data.copy()
                row_data.update({
                    'InventoryId': None,
                    'InventoryCode': '',
                    'InventoryName': '',
                    'Quantity': 0.0,
                    'UnitCost': 0.0,
                    'UnitPrice': 0.0,
                    'TotalCost': 0.0,
                    'TotalPrice': 0.0,
                })
                documents_data.append(row_data)
        
        # Format details data for ЖУРНАЛ tab
        details_data = []
        for detail in all_details:
            details_data.append({
                'document_id': detail.DocumentId.DocumentId,  # Add document_id for navigation
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


@login_required
@permission_required('core.view_invdocument', raise_exception=True)
def get_inv_balance_data(request):
    """API endpoint to get inventory account balance data"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method allowed'}, status=405)
    
    try:
        # Get date parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        as_of_date = request.GET.get('as_of_date')
        effective_as_of = as_of_date or end_date or start_date
        
        if not effective_as_of:
            effective_as_of = timezone.now().date().isoformat()
        
        balance_data = []
        try:
            db_alias = get_current_db()
            try:
                # Execute the inventory balance function
                with connections[db_alias].cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM calculate_inventory_balance(%s, %s)",
                        [start_date, end_date]
                    )
                    
                    # Get column names
                    columns = [col[0] for col in cursor.description]
                    
                    # Fetch all results
                    results = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    balance_data = [
                        dict(zip(columns, row)) for row in results
                    ]
                    
                    # Convert Decimal values to float for JSON serialization
                    from decimal import Decimal
                    for item in balance_data:
                        for key, value in item.items():
                            if isinstance(value, Decimal):
                                item[key] = float(value)
            finally:
                connections[db_alias].close()
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error calculating inventory balance: {str(e)}'
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'balance_data': balance_data,
            'balance_count': len(balance_data),
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error loading balance data: {str(e)}'
        }, status=500)


@login_required
@permission_required('core.view_invdocument', raise_exception=True)
@require_http_methods(["GET"])
def api_get_inventory_balance_warehouse(request):
    """API endpoint to get inventory balance data filtered by warehouse and account"""
    from datetime import datetime
    from decimal import Decimal
    
    # Get all required parameters
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    warehouse_id_str = request.GET.get('warehouse_id')
    account_id_str = request.GET.get('account_id')
    
    # Validate all required parameters
    if not start_date_str or not end_date_str or not warehouse_id_str or not account_id_str:
        return JsonResponse({
            'success': False,
            'error': 'All parameters are required: start_date, end_date, warehouse_id, account_id'
        }, status=400)
    
    try:
        # Parse dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Parse IDs
        try:
            warehouse_id = int(warehouse_id_str)
            account_id = int(account_id_str)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'warehouse_id and account_id must be valid integers'
            }, status=400)
        
        balance_data = []
        db_alias = get_current_db()
        try:
            # Execute the inventory balance warehouse function
            with connections[db_alias].cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM report_inventory_balance_warehouse(%s, %s, %s::SMALLINT, %s)",
                    [start_date, end_date, warehouse_id, account_id]
                )
                
                # Get column names
                columns = [col[0] for col in cursor.description]
                
                # Fetch all results
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                balance_data = [
                    dict(zip(columns, row)) for row in results
                ]
                
                # Convert Decimal values to float for JSON serialization
                for item in balance_data:
                    for key, value in item.items():
                        if isinstance(value, Decimal):
                            item[key] = float(value)
        finally:
            connections[db_alias].close()
        
        # Enrich balance data with inventory details (UnitCost, UnitPrice, InventoryTypeName)
        inventory_ids = [item.get('inventoryid') for item in balance_data if item.get('inventoryid')]
        if inventory_ids:
            inventory_details = RefInventory.objects.filter(
                InventoryId__in=inventory_ids,
                IsDelete=False
            ).select_related('InventoryTypeId').values(
                'InventoryId', 'UnitCost', 'UnitPrice', 'InventoryTypeId__InventoryTypeName'
            )
            
            # Create a lookup dictionary for inventory details
            inventory_lookup = {
                inv['InventoryId']: {
                    'unitcost': float(inv['UnitCost']) if inv['UnitCost'] is not None else None,
                    'unitprice': float(inv['UnitPrice']) if inv['UnitPrice'] is not None else None,
                    'inventorytypename': inv['InventoryTypeId__InventoryTypeName'] if inv['InventoryTypeId__InventoryTypeName'] else None
                }
                for inv in inventory_details
            }
            
            # Merge inventory details into balance data
            for item in balance_data:
                inventory_id = item.get('inventoryid')
                if inventory_id and inventory_id in inventory_lookup:
                    item['unitcost'] = inventory_lookup[inventory_id]['unitcost']
                    item['unitprice'] = inventory_lookup[inventory_id]['unitprice']
                    item['inventorytypename'] = inventory_lookup[inventory_id]['inventorytypename']
                else:
                    item['unitcost'] = None
                    item['unitprice'] = None
                    item['inventorytypename'] = None
        
        return JsonResponse({
            'success': True,
            'balance_data': balance_data,
            'count': len(balance_data)
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': f'Invalid date format. Use YYYY-MM-DD: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error loading inventory balance: {str(e)}'
        }, status=500)


@login_required
@permission_required('core.view_invdocument', raise_exception=True)
@require_http_methods(["GET"])
def api_get_inventory_list(request):
    """JSON API endpoint to get all inventory items for modal selection"""
    from decimal import Decimal
    
    try:
        # Get all non-deleted inventory items with related data
        inventory_list = RefInventory.objects.filter(IsDelete=False).select_related(
            'InventoryTypeId', 'MeasurementId'
        ).order_by('InventoryName')
        
        # Convert to JSON-serializable format
        inventory_data = []
        for inv in inventory_list:
            inventory_data.append({
                'id': inv.InventoryId,
                'inventoryid': inv.InventoryId,
                'code': inv.InventoryCode or '',
                'inventorycode': inv.InventoryCode or '',
                'name': inv.InventoryName or '',
                'inventoryname': inv.InventoryName or '',
                'type': inv.InventoryTypeId.InventoryTypeName if inv.InventoryTypeId else '',
                'inventorytypename': inv.InventoryTypeId.InventoryTypeName if inv.InventoryTypeId else '',
                'inventorytypeid': inv.InventoryTypeId.InventoryTypeId if inv.InventoryTypeId else None,
                'unit': inv.MeasurementId.MeasurementName if inv.MeasurementId else '',
                'measurementname': inv.MeasurementId.MeasurementName if inv.MeasurementId else '',
                'measurementid': inv.MeasurementId.MeasurementId if inv.MeasurementId else None,
                'unitCost': str(inv.UnitCost) if inv.UnitCost is not None else '',
                'unitcost': float(inv.UnitCost) if inv.UnitCost is not None else None,
                'unitPrice': str(inv.UnitPrice) if inv.UnitPrice is not None else '',
                'unitprice': float(inv.UnitPrice) if inv.UnitPrice is not None else None,
                'isActive': inv.IsActive
            })
        
        return JsonResponse({
            'success': True,
            'inventory_data': inventory_data,
            'count': len(inventory_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error loading inventory list: {str(e)}'
        }, status=500)


@login_required
@permission_required('core.view_ref_account', raise_exception=True)
@require_http_methods(["GET"])
def api_accounts_json(request):
    """JSON API endpoint to return accounts as JSON for modal selection"""
    try:
        # Get filter parameters
        code_filter = request.GET.get('code', '')
        name_filter = request.GET.get('name', '')
        type_filter = request.GET.get('type', '')
        account_type_filter = request.GET.get('account_type', '')
        document_type_id = request.GET.get('document_type_id')
        status_filter = request.GET.get('status', '')
        
        # Get all accounts with related data
        accounts_list = Ref_Account.objects.select_related('AccountTypeId', 'CurrencyId').all()
        
        # Apply filters (same logic as refaccount_list)
        if code_filter:
            accounts_list = accounts_list.filter(AccountCode__icontains=code_filter)
        
        if name_filter:
            accounts_list = accounts_list.filter(AccountName__icontains=name_filter)
        
        if type_filter:
            accounts_list = accounts_list.filter(AccountTypeId__AccountTypeName__icontains=type_filter)
        
        if status_filter:
            if status_filter == 'active':
                accounts_list = accounts_list.filter(IsDelete=False)
            elif status_filter == 'inactive':
                accounts_list = accounts_list.filter(IsDelete=True)
        
        # Handle document_type_id filtering (same logic as refaccount_list)
        if not account_type_filter and document_type_id:
            if str(document_type_id) in {'5', '6', '7'}:
                account_type_filter = '8,9,11'
            else:
                try:
                    doc_type = Ref_Document_Type.objects.get(DocumentTypeId=document_type_id)
                    if doc_type.ParentId == 1:
                        account_type_filter = '1'
                    elif doc_type.ParentId == 2:
                        account_type_filter = '2'
                    else:
                        account_type_filter = '1,2,3,5,42,43,44,51,55,67,68,45,46,47,48'
                except Ref_Document_Type.DoesNotExist:
                    pass
        
        if account_type_filter:
            if ',' in account_type_filter:
                account_type_ids = [int(x.strip()) for x in account_type_filter.split(',') if x.strip().isdigit()]
                accounts_list = accounts_list.filter(AccountTypeId__AccountTypeId__in=account_type_ids)
            else:
                accounts_list = accounts_list.filter(AccountTypeId__AccountTypeId=account_type_filter)
        
        # Order by code
        accounts_list = accounts_list.order_by('AccountCode')
        
        # Convert to JSON-serializable format
        accounts_data = []
        for account in accounts_list:
            # Get currency default value from Ref_Currency.DefaultValue
            currency_default_value = 'null'
            if account.CurrencyId:
                try:
                    # Use the DefaultValue from Ref_Currency model
                    if account.CurrencyId.DefaultValue is not None:
                        currency_default_value = str(account.CurrencyId.DefaultValue)
                    else:
                        # Fallback: default to 1 if currency is MNT (CurrencyId == 1)
                        if account.CurrencyId.CurrencyId == 1:
                            currency_default_value = '1'
                except:
                    currency_default_value = 'null'
            
            accounts_data.append({
                'AccountId': account.AccountId,
                'AccountCode': account.AccountCode or '',
                'AccountName': account.AccountName or '',
                'AccountTypeName': account.AccountTypeId.AccountTypeName if account.AccountTypeId else '',
                'CurrencyId': account.CurrencyId.CurrencyId if account.CurrencyId else None,
                'CurrencyName': account.CurrencyId.Currency_name if account.CurrencyId else '',
                'CurrencyDefaultValue': currency_default_value,
                'IsDelete': account.IsDelete
            })
        
        return JsonResponse({
            'success': True,
            'accounts': accounts_data,
            'count': len(accounts_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@permission_required('core.view_ref_account', raise_exception=True)
@require_http_methods(["GET"])
def check_account_uniqueness(request):
    """API endpoint to check if AccountCode or AccountName already exists"""
    try:
        account_code = request.GET.get('account_code', '').strip()
        account_name = request.GET.get('account_name', '').strip()
        account_id = request.GET.get('account_id')  # For update operations
        
        result = {
            'success': True,
            'account_code_exists': False,
            'account_name_exists': False,
            'message': ''
        }
        
        # Check AccountCode uniqueness
        if account_code:
            query = Ref_Account.objects.filter(AccountCode=account_code)
            if account_id:
                try:
                    account_id = int(account_id)
                    query = query.exclude(pk=account_id)
                except (ValueError, TypeError):
                    pass
            
            if query.exists():
                result['account_code_exists'] = True
                result['message'] = 'Энэ данс жагсаалтанд байна.'
        
        # Check AccountName uniqueness
        if account_name:
            query = Ref_Account.objects.filter(AccountName=account_name)
            if account_id:
                try:
                    account_id = int(account_id)
                    query = query.exclude(pk=account_id)
                except (ValueError, TypeError):
                    pass
            
            if query.exists():
                result['account_name_exists'] = True
                if not result['message']:
                    result['message'] = 'Энэ данс жагсаалтанд байна.'
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@permission_required('core.view_refclient', raise_exception=True)
@require_http_methods(["GET"])
def check_client_name_register_uniqueness(request):
    """API endpoint to check if ClientName and ClientRegister combination already exists"""
    try:
        client_name = request.GET.get('client_name', '').strip()
        client_register = request.GET.get('client_register', '').strip()
        client_id = request.GET.get('client_id')  # For update operations
        
        result = {
            'success': True,
            'combination_exists': False,
            'message': ''
        }
        
        # Normalize client_name (remove extra whitespace)
        if client_name:
            client_name = ' '.join(client_name.split())
        
        # Normalize client_register (strip whitespace, treat empty as None)
        if client_register:
            client_register = client_register.strip()
            if not client_register:
                client_register = None
        else:
            client_register = None
        
        # Check combination uniqueness
        if client_name:
            query = RefClient.objects.filter(ClientName=client_name)
            
            # Handle ClientRegister: if None, check for None or empty string
            if client_register is None:
                query = query.filter(Q(ClientRegister__isnull=True) | Q(ClientRegister=''))
            else:
                query = query.filter(ClientRegister=client_register)
            
            # Exclude current instance if updating
            if client_id:
                try:
                    client_id = int(client_id)
                    query = query.exclude(pk=client_id)
                except (ValueError, TypeError):
                    pass
            
            if query.exists():
                result['combination_exists'] = True
                result['message'] = 'Харилцагчийн нэр болон регистрийн дугаарын хослол давхардаж байна. Нягтална уу?'
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== ASSET JOURNAL VIEWS ====================

@login_required
@permission_required('core.view_ast_document', raise_exception=True)
def ast_documents(request):
    """View for displaying asset documents with new template"""
    # Get asset documents with related data (including deleted ones)
    ast_documents = Ast_Document.objects.select_related(
        'DocumentTypeId', 'ClientId', 'AccountId', 'TemplateId'
    ).order_by('-DocumentDate')
    
    context = {
        'ast_documents': ast_documents,
    }
    
    return render(request, 'core/astreport.html', context)


@login_required
@permission_required('core.view_ast_document', raise_exception=True)
def get_ast_documents_filtered(request):
    """API endpoint to get ALL asset documents and details for all tabs in one call"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method allowed'}, status=405)
    
    try:
        # Get filter parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        document_type_id = request.GET.get('document_type_id')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 1000))  # Large page size to get all records
        
        # Limit page size to prevent abuse
        if page_size > 2000:
            page_size = 2000
        
        # Get ALL asset documents (active only, exclude deleted) with related data
        all_documents = Ast_Document.objects.select_related(
            'DocumentTypeId', 'AccountId', 'ClientId', 'TemplateId', 'CreatedBy'
        ).prefetch_related('document_items__AssetCardId').filter(IsDelete=False).order_by('-DocumentDate').distinct()
        
        # Apply date filtering if provided
        if start_date:
            all_documents = all_documents.filter(DocumentDate__gte=start_date)
        if end_date:
            all_documents = all_documents.filter(DocumentDate__lte=end_date)
        
        # Apply DocumentTypeId filter if provided
        if document_type_id:
            all_documents = all_documents.filter(DocumentTypeId=document_type_id)
        
        # Get ALL asset document details for ЖУРНАЛ tab
        all_details = Ast_Document_Detail.objects.select_related(
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
        
        # Format documents data for БАРИМТ and УСТГАСАН БАРИМТ tabs
        # Create one row per document-item combination to enable item-by-item searching
        documents_data = []
        seen_documents = set()
        
        for doc in all_documents:
            # Create a unique key for this document
            doc_key = f"{doc.DocumentId}_{doc.DocumentNo}_{doc.DocumentDate}"
            
            # Skip if we've already seen this document
            if doc_key in seen_documents:
                continue
                
            seen_documents.add(doc_key)
            
            # Get document items
            document_items = doc.document_items.all()
            
            # Base document data fields
            base_doc_data = {
                'DocumentId': doc.DocumentId,
                'DocumentNo': doc.DocumentNo,
                'DocumentDate': doc.DocumentDate.strftime('%Y-%m-%d'),
                'DocumentTypeId': doc.DocumentTypeId.DocumentTypeId if doc.DocumentTypeId else None,
                'DocumentTypeCode': doc.DocumentTypeId.DocumentTypeCode if doc.DocumentTypeId else '',
                'ClientName': doc.ClientId.ClientName if doc.ClientId else '',
                'AccountCode': doc.AccountId.AccountCode if doc.AccountId else '',
                'UserName': doc.CreatedBy.username if doc.CreatedBy else '',
                'IsDelete': doc.IsDelete,  # Include delete status for frontend filtering
            }
            
            # If document has items, create one row per item
            if document_items:
                for item in document_items:
                    asset_card = item.AssetCardId
                    quantity = float(item.Quantity) if item.Quantity else 0.0
                    unit_cost = float(item.UnitCost) if item.UnitCost else 0.0
                    unit_price = float(item.UnitPrice) if item.UnitPrice else 0.0
                    
                    row_data = base_doc_data.copy()
                    row_data.update({
                        'AssetCardId': asset_card.AssetCardId if asset_card else None,
                        'AssetCardCode': asset_card.AssetCardCode if asset_card else '',
                        'AssetCardName': asset_card.AssetCardName if asset_card else '',
                        'Quantity': quantity,
                        'UnitCost': unit_cost,
                        'UnitPrice': unit_price,
                        'TotalCost': quantity * unit_cost,
                        'TotalPrice': quantity * unit_price,
                    })
                    documents_data.append(row_data)
            else:
                # Document has no items, create one row with empty asset card fields
                row_data = base_doc_data.copy()
                row_data.update({
                    'AssetCardId': None,
                    'AssetCardCode': '',
                    'AssetCardName': '',
                    'Quantity': 0.0,
                    'UnitCost': 0.0,
                    'UnitPrice': 0.0,
                    'TotalCost': 0.0,
                    'TotalPrice': 0.0,
                })
                documents_data.append(row_data)
        
        # Format details data for ЖУРНАЛ tab
        details_data = []
        for detail in all_details:
            details_data.append({
                'document_id': detail.DocumentId.DocumentId,  # Add document_id for navigation
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


@login_required
@permission_required('core.view_ast_document', raise_exception=True)
def get_ast_balance_data(request):
    """API endpoint to get asset account balance data"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method allowed'}, status=405)
    
    try:
        # Get date parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        as_of_date = request.GET.get('as_of_date')
        effective_as_of = as_of_date or end_date or start_date
        
        if not effective_as_of:
            effective_as_of = timezone.now().date().isoformat()
        
        balance_data = []
        try:
            db_alias = get_current_db()
            try:
                # Execute the asset balance function (uses only end_date as asofdate)
                with connections[db_alias].cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM report_assetcard_balance(%s)",
                        [effective_as_of]
                    )
                    
                    # Get column names
                    columns = [col[0] for col in cursor.description]
                    
                    # Fetch all results
                    results = cursor.fetchall()
                    
                    # Convert to list of dictionaries
                    balance_data = [
                        dict(zip(columns, row)) for row in results
                    ]
                    
                    # Convert Decimal values to float for JSON serialization
                    from decimal import Decimal
                    for item in balance_data:
                        for key, value in item.items():
                            if isinstance(value, Decimal):
                                item[key] = float(value)
            finally:
                connections[db_alias].close()
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error calculating asset balance: {str(e)}'
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'balance_data': balance_data,
            'balance_count': len(balance_data),
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            },
            'as_of_date': effective_as_of
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error loading balance data: {str(e)}'
        }, status=500)


@login_required
@permission_required('core.view_ast_document', raise_exception=True)
@require_http_methods(["GET"])
def api_asset_card_usage_check(request):
    """Check if an asset card is already used when creating asset receipts (DocumentTypeId=10)."""
    asset_card_id = request.GET.get('asset_card_id')
    document_type = request.GET.get('document_type')

    if not asset_card_id:
        return JsonResponse({
            'success': False,
            'error': 'asset_card_id is required'
        }, status=400)

    try:
        asset_card_id = int(asset_card_id)
    except (TypeError, ValueError):
        return JsonResponse({
            'success': False,
            'error': 'Invalid asset_card_id'
        }, status=400)

    # Only enforce for document type 10 (asset receipt)
    if str(document_type) != '10':
        return JsonResponse({
            'success': True,
            'is_available': True
        })

    warning_message = (
        "Тухайн хөрөнгийг орлогод авсан байна. эсвэл элэгдэл байгуулсан байна. эсвэл эхний үлдэгдэлтэй байна."
    )

    try:
        has_beginning = Ast_Beginning_Balance.objects.filter(
            AssetCardId_id=asset_card_id,
            IsDelete=False
        ).exists()

        has_depreciation = AstDepreciationExpense.objects.filter(
            AssetCardId_id=asset_card_id
        ).exists()

        has_documents = Ast_Document_Item.objects.filter(
            AssetCardId_id=asset_card_id,
            DocumentId__IsDelete=False
        ).exists()

        is_available = not (has_beginning or has_depreciation or has_documents)

        return JsonResponse({
            'success': True,
            'is_available': is_available,
            'message': None if is_available else warning_message
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error checking asset card usage: {str(e)}'
        }, status=500)


# ==================== TRIAL CLOSING ENTRY VIEWS ====================

@login_required
@permission_required('core.view_astdepreciationexpense', raise_exception=True)
def trial_closing_entry(request):
    """Display trial closing entry page with 3 tabs"""
    return render(request, 'core/trial_closing_entry.html')


@login_required
@permission_required('core.view_astdepreciationexpense', raise_exception=True)
def trial_depreciation(request):
    """Display trial depreciation entry page"""
    return render(request, 'core/trial_depreciation.html')


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


@login_required
@permission_required('core.view_astdepreciationexpense', raise_exception=True)
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
                    'depreciation_date': exp.DepreciationDate.strftime('%Y-%m-%d') if exp.DepreciationDate else '',
                'created_date': exp.CreatedDate.strftime('%Y-%m-%d') if exp.CreatedDate else '',
                'created_by': exp.CreatedBy.username if exp.CreatedBy else '',
                'debit_account_code': exp.DebitAccountId.AccountCode if exp.DebitAccountId else '',
                'credit_account_id': exp.CreditAccountId.AccountId if exp.CreditAccountId else None,
                'credit_account_code': exp.CreditAccountId.AccountCode if exp.CreditAccountId else '',
                'document_id': exp.DocumentId.DocumentId if exp.DocumentId else None,
                'document_no': exp.DocumentId.DocumentNo if exp.DocumentId else '',
                'document_date': exp.DocumentId.DocumentDate.strftime('%Y-%m-%d') if exp.DocumentId and exp.DocumentId.DocumentDate else ''
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


@login_required
@require_http_methods(["GET"])
def api_calculate_depreciation(request):
    """API endpoint to calculate depreciation for a date range"""
    from datetime import datetime
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if not start_date_str or not end_date_str:
        return JsonResponse({
            'success': False,
            'error': 'Both start_date and end_date are required'
        }, status=400)
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Find period - first try exact match
        period = Ref_Period.objects.filter(
            BeginDate=start_date,
            EndDate=end_date
        ).first()
        
        # If not found, find period that contains end_date (auto-adjust)
        if not period:
            period = Ref_Period.objects.filter(
                BeginDate__lte=end_date,
                EndDate__gte=end_date
            ).first()
        
        if not period:
            return JsonResponse({
                'success': False,
                'error': 'No period found for the selected date range'
            }, status=400)
        
        # Call SQL function (cast period_id to SMALLINT as function expects SMALLINT)
        db_alias = get_current_db()
        try:
            with connections[db_alias].cursor() as cursor:
                cursor.execute("SELECT * FROM calculate_depreciation(%s::SMALLINT, %s)", [period.PeriodId, request.user.id])
                columns = [col[0] for col in cursor.description]
                results = [
                    dict(zip(columns, row))
                    for row in cursor.fetchall()
                ]
        finally:
            connections[db_alias].close()
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully calculated {len(results)} depreciation expense records',
            'period_id': period.PeriodId,
            'period_name': period.PeriodName,
            'adjusted_dates': {
                'start_date': period.BeginDate.strftime('%Y-%m-%d'),
                'end_date': period.EndDate.strftime('%Y-%m-%d')
            },
            'records_count': len(results)
        })
        
    except Exception as e:
        logger.error(f'Error calculating depreciation: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error calculating depreciation: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_calculate_closing_record(request):
    """API endpoint to calculate closing record for a date range"""
    from datetime import datetime
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if not start_date_str or not end_date_str:
        return JsonResponse({
            'success': False,
            'error': 'Both start_date and end_date are required'
        }, status=400)
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Find period - first try exact match
        period = Ref_Period.objects.filter(
            BeginDate=start_date,
            EndDate=end_date
        ).first()
        
        # If not found, find period that contains end_date (auto-adjust)
        if not period:
            period = Ref_Period.objects.filter(
                BeginDate__lte=end_date,
                EndDate__gte=end_date
            ).first()
        
        if not period:
            return JsonResponse({
                'success': False,
                'error': 'No period found for the selected date range'
            }, status=400)
        
        # Call SQL function (returns VOID, cast period_id to SMALLINT as function expects SMALLINT)
        db_alias = get_current_db()
        try:
            with connections[db_alias].cursor() as cursor:
                cursor.execute("SELECT calculate_closing_record(%s::SMALLINT, %s)", [period.PeriodId, request.user.id])
                # Function returns VOID, so no need to fetch results
        finally:
            connections[db_alias].close()
        
        return JsonResponse({
            'success': True,
            'message': 'Successfully calculated closing records',
            'period_id': period.PeriodId,
            'period_name': period.PeriodName,
            'adjusted_dates': {
                'start_date': period.BeginDate.strftime('%Y-%m-%d'),
                'end_date': period.EndDate.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        logger.error(f'Error calculating closing record: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error calculating closing record: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_get_period_begin_date(request):
    """API endpoint to get period BeginDate for a given document date"""
    from datetime import datetime
    
    document_date_str = request.GET.get('document_date')
    
    if not document_date_str:
        return JsonResponse({
            'success': False,
            'error': 'document_date parameter is required'
        }, status=400)
    
    try:
        document_date = datetime.strptime(document_date_str, '%Y-%m-%d').date()
        
        # Find period that contains the document date
        period = Ref_Period.objects.filter(
            BeginDate__lte=document_date,
            EndDate__gte=document_date
        ).first()
        
        if not period:
            return JsonResponse({
                'success': False,
                'error': 'No period found for the document date'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'begin_date': period.BeginDate.strftime('%Y-%m-%d')
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid date format. Please use YYYY-MM-DD format.'
        }, status=400)
    except Exception as e:
        logger.error(f'Error getting period begin date: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error getting period begin date: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_get_periods_list(request):
    """API endpoint to get all periods from ref_period table"""
    try:
        periods = Ref_Period.objects.all().order_by('PeriodId')
        
        periods_data = []
        for period in periods:
            periods_data.append({
                'period_id': period.PeriodId,
                'period_name': period.PeriodName,
                'begin_date': period.BeginDate.strftime('%Y-%m-%d'),
                'end_date': period.EndDate.strftime('%Y-%m-%d'),
                'is_locked': period.IsLock
            })
        
        return JsonResponse({
            'success': True,
            'periods': periods_data
        })
        
    except Exception as e:
        logger.error(f'Error getting periods list: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error getting periods list: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
@permission_required('core.delete_cash_document', raise_exception=True)
def api_delete_closing_entries(request):
    """API endpoint to delete closing entries (DocumentTypeId=14) for a period"""
    from datetime import datetime
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if not start_date_str or not end_date_str:
        return JsonResponse({
            'success': False,
            'error': 'Both start_date and end_date are required'
        }, status=400)
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Find closing documents (DocumentTypeId=14) within the date range
        closing_documents = Cash_Document.objects.filter(
            DocumentTypeId=14,
            DocumentDate__gte=start_date,
            DocumentDate__lte=end_date
        )
        
        # Get document IDs before deletion
        document_ids = list(closing_documents.values_list('DocumentId', flat=True))
        
        if not document_ids:
            return JsonResponse({
                'success': True,
                'message': 'No closing entries found for the selected period',
                'deleted_count': 0
            })
        
        # Delete cash_document_detail records first (foreign key constraint)
        deleted_details_count = Cash_DocumentDetail.objects.filter(
            DocumentId__in=document_ids
        ).delete()[0]
        
        # Delete cash_document records
        deleted_documents_count = closing_documents.delete()[0]
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_documents_count} closing document(s) and {deleted_details_count} detail record(s)',
            'deleted_count': deleted_documents_count,
            'deleted_details_count': deleted_details_count
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid date format. Please use YYYY-MM-DD format.'
        }, status=400)
    except Exception as e:
        logger.error(f'Error deleting closing entries: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error deleting closing entries: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_delete_depreciation_entries(request):
    """API endpoint to delete depreciation entries (DocumentTypeId=13) for a period"""
    from datetime import datetime
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if not start_date_str or not end_date_str:
        return JsonResponse({
            'success': False,
            'error': 'Both start_date and end_date are required'
        }, status=400)
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Find depreciation documents (DocumentTypeId=13) within the date range
        depreciation_documents = Cash_Document.objects.filter(
            DocumentTypeId=13,
            DocumentDate__gte=start_date,
            DocumentDate__lte=end_date
        )
        
        # Get document IDs before deletion
        document_ids = list(depreciation_documents.values_list('DocumentId', flat=True))
        
        if not document_ids:
            return JsonResponse({
                'success': True,
                'message': 'No depreciation entries found for the selected period',
                'deleted_count': 0
            })
        
        # Delete cash_document_detail records first (foreign key constraint)
        deleted_details_count = Cash_DocumentDetail.objects.filter(
            DocumentId__in=document_ids
        ).delete()[0]
        
        # Delete cash_document records
        deleted_documents_count = depreciation_documents.delete()[0]
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_documents_count} depreciation document(s) and {deleted_details_count} detail record(s)',
            'deleted_count': deleted_documents_count,
            'deleted_details_count': deleted_details_count
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid date format. Use YYYY-MM-DD'
        }, status=400)
    except Exception as e:
        logger.error(f'Error deleting depreciation entries: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error deleting depreciation entries: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_calculate_cost_adjustment(request):
    """API endpoint to calculate cost adjustment for a date range"""
    from datetime import datetime
    
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if not start_date_str or not end_date_str:
        return JsonResponse({
            'success': False,
            'error': 'Both start_date and end_date are required'
        }, status=400)
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        # Find period - first try exact match
        period = Ref_Period.objects.filter(
            BeginDate=start_date,
            EndDate=end_date
        ).first()
        
        # If not found, find period that contains end_date (auto-adjust)
        if not period:
            period = Ref_Period.objects.filter(
                BeginDate__lte=end_date,
                EndDate__gte=end_date
            ).first()
        
        if not period:
            return JsonResponse({
                'success': False,
                'error': 'No period found for the selected date range'
            }, status=400)
        
        # Call SQL function (returns VOID, cast period_id to SMALLINT as function expects SMALLINT)
        db_alias = get_current_db()
        try:
            with connections[db_alias].cursor() as cursor:
                cursor.execute("SELECT calculate_cost_adjustment(%s::SMALLINT)", [period.PeriodId])
                # Function returns VOID, so no need to fetch results
        finally:
            connections[db_alias].close()
        
        return JsonResponse({
            'success': True,
            'message': 'Successfully calculated cost adjustment',
            'period_id': period.PeriodId,
            'period_name': period.PeriodName,
            'adjusted_dates': {
                'start_date': period.BeginDate.strftime('%Y-%m-%d'),
                'end_date': period.EndDate.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        logger.error(f'Error calculating cost adjustment: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error calculating cost adjustment: {str(e)}'
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
        vat_constant_9 = Ref_Constant.objects.get(ConstantID=9)   # Receivable VAT
        vat_constant_10 = Ref_Constant.objects.get(ConstantID=10) # Payable VAT
        
        # Convert ConstantName to integer to get AccountId
        receivable_vat_account_id = int(vat_constant_9.ConstantName)   # Receivable (ConstantID=9)
        payable_vat_account_id = int(vat_constant_10.ConstantName)    # Payable (ConstantID=10)
        
        # Get actual account objects to retrieve account codes
        receivable_vat_account = Ref_Account.objects.get(AccountId=receivable_vat_account_id)
        payable_vat_account = Ref_Account.objects.get(AccountId=payable_vat_account_id)
        
        vat_accounts = {
            'vat_account_1_id': payable_vat_account_id,      # Payable VAT (ConstantID=10)
            'vat_account_2_id': receivable_vat_account_id,   # Receivable VAT (ConstantID=9)
            'vat_account_1_display': payable_vat_account.AccountCode,
            'vat_account_2_display': receivable_vat_account.AccountCode,
        }
    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
        # Fallback values
        vat_accounts = {
            'vat_account_1_id': 8,  # Payable VAT fallback
            'vat_account_2_id': 9,  # Receivable VAT fallback
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
            
            # Check period lock (server-side validation)
            if Ref_Period.objects.filter(IsLock=True, BeginDate__lte=document.DocumentDate, EndDate__gte=document.DocumentDate).exists():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Тухайн сар түгжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.'
                    })
                else:
                    messages.error(request, 'Тухайн сар түгжигдсэн байна. Админы зөвшөөрлөөр эрх нээгдэнэ.')
                    # Get VAT accounts for re-rendering
                    vat_accounts = {}
                    try:
                        from .models import Ref_Constant, Ref_Account
                        vat_constant_9 = Ref_Constant.objects.get(ConstantID=9)   # Receivable VAT
                        vat_constant_10 = Ref_Constant.objects.get(ConstantID=10) # Payable VAT
                        
                        # Convert ConstantName to integer to get AccountId
                        receivable_vat_account_id = int(vat_constant_9.ConstantName)   # Receivable (ConstantID=9)
                        payable_vat_account_id = int(vat_constant_10.ConstantName)    # Payable (ConstantID=10)
                        
                        # Get actual account objects to retrieve account codes
                        receivable_vat_account = Ref_Account.objects.get(AccountId=receivable_vat_account_id)
                        payable_vat_account = Ref_Account.objects.get(AccountId=payable_vat_account_id)
                        
                        vat_accounts = {
                            'vat_account_1_id': payable_vat_account_id,      # Payable VAT (ConstantID=10)
                            'vat_account_2_id': receivable_vat_account_id,   # Receivable VAT (ConstantID=9)
                            'vat_account_1_display': payable_vat_account.AccountCode,
                            'vat_account_2_display': receivable_vat_account.AccountCode,
                        }
                    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
                        vat_accounts = {
                            'vat_account_1_id': 8,  # Payable VAT fallback
                            'vat_account_2_id': 9,  # Receivable VAT fallback
                            'vat_account_1_display': '3403-01',
                            'vat_account_2_display': '3403-02',
                        }
                    return render(request, 'core/astdocument_form.html', {
                        'form': form,
                        'item': document,
                        'parentid': parentid,
                        'vat_accounts': vat_accounts
                    })
            
            document.save()
            messages.success(request, 'Asset document updated successfully.')
            
            # Check if AJAX request and return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('core:astdocument_master_detail')
                })
            
            return redirect('core:astdocument_master_detail')
        else:
            # Form validation failed
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Validation failed',
                    'errors': form.errors
                }, status=400)
            messages.error(request, 'Please correct the errors below.')
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
                    'error': 'Тухайн сар түгжигдсэн байна. Засварлах боломжгүй. Админы зөвшөөрлөөр эрх нээгдэнэ.',
                    'redirect': True
                })
            else:
                messages.error(request, 'Тухайн сар түгжигдсэн байна. Засварлах боломжгүй. Админы зөвшөөрлөөр эрх нээгдэнэ.')
                return redirect('core:astdocument_master_detail')
        
        form = AstDocumentForm(instance=document, parentid=parentid)
    
    # Get VAT account IDs from ref_constant table and fetch actual account codes
    vat_accounts = {}
    try:
        from .models import Ref_Constant, Ref_Account
        vat_constant_9 = Ref_Constant.objects.get(ConstantID=9)   # Receivable VAT
        vat_constant_10 = Ref_Constant.objects.get(ConstantID=10) # Payable VAT
        
        # Convert ConstantName to integer to get AccountId
        receivable_vat_account_id = int(vat_constant_9.ConstantName)   # Receivable (ConstantID=9)
        payable_vat_account_id = int(vat_constant_10.ConstantName)    # Payable (ConstantID=10)
        
        # Get actual account objects to retrieve account codes
        receivable_vat_account = Ref_Account.objects.get(AccountId=receivable_vat_account_id)
        payable_vat_account = Ref_Account.objects.get(AccountId=payable_vat_account_id)
        
        vat_accounts = {
            'vat_account_1_id': payable_vat_account_id,      # Payable VAT (ConstantID=10)
            'vat_account_2_id': receivable_vat_account_id,   # Receivable VAT (ConstantID=9)
            'vat_account_1_display': payable_vat_account.AccountCode,
            'vat_account_2_display': receivable_vat_account.AccountCode,
        }
    except (Ref_Constant.DoesNotExist, Ref_Account.DoesNotExist, ValueError):
        # Fallback values
        vat_accounts = {
            'vat_account_1_id': 8,  # Payable VAT fallback
            'vat_account_2_id': 9,  # Receivable VAT fallback
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
    
    depreciation_account_id = None
    expense_account_id = None
    if document.AccountId_id:
        dep_mapping = Ref_Asset_Depreciation_Account.objects.filter(
            AssetAccountId=document.AccountId,
            IsDelete=False
        ).select_related('DepreciationAccountId', 'ExpenseAccountId').first()
        if dep_mapping and dep_mapping.DepreciationAccountId_id:
            depreciation_account_id = dep_mapping.DepreciationAccountId_id
        if dep_mapping and dep_mapping.ExpenseAccountId_id:
            expense_account_id = dep_mapping.ExpenseAccountId_id
    
    # Get document items and details
    document_items_queryset = Ast_Document_Item.objects.select_related('AssetCardId').filter(
        DocumentId=document
    ).order_by('DocumentItemId')
    document_items = list(document_items_queryset)

    # Prefetch cumulative depreciation + depreciation expense per asset card as of document date
    asset_depreciation_lookup = {}
    if document.DocumentDate and document.AccountId_id:
        db_alias = get_current_db()
        try:
            with connections[db_alias].cursor() as cursor:
                cursor.execute(
                    """
                    SELECT accountid,
                           assetcardid,
                           COALESCE(cumulateddepreciation, 0) AS cumulated_depreciation,
                           COALESCE(depreciationexpense, 0) AS depreciation_expense,
                           totalexpense
                    FROM report_assetcard_balance(%s)
                    """,
                    [document.DocumentDate]
                )
                records = cursor.fetchall()
                for account_id, asset_card_id, cumulated_depreciation, depreciation_expense, total_expense in records:
                    if asset_card_id is None:
                        continue
                    cumulated_value = Decimal(cumulated_depreciation or 0)
                    expense_value = Decimal(depreciation_expense or 0)
                    total_value = Decimal(total_expense) if total_expense is not None else None

                    asset_info = {
                        'cumulated': cumulated_value,
                        'expense': expense_value,
                        'total': total_value,
                        'initial': (total_value if total_value is not None else cumulated_value + expense_value)
                    }

                    asset_card_id_int = int(asset_card_id)
                    current = asset_depreciation_lookup.get(asset_card_id_int)

                    # Prefer record matching the document's account; otherwise keep first seen
                    if document.AccountId_id and account_id == document.AccountId_id:
                        asset_depreciation_lookup[asset_card_id_int] = asset_info
                    elif current is None:
                        asset_depreciation_lookup[asset_card_id_int] = asset_info
        except Exception as exc:
            logger.warning('Unable to load asset depreciation balances for document %s: %s', document.DocumentId, exc)
        finally:
            connections[db_alias].close()

    zero_decimal = Decimal('0.00')
    for item in document_items:
        balance_info = asset_depreciation_lookup.get(item.AssetCardId_id)
        if balance_info:
            item.balance_cumulated_depreciation = balance_info['cumulated']
            item.balance_depreciation_expense = balance_info['expense']
            if balance_info.get('total') is not None:
                item.total_expense = balance_info['total']
                item.initial_depreciation = balance_info['total']
            else:
                item.total_expense = balance_info['initial']
                item.initial_depreciation = balance_info['initial']
        else:
            item.balance_cumulated_depreciation = zero_decimal
            item.balance_depreciation_expense = zero_decimal
            item.total_expense = zero_decimal
            item.initial_depreciation = zero_decimal
    
    document_details = Ast_Document_Detail.objects.select_related(
        'AccountId', 'ClientId', 'CurrencyId'
    ).filter(DocumentId=document).order_by('DocumentDetailId')
    
    # Get currencies for the form
    currencies = Ref_Currency.objects.filter(IsActive=True).order_by('CurrencyId')
    
    # Get template details if TemplateId exists
    template_details = []
    if document.TemplateId:
        template_details = Ref_Template_Detail.objects.select_related('AccountId', 'AccountId__AccountTypeId').filter(
            TemplateId=document.TemplateId
        ).order_by('TemplateDetailId')
    
    # VAT rate is available globally via context processor (VAT_RATE_PERCENT)
    # No need to pass it explicitly in context
    
    context = {
        'document': document,
        'document_items': document_items,
        'document_details': document_details,
        'currencies': currencies,
        'template_details': template_details,
        'depreciation_account_id': depreciation_account_id,
        'expense_account_id': expense_account_id,
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
def asset_cards_json(request):
    """API endpoint to return asset cards as JSON with asset type information"""
    try:
        asset_cards = Ref_Asset_Card.objects.select_related(
            'AssetId__AssetTypeId', 'ClientId'
        ).order_by('AssetCardCode')
        
        asset_cards_data = []
        for card in asset_cards:
            asset_cards_data.append({
                'AssetCardId': card.AssetCardId,
                'AssetCardCode': card.AssetCardCode,
                'AssetCardName': card.AssetCardName or '',
                'AssetId': card.AssetId.AssetId if card.AssetId else None,
                'AssetName': card.AssetId.AssetName if card.AssetId else '',
                'AssetTypeId': card.AssetId.AssetTypeId.AssetTypeId if card.AssetId and card.AssetId.AssetTypeId else None,
                'AssetTypeName': card.AssetId.AssetTypeId.AssetTypeName if card.AssetId and card.AssetId.AssetTypeId else '',
                'UnitCost': float(card.UnitCost) if card.UnitCost else 0,
                'UnitPrice': float(card.UnitPrice) if card.UnitPrice else 0,
                'CumulatedDepreciation': float(card.CumulatedDepreciation) if card.CumulatedDepreciation else 0,
                'DailyExpense': float(card.DailyExpense) if card.DailyExpense else 0,
                'ClientId': card.ClientId.ClientId if card.ClientId else None,
                'ClientName': card.ClientId.ClientName if card.ClientId else ''
            })
        
        return JsonResponse({
            'success': True,
            'asset_cards': asset_cards_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def clients_json(request):
    """API endpoint to return clients as JSON for modal dropdowns with pagination support"""
    try:
        # Use select_related to optimize query and get ClientType data
        clients_queryset = RefClient.objects.filter(IsDelete=False).select_related('ClientType').order_by('ClientName')
        
        # Filter by client_type_id if provided
        client_type_id = request.GET.get('client_type_id', '')
        if client_type_id:
            try:
                client_type_id = int(client_type_id)
                clients_queryset = clients_queryset.filter(ClientType__ClientTypeId=client_type_id)
            except (ValueError, TypeError):
                pass
        
        # Support pagination parameters
        page = request.GET.get('page', '1')
        page_size = request.GET.get('page_size', '100')  # Default to 100 for modal, can be increased
        
        try:
            page = int(page)
            page_size = int(page_size)
            # Limit max page size to prevent memory issues
            if page_size > 500:
                page_size = 500
        except (ValueError, TypeError):
            page = 1
            page_size = 100
        
        # Use values() to optimize query - only fetch needed fields
        paginator = Paginator(clients_queryset.values(
            'ClientId', 'ClientName', 'ClientCode', 'ClientRegister', 
            'ClientType__ClientTypeId', 'ClientType__ClientTypeName'
        ), page_size)
        
        try:
            clients_page = paginator.page(page)
        except PageNotAnInteger:
            clients_page = paginator.page(1)
        except EmptyPage:
            clients_page = paginator.page(paginator.num_pages)
        
        # Build response data
        clients_data = []
        for client in clients_page:
            clients_data.append({
                'ClientId': client['ClientId'],
                'ClientName': client['ClientName'],
                'ClientCode': client['ClientCode'],
                'ClientRegister': client['ClientRegister'] or '',
                'ClientTypeId': client['ClientType__ClientTypeId'],
                'ClientTypeName': client['ClientType__ClientTypeName'] or ''
            })
        
        return JsonResponse({
            'success': True,
            'clients': clients_data,
            'count': len(clients_data),
            'total_count': paginator.count,
            'page': clients_page.number,
            'num_pages': paginator.num_pages,
            'has_next': clients_page.has_next(),
            'has_previous': clients_page.has_previous()
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
def refinventory_types_json(request):
    """API endpoint to return inventory types as JSON for modal dropdowns"""
    try:
        from .models import Ref_Inventory_Type
        inventory_types = Ref_Inventory_Type.objects.all().order_by('InventoryTypeName')
        types_data = []
        
        for inv_type in inventory_types:
            types_data.append({
                'InventoryTypeId': inv_type.InventoryTypeId,
                'InventoryTypeName': inv_type.InventoryTypeName
            })
        
        return JsonResponse({
            'success': True,
            'inventory_types': types_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def refmeasurements_json(request):
    """API endpoint to return measurement units as JSON for modal dropdowns"""
    try:
        from .models import Ref_Measurement
        measurements = Ref_Measurement.objects.all().order_by('MeasurementName')
        measurements_data = []
        
        for measurement in measurements:
            measurements_data.append({
                'MeasurementId': measurement.MeasurementId,
                'MeasurementName': measurement.MeasurementName
            })
        
        return JsonResponse({
            'success': True,
            'measurements': measurements_data
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
            import time
            cache_buster = int(time.time() * 1000)  # Current timestamp in milliseconds
            db_alias = get_current_db()
            try:
                with connections[db_alias].cursor() as cursor:
                    # Add cache-busting comment to force PostgreSQL to treat each query as unique
                    cursor.execute(
                        f"SELECT * FROM calculate_trial_balance(%s, %s) /* cache_bust: {cache_buster} */",
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
            finally:
                # Force-close the tenant database connection so next request gets a fresh connection
                connections[db_alias].close()
        
        context = {
            'trial_balance_data': trial_balance_data,
            'begin_date': begin_date,
            'end_date': end_date,
            'error_message': error_message,
        }
        
        response = render(request, 'core/trial_balance.html', context)
        # Add explicit no-cache headers to prevent browser caching
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        # Remove ETag and Last-Modified headers that can cause caching
        if 'ETag' in response:
            del response['ETag']
        if 'Last-Modified' in response:
            del response['Last-Modified']
        return response
        
    except Exception as e:
        context = {
            'trial_balance_data': [],
            'begin_date': begin_date if 'begin_date' in locals() else '',
            'end_date': end_date if 'end_date' in locals() else '',
            'error_message': f'Error generating trial balance: {str(e)}',
        }
        response = render(request, 'core/trial_balance.html', context)
        # Add explicit no-cache headers to prevent browser caching
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        # Remove ETag and Last-Modified headers that can cause caching
        if 'ETag' in response:
            del response['ETag']
        if 'Last-Modified' in response:
            del response['Last-Modified']
        return response
@login_required
def y_balance(request):
    """Y Balance Financial Statement Report View"""
    try:
        # Get date parameters from request
        begin_date = request.GET.get('begin_date', '')
        end_date = request.GET.get('end_date', '')
        active_tab = request.GET.get('active_tab', 'balance')
        
        st_balance_data = []
        st_income_data = []
        st_cashflow_data = []
        st_equity_data = []
        error_message = None
        
        # Check if this is a form submission (calculate parameter) or just tab switching
        # Only call calculation functions when explicitly requested via form submission
        calculate = request.GET.get('calculate', 'false').lower() == 'true'
        
        if begin_date and end_date and calculate:
            # Execute stored procedures only when "ТООЦООЛОХ" button is clicked (form submitted)
            # Functions now return data sets directly
            import time
            cache_buster = int(time.time() * 1000)  # Current timestamp in milliseconds
            db_alias = get_current_db()
            try:
                with connections[db_alias].cursor() as cursor:
                    # Column name mapping for St_Balance (PostgreSQL returns column names as defined in RETURNS TABLE)
                    # Since we use quoted identifiers, they preserve case, but we'll map to be safe
                    balance_column_mapping = {
                        'stbalanceid': 'StbalanceId',
                        'stbalancecode': 'StbalanceCode',
                        'stbalancename': 'StbalanceName',
                        'beginbalance': 'BeginBalance',
                        'endbalance': 'EndBalance',
                        'order': 'Order',
                        # Also handle exact case matches
                        'StbalanceId': 'StbalanceId',
                        'StbalanceCode': 'StbalanceCode',
                        'StbalanceName': 'StbalanceName',
                        'BeginBalance': 'BeginBalance',
                        'EndBalance': 'EndBalance',
                        'Order': 'Order'
                    }
                    
                    # Calculate St_Balance and get data
                    # Add cache-busting comment to force PostgreSQL to treat each query as unique
                    cursor.execute(
                        f"SELECT * FROM calculate_st_balance(%s, %s) /* cache_bust: {cache_buster} */",
                        [begin_date, end_date]
                    )
                    columns = [col[0] for col in cursor.description]
                    st_balance_data = []
                    for row in cursor.fetchall():
                        row_dict = {}
                        for i, col_name in enumerate(columns):
                            # Remove quotes if present and normalize
                            clean_col_name = col_name.strip('"').strip("'")
                            # Map column names to expected format (try exact match first, then lowercase)
                            mapped_name = balance_column_mapping.get(clean_col_name, balance_column_mapping.get(clean_col_name.lower(), clean_col_name))
                            row_dict[mapped_name] = row[i]
                        st_balance_data.append(row_dict)
                    
                    # Column name mapping for St_Income
                    income_column_mapping = {
                        'stincomeid': 'StIncomeId',
                        'stincome': 'StIncome',
                        'stincomename': 'StIncomeName',
                        'endbalance': 'EndBalance',
                        'order': 'Order',
                        # Also handle exact case matches
                        'StIncomeId': 'StIncomeId',
                        'StIncome': 'StIncome',
                        'StIncomeName': 'StIncomeName',
                        'EndBalance': 'EndBalance',
                        'Order': 'Order'
                    }
                    
                    # Calculate St_Income and get data
                    # Add cache-busting comment to force PostgreSQL to treat each query as unique
                    cursor.execute(
                        f"SELECT * FROM calculate_st_income(%s, %s) /* cache_bust: {cache_buster} */",
                        [begin_date, end_date]
                    )
                    columns = [col[0] for col in cursor.description]
                    st_income_data = []
                    for row in cursor.fetchall():
                        row_dict = {}
                        for i, col_name in enumerate(columns):
                            # Remove quotes if present and normalize
                            clean_col_name = col_name.strip('"').strip("'")
                            # Map column names to expected format
                            mapped_name = income_column_mapping.get(clean_col_name, income_column_mapping.get(clean_col_name.lower(), clean_col_name))
                            row_dict[mapped_name] = row[i]
                        st_income_data.append(row_dict)
                    
                    # Column name mapping for St_CashFlow
                    cashflow_column_mapping = {
                        'stcashflowid': 'StCashFlowId',
                        'stcashflowcode': 'StCashFlowCode',
                        'stcashflowname': 'StCashFlowName',
                        'endbalance': 'EndBalance',
                        'order': 'Order',
                        'isvisible': 'IsVisible',
                        # Also handle exact case matches
                        'StCashFlowId': 'StCashFlowId',
                        'StCashFlowCode': 'StCashFlowCode',
                        'StCashFlowName': 'StCashFlowName',
                        'EndBalance': 'EndBalance',
                        'Order': 'Order',
                        'IsVisible': 'IsVisible'
                    }
                    
                    # Calculate St_CashFlow and get data
                    # Add cache-busting comment to force PostgreSQL to treat each query as unique
                    cursor.execute(
                        f"SELECT * FROM calculate_st_cash_flow(%s, %s) /* cache_bust: {cache_buster} */",
                        [begin_date, end_date]
                    )
                    columns = [col[0] for col in cursor.description]
                    st_cashflow_data = []
                    for row in cursor.fetchall():
                        row_dict = {}
                        for i, col_name in enumerate(columns):
                            # Remove quotes if present and normalize
                            clean_col_name = col_name.strip('"').strip("'")
                            # Map column names to expected format
                            mapped_name = cashflow_column_mapping.get(clean_col_name, cashflow_column_mapping.get(clean_col_name.lower(), clean_col_name))
                            row_dict[mapped_name] = row[i]
                        st_cashflow_data.append(row_dict)
            finally:
                # Force-close the tenant database connection so next request gets a fresh connection
                connections[db_alias].close()
        elif begin_date and end_date:
            # If just switching tabs, query existing data from models
            # Convert QuerySet to list of dictionaries with proper field names
            st_balance_data = [
                {
                    'StbalanceId': item['StbalanceId'],
                    'StbalanceCode': item['StbalanceCode'],
                    'StbalanceName': item['StbalanceName'],
                    'BeginBalance': item['BeginBalance'],
                    'EndBalance': item['EndBalance'],
                    'Order': item['Order']
                }
                for item in St_Balance.objects.all().order_by('Order', 'StbalanceCode').values()
            ]
            st_income_data = [
                {
                    'StIncomeId': item['StIncomeId'],
                    'StIncome': item['StIncome'],
                    'StIncomeName': item['StIncomeName'],
                    'EndBalance': item['EndBalance'],
                    'Order': item['Order']
                }
                for item in St_Income.objects.all().order_by('Order', 'StIncome').values()
            ]
            st_cashflow_data = [
                {
                    'StCashFlowId': item['StCashFlowId'],
                    'StCashFlowCode': item['StCashFlowCode'],
                    'StCashFlowName': item['StCashFlowName'],
                    'EndBalance': item['EndBalance'],
                    'Order': item['Order'],
                    'IsVisible': item['IsVisible']
                }
                for item in St_CashFlow.objects.filter(IsVisible=True).order_by('Order', 'StCashFlowCode').values()
            ]
        
        context = {
            'st_balance_data': st_balance_data,
            'st_income_data': st_income_data,
            'st_cashflow_data': st_cashflow_data,
            'st_equity_data': st_equity_data,
            'begin_date': begin_date,
            'end_date': end_date,
            'active_tab': active_tab,
            'error_message': error_message,
        }
        
        response = render(request, 'core/y_balance.html', context)
        # Add explicit no-cache headers to prevent browser caching
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        # Remove ETag and Last-Modified headers that can cause caching
        if 'ETag' in response:
            del response['ETag']
        if 'Last-Modified' in response:
            del response['Last-Modified']
        return response
        
    except Exception as e:
        context = {
            'st_balance_data': [],
            'st_income_data': [],
            'st_cashflow_data': [],
            'st_equity_data': [],
            'begin_date': begin_date if 'begin_date' in locals() else '',
            'end_date': end_date if 'end_date' in locals() else '',
            'active_tab': active_tab if 'active_tab' in locals() else 'balance',
            'error_message': f'Error generating report: {str(e)}',
        }
        response = render(request, 'core/y_balance.html', context)
        # Add explicit no-cache headers to prevent browser caching
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        # Remove ETag and Last-Modified headers that can cause caching
        if 'ETag' in response:
            del response['ETag']
        if 'Last-Modified' in response:
            del response['Last-Modified']
        return response
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
            db_alias = get_current_db()
            try:
                with connections[db_alias].cursor() as cursor:
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
            finally:
                connections[db_alias].close()
        
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


@login_required
def account_statement(request):
    """Account Statement Report View"""
    try:
        # Get parameters from request
        account_id = request.GET.get('account_id')
        begin_date = request.GET.get('begin_date', '')
        end_date = request.GET.get('end_date', '')
        begin_balance_debit = request.GET.get('begin_balance_debit', '0')
        begin_balance_credit = request.GET.get('begin_balance_credit', '0')
        debit_total = request.GET.get('debit_total', '0')
        credit_total = request.GET.get('credit_total', '0')
        end_balance_debit = request.GET.get('end_balance_debit', '0')
        end_balance_credit = request.GET.get('end_balance_credit', '0')
        
        subsidiary_ledger_data = []
        account_info = None
        client_info = None  # Always None for account statement (no client filtering)
        summary = {
            'begin_balance_debit': 0,
            'begin_balance_credit': 0,
            'debit_total': 0,
            'credit_total': 0,
            'end_balance_debit': 0,
            'end_balance_credit': 0
        }
        error_message = None
        
        # Validate required parameters
        if not all([account_id, begin_date, end_date]):
            error_message = 'Account ID, begin date, and end date are required'
        else:
            try:
                account_id = int(account_id)
                # Get all summary values from request parameters (already calculated in trial_balance)
                summary['begin_balance_debit'] = float(begin_balance_debit or 0)
                summary['begin_balance_credit'] = float(begin_balance_credit or 0)
                summary['debit_total'] = float(debit_total or 0)
                summary['credit_total'] = float(credit_total or 0)
                summary['end_balance_debit'] = float(end_balance_debit or 0)
                summary['end_balance_credit'] = float(end_balance_credit or 0)
            except (ValueError, TypeError):
                error_message = 'Invalid account_id parameter'
            
            if not error_message:
                # Get account information
                try:
                    account_info = Ref_Account.objects.select_related('AccountTypeId').get(AccountId=account_id, IsDelete=False)
                except Ref_Account.DoesNotExist:
                    error_message = 'Account not found'
                
                # Execute the account statement function
                if not error_message:
                    try:
                        db_alias = get_current_db()
                        try:
                            with connections[db_alias].cursor() as cursor:
                                # Call SQL function with parameters (no ClientId)
                                # Cast date parameters to DATE type explicitly
                                cursor.execute(
                                    "SELECT * FROM report_account_statement(%s, %s::DATE, %s::DATE)",
                                    [account_id, begin_date, end_date]
                                )
                                
                                # Get column names
                                columns = [col[0] for col in cursor.description]
                                
                                # Fetch all results
                                results = cursor.fetchall()
                                
                                # Convert to list of dictionaries with proper column name mapping
                                # PostgreSQL returns column names in lowercase, but template expects mixed case
                                column_mapping = {
                                    'documentdate': 'DocumentDate',
                                    'documentno': 'DocumentNo',
                                    'documentid': 'DocumentId',
                                    'documenttypeid': 'DocumentTypeId',
                                    'documentsource': 'DocumentSource',
                                    'clientname': 'ClientName',
                                    'description': 'Description',
                                    'currencyname': 'CurrencyName',
                                    'currencyexchange': 'CurrencyExchange',
                                    'currencyamount': 'CurrencyAmount',
                                    'debitamount': 'DebitAmount',
                                    'creditamount': 'CreditAmount',
                                    'accountcode': 'AccountCode',
                                    'cashflowname': 'CashFlowName'
                                }
                                
                                subsidiary_ledger_data = []
                                for row in results:
                                    row_dict = {}
                                    for i, col_name in enumerate(columns):
                                        # Map lowercase column names to mixed case for template
                                        mapped_name = column_mapping.get(col_name.lower(), col_name)
                                        row_dict[mapped_name] = row[i]
                                    subsidiary_ledger_data.append(row_dict)
                                
                                # All summary values are already passed from trial_balance.html
                                # No need to calculate them again
                                
                                # Convert Decimal values to float for JSON serialization
                                from decimal import Decimal
                                for item in subsidiary_ledger_data:
                                    for key, value in item.items():
                                        if isinstance(value, Decimal):
                                            item[key] = float(value)
                        finally:
                            connections[db_alias].close()
                                    
                    except Exception as e:
                        error_message = f'Error executing account statement query: {str(e)}'
        
        context = {
            'subsidiary_ledger_data': subsidiary_ledger_data,
            'account_info': account_info,
            'client_info': client_info,
            'summary': summary,
            'account_id': account_id,
            'client_id': '',  # Empty string for account statement
            'begin_date': begin_date,
            'end_date': end_date,
            'error_message': error_message,
            'report_title': 'ДАНСНЫ ТАЙЛАН',
        }
        
        return render(request, 'core/trial_edit_account_and_sub_ledger.html', context)
        
    except Exception as e:
        context = {
            'subsidiary_ledger_data': [],
            'account_info': None,
            'client_info': None,
            'summary': {
                'begin_balance_debit': 0,
                'begin_balance_credit': 0,
                'debit_total': 0,
                'credit_total': 0,
                'end_balance_debit': 0,
                'end_balance_credit': 0
            },
            'account_id': request.GET.get('account_id', ''),
            'client_id': '',
            'begin_date': request.GET.get('begin_date', ''),
            'end_date': request.GET.get('end_date', ''),
            'error_message': f'Error generating account statement: {str(e)}',
            'report_title': 'ДАНСНЫ ТАЙЛАН',
        }
        return render(request, 'core/trial_edit_account_and_sub_ledger.html', context)


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
            db_alias = get_current_db()
            try:
                with connections[db_alias].cursor() as cursor:
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
                    COALESCE(cur."Currency_name", '') as currencyname,
                    COALESCE(cdd."CurrencyExchange", 1.0) as currencyexchange,
                    cdd."CurrencyAmount",
                    cdd."DebitAmount",
                    cdd."CreditAmount",
                    cdd."IsDebit",
                    'Cash' as DocumentCategory
                FROM cash_document cd
                INNER JOIN cash_document_detail cdd ON cd."DocumentId" = cdd."DocumentId"
                INNER JOIN ref_account a ON cdd."AccountId" = a."AccountId"
                LEFT JOIN ref_client c ON cdd."ClientId" = c."ClientId"
                LEFT JOIN ref_currency cur ON cdd."CurrencyId" = cur."CurrencyId"
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
                    COALESCE(cur."Currency_name", '') as currencyname,
                    COALESCE(idd."CurrencyExchange", 1.0) as currencyexchange,
                    idd."CurrencyAmount",
                    idd."DebitAmount",
                    idd."CreditAmount",
                    idd."IsDebit",
                    'Inventory' as DocumentCategory
                FROM inv_document id
                INNER JOIN inv_document_detail idd ON id."DocumentId" = idd."DocumentId"
                INNER JOIN ref_account a ON idd."AccountId" = a."AccountId"
                LEFT JOIN ref_client c ON idd."ClientId" = c."ClientId"
                LEFT JOIN ref_currency cur ON idd."CurrencyId" = cur."CurrencyId"
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
                    COALESCE(cur."Currency_name", '') as currencyname,
                    COALESCE(add."CurrencyExchange", 1.0) as currencyexchange,
                    add."CurrencyAmount",
                    add."DebitAmount",
                    add."CreditAmount",
                    add."IsDebit",
                    'Asset' as DocumentCategory
                FROM ast_document ad
                INNER JOIN ast_document_detail add ON ad."DocumentId" = add."DocumentId"
                INNER JOIN ref_account a ON add."AccountId" = a."AccountId"
                LEFT JOIN ref_client c ON add."ClientId" = c."ClientId"
                LEFT JOIN ref_currency cur ON add."CurrencyId" = cur."CurrencyId"
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
            finally:
                connections[db_alias].close()
            
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
                        'CurrencyName': detail.get('currencyname') or '',
                        'CurrencyExchange': float(detail.get('currencyexchange') or 1.0),
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
def subsidiary_ledger(request):
    """Subsidiary Ledger Report View"""
    try:
        # Get parameters from request
        account_id = request.GET.get('account_id')
        client_id = request.GET.get('client_id', '')
        begin_date = request.GET.get('begin_date', '')
        end_date = request.GET.get('end_date', '')
        begin_balance_debit = request.GET.get('begin_balance_debit', '0')
        begin_balance_credit = request.GET.get('begin_balance_credit', '0')
        debit_total = request.GET.get('debit_total', '0')
        credit_total = request.GET.get('credit_total', '0')
        end_balance_debit = request.GET.get('end_balance_debit', '0')
        end_balance_credit = request.GET.get('end_balance_credit', '0')
        
        subsidiary_ledger_data = []
        account_info = None
        client_info = None
        summary = {
            'begin_balance_debit': 0,
            'begin_balance_credit': 0,
            'debit_total': 0,
            'credit_total': 0,
            'end_balance_debit': 0,
            'end_balance_credit': 0
        }
        error_message = None
        
        # Validate required parameters
        if not all([account_id, begin_date, end_date]):
            error_message = 'Account ID, begin date, and end date are required'
        else:
            try:
                account_id = int(account_id)
                # Convert client_id to integer if provided
                if client_id:
                    try:
                        client_id = int(client_id)
                    except (ValueError, TypeError):
                        client_id = None
                else:
                    client_id = None
                
                # Get all summary values from request parameters (already calculated in trial_recpay_balance)
                summary['begin_balance_debit'] = float(begin_balance_debit or 0)
                summary['begin_balance_credit'] = float(begin_balance_credit or 0)
                summary['debit_total'] = float(debit_total or 0)
                summary['credit_total'] = float(credit_total or 0)
                summary['end_balance_debit'] = float(end_balance_debit or 0)
                summary['end_balance_credit'] = float(end_balance_credit or 0)
            except (ValueError, TypeError):
                error_message = 'Invalid account_id parameter'
            
            if not error_message:
                # Get account information
                try:
                    account_info = Ref_Account.objects.select_related('AccountTypeId').get(AccountId=account_id, IsDelete=False)
                except Ref_Account.DoesNotExist:
                    error_message = 'Account not found'
                
                # Get client information if client_id is provided
                if client_id and not error_message:
                    try:
                        client_info = RefClient.objects.get(ClientId=client_id, IsDelete=False)
                    except RefClient.DoesNotExist:
                        client_info = None
                
                # Execute the subsidiary ledger query
                if not error_message:
                    try:
                        db_alias = get_current_db()
                        try:
                            with connections[db_alias].cursor() as cursor:
                                # Use the same SQL query pattern as subsidiary_ledger_detail API
                                if client_id:
                                    # With client filter
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
                                        COALESCE(cur."Currency_name", '') as currencyname,
                                        COALESCE(cdd."CurrencyExchange", 1.0) as currencyexchange,
                                        cdd."CurrencyAmount",
                                        cdd."DebitAmount",
                                        cdd."CreditAmount",
                                        cdd."IsDebit",
                                        'Cash' as DocumentCategory
                                    FROM cash_document cd
                                    INNER JOIN cash_document_detail cdd ON cd."DocumentId" = cdd."DocumentId"
                                    INNER JOIN ref_account a ON cdd."AccountId" = a."AccountId"
                                    LEFT JOIN ref_client c ON cdd."ClientId" = c."ClientId"
                                    LEFT JOIN ref_currency cur ON cdd."CurrencyId" = cur."CurrencyId"
                                    INNER JOIN ref_document_type dt ON cd."DocumentTypeId" = dt."DocumentTypeId"
                                    WHERE cd."DocumentId" IN (
                                        SELECT DISTINCT "DocumentId" 
                                        FROM cash_document_detail 
                                        WHERE "AccountId" = %s AND "ClientId" = %s
                                    )
                                    AND cd."DocumentDate" >= %s 
                                    AND cd."DocumentDate" <= %s 
                                    AND cd."IsDelete" = false
                                    AND cdd."ClientId" = %s
                                    
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
                                        COALESCE(cur."Currency_name", '') as currencyname,
                                        COALESCE(idd."CurrencyExchange", 1.0) as currencyexchange,
                                        idd."CurrencyAmount",
                                        idd."DebitAmount",
                                        idd."CreditAmount",
                                        idd."IsDebit",
                                        'Inventory' as DocumentCategory
                                    FROM inv_document id
                                    INNER JOIN inv_document_detail idd ON id."DocumentId" = idd."DocumentId"
                                    INNER JOIN ref_account a ON idd."AccountId" = a."AccountId"
                                    LEFT JOIN ref_client c ON idd."ClientId" = c."ClientId"
                                    LEFT JOIN ref_currency cur ON idd."CurrencyId" = cur."CurrencyId"
                                    INNER JOIN ref_document_type dt ON id."DocumentTypeId" = dt."DocumentTypeId"
                                    WHERE id."DocumentId" IN (
                                        SELECT DISTINCT "DocumentId" 
                                        FROM inv_document_detail 
                                        WHERE "AccountId" = %s AND "ClientId" = %s
                                    )
                                    AND id."DocumentDate" >= %s 
                                    AND id."DocumentDate" <= %s 
                                    AND id."IsDelete" = false
                                    AND idd."ClientId" = %s
                                    
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
                                        COALESCE(cur."Currency_name", '') as currencyname,
                                        COALESCE(add."CurrencyExchange", 1.0) as currencyexchange,
                                        add."CurrencyAmount",
                                        add."DebitAmount",
                                        add."CreditAmount",
                                        add."IsDebit",
                                        'Asset' as DocumentCategory
                                    FROM ast_document ad
                                    INNER JOIN ast_document_detail add ON ad."DocumentId" = add."DocumentId"
                                    INNER JOIN ref_account a ON add."AccountId" = a."AccountId"
                                    LEFT JOIN ref_client c ON add."ClientId" = c."ClientId"
                                    LEFT JOIN ref_currency cur ON add."CurrencyId" = cur."CurrencyId"
                                    INNER JOIN ref_document_type dt ON ad."DocumentTypeId" = dt."DocumentTypeId"
                                    WHERE ad."DocumentId" IN (
                                        SELECT DISTINCT "DocumentId" 
                                        FROM ast_document_detail 
                                        WHERE "AccountId" = %s AND "ClientId" = %s
                                    )
                                    AND ad."DocumentDate" >= %s 
                                    AND ad."DocumentDate" <= %s 
                                    AND ad."IsDelete" = false
                                    AND add."ClientId" = %s
                                    
                                    ORDER BY "DocumentDate", "DocumentNo", "DocumentDetailId"
                                    """, 
                                    [account_id, client_id, begin_date, end_date, client_id,
                                     account_id, client_id, begin_date, end_date, client_id,
                                     account_id, client_id, begin_date, end_date, client_id])
                                else:
                                    # Without client filter
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
                                        COALESCE(cur."Currency_name", '') as currencyname,
                                        COALESCE(cdd."CurrencyExchange", 1.0) as currencyexchange,
                                        cdd."CurrencyAmount",
                                        cdd."DebitAmount",
                                        cdd."CreditAmount",
                                        cdd."IsDebit",
                                        'Cash' as DocumentCategory
                                    FROM cash_document cd
                                    INNER JOIN cash_document_detail cdd ON cd."DocumentId" = cdd."DocumentId"
                                    INNER JOIN ref_account a ON cdd."AccountId" = a."AccountId"
                                    LEFT JOIN ref_client c ON cdd."ClientId" = c."ClientId"
                                    LEFT JOIN ref_currency cur ON cdd."CurrencyId" = cur."CurrencyId"
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
                                        COALESCE(cur."Currency_name", '') as currencyname,
                                        COALESCE(idd."CurrencyExchange", 1.0) as currencyexchange,
                                        idd."CurrencyAmount",
                                        idd."DebitAmount",
                                        idd."CreditAmount",
                                        idd."IsDebit",
                                        'Inventory' as DocumentCategory
                                    FROM inv_document id
                                    INNER JOIN inv_document_detail idd ON id."DocumentId" = idd."DocumentId"
                                    INNER JOIN ref_account a ON idd."AccountId" = a."AccountId"
                                    LEFT JOIN ref_client c ON idd."ClientId" = c."ClientId"
                                    LEFT JOIN ref_currency cur ON idd."CurrencyId" = cur."CurrencyId"
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
                                        COALESCE(cur."Currency_name", '') as currencyname,
                                        COALESCE(add."CurrencyExchange", 1.0) as currencyexchange,
                                        add."CurrencyAmount",
                                        add."DebitAmount",
                                        add."CreditAmount",
                                        add."IsDebit",
                                        'Asset' as DocumentCategory
                                    FROM ast_document ad
                                    INNER JOIN ast_document_detail add ON ad."DocumentId" = add."DocumentId"
                                    INNER JOIN ref_account a ON add."AccountId" = a."AccountId"
                                    LEFT JOIN ref_client c ON add."ClientId" = c."ClientId"
                                    LEFT JOIN ref_currency cur ON add."CurrencyId" = cur."CurrencyId"
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
                                    """, 
                                    [account_id, begin_date, end_date,
                                     account_id, begin_date, end_date,
                                     account_id, begin_date, end_date])
                                
                                # Get column names
                                columns = [col[0] for col in cursor.description]
                                
                                # Fetch all results
                                results = cursor.fetchall()
                                
                                # Convert to list of dictionaries with proper column name mapping
                                column_mapping = {
                                    'documentdate': 'DocumentDate',
                                    'documentno': 'DocumentNo',
                                    'documentid': 'DocumentId',
                                    'documenttype': 'DocumentType',
                                    'documentdescription': 'Description',
                                    'documentcategory': 'DocumentCategory',
                                    'clientname': 'ClientName',
                                    'currencyname': 'CurrencyName',
                                    'currencyexchange': 'CurrencyExchange',
                                    'currencyamount': 'CurrencyAmount',
                                    'debitamount': 'DebitAmount',
                                    'creditamount': 'CreditAmount'
                                }
                                
                                # Map DocumentCategory to DocumentSource
                                for row in results:
                                    row_dict = {}
                                    document_category = None
                                    for i, col_name in enumerate(columns):
                                        mapped_name = column_mapping.get(col_name.lower(), col_name)
                                        value = row[i]
                                        
                                        if mapped_name == 'DocumentCategory':
                                            document_category = value
                                            # Map category to source
                                            if value == 'Cash':
                                                row_dict['DocumentSource'] = 'cash'
                                            elif value == 'Inventory':
                                                row_dict['DocumentSource'] = 'inv'
                                            elif value == 'Asset':
                                                row_dict['DocumentSource'] = 'ast'
                                            else:
                                                row_dict['DocumentSource'] = value.lower() if value else 'cash'
                                        else:
                                            row_dict[mapped_name] = value
                                    
                                    # Add DocumentTypeId (not available in query, set to None)
                                    row_dict['DocumentTypeId'] = None
                                    
                                    subsidiary_ledger_data.append(row_dict)
                                
                                # Convert Decimal values to float for JSON serialization
                                from decimal import Decimal
                                for item in subsidiary_ledger_data:
                                    for key, value in item.items():
                                        if isinstance(value, Decimal):
                                            item[key] = float(value)
                                        
                        finally:
                            connections[db_alias].close()
                    except Exception as e:
                        error_message = f'Error executing subsidiary ledger query: {str(e)}'
        
        context = {
            'subsidiary_ledger_data': subsidiary_ledger_data,
            'account_info': account_info,
            'client_info': client_info,
            'summary': summary,
            'account_id': account_id,
            'client_id': client_id or '',
            'begin_date': begin_date,
            'end_date': end_date,
            'error_message': error_message,
            'report_title': 'АВЛАГА ӨГЛӨГИЙН ТУСЛАХ ДЭВТЭР',
        }
        
        return render(request, 'core/trial_edit_account_and_sub_ledger.html', context)
        
    except Exception as e:
        context = {
            'subsidiary_ledger_data': [],
            'account_info': None,
            'client_info': None,
            'summary': {
                'begin_balance_debit': 0,
                'begin_balance_credit': 0,
                'debit_total': 0,
                'credit_total': 0,
                'end_balance_debit': 0,
                'end_balance_credit': 0
            },
            'account_id': request.GET.get('account_id', ''),
            'client_id': request.GET.get('client_id', ''),
            'begin_date': request.GET.get('begin_date', ''),
            'end_date': request.GET.get('end_date', ''),
            'error_message': f'Error generating subsidiary ledger: {str(e)}',
            'report_title': 'АВЛАГА ӨГЛӨГИЙН ТУСЛАХ ДЭВТЭР',
        }
        return render(request, 'core/trial_edit_account_and_sub_ledger.html', context)


@csrf_exempt
@login_required
def subsidiary_ledger_detail(request):
    """Subsidiary Ledger Detail API endpoint - Uses same pattern as account_statement_detail"""
    try:
        # Get parameters from request
        account_id = request.GET.get('account_id')
        client_id = request.GET.get('client_id', '')
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
        
        # Convert client_id to integer if provided
        if client_id:
            try:
                client_id = int(client_id)
            except (ValueError, TypeError):
                client_id = None
        else:
            client_id = None
        
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
        
        # Get client information if client_id is provided
        client_info = None
        if client_id:
            try:
                client = RefClient.objects.get(ClientId=client_id, IsDelete=False)
                client_info = {
                    'ClientId': client.ClientId,
                    'ClientCode': client.ClientCode,
                    'ClientName': client.ClientName
                }
            except RefClient.DoesNotExist:
                client_info = None
        
        # Get documents with all their details where at least one detail matches the account and client (if provided)
        try:
            db_alias = get_current_db()
            try:
                with connections[db_alias].cursor() as cursor:
                    # Build the SQL query with proper client filtering
                    if client_id:
                        # With client filter
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
                            COALESCE(cur."Currency_name", '') as currencyname,
                            COALESCE(cdd."CurrencyExchange", 1.0) as currencyexchange,
                            cdd."CurrencyAmount",
                            cdd."DebitAmount",
                            cdd."CreditAmount",
                            cdd."IsDebit",
                            'Cash' as DocumentCategory
                        FROM cash_document cd
                        INNER JOIN cash_document_detail cdd ON cd."DocumentId" = cdd."DocumentId"
                        INNER JOIN ref_account a ON cdd."AccountId" = a."AccountId"
                        LEFT JOIN ref_client c ON cdd."ClientId" = c."ClientId"
                        LEFT JOIN ref_currency cur ON cdd."CurrencyId" = cur."CurrencyId"
                        INNER JOIN ref_document_type dt ON cd."DocumentTypeId" = dt."DocumentTypeId"
                        WHERE cd."DocumentId" IN (
                            SELECT DISTINCT "DocumentId" 
                            FROM cash_document_detail 
                            WHERE "AccountId" = %s AND "ClientId" = %s
                        )
                        AND cd."DocumentDate" >= %s 
                        AND cd."DocumentDate" <= %s 
                        AND cd."IsDelete" = false
                        AND cdd."ClientId" = %s
                        
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
                            COALESCE(cur."Currency_name", '') as currencyname,
                            COALESCE(idd."CurrencyExchange", 1.0) as currencyexchange,
                            idd."CurrencyAmount",
                            idd."DebitAmount",
                            idd."CreditAmount",
                            idd."IsDebit",
                            'Inventory' as DocumentCategory
                        FROM inv_document id
                        INNER JOIN inv_document_detail idd ON id."DocumentId" = idd."DocumentId"
                        INNER JOIN ref_account a ON idd."AccountId" = a."AccountId"
                        LEFT JOIN ref_client c ON idd."ClientId" = c."ClientId"
                        LEFT JOIN ref_currency cur ON idd."CurrencyId" = cur."CurrencyId"
                        INNER JOIN ref_document_type dt ON id."DocumentTypeId" = dt."DocumentTypeId"
                        WHERE id."DocumentId" IN (
                            SELECT DISTINCT "DocumentId" 
                            FROM inv_document_detail 
                            WHERE "AccountId" = %s AND "ClientId" = %s
                        )
                        AND id."DocumentDate" >= %s 
                        AND id."DocumentDate" <= %s 
                        AND id."IsDelete" = false
                        AND idd."ClientId" = %s
                        
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
                            COALESCE(cur."Currency_name", '') as currencyname,
                            COALESCE(add."CurrencyExchange", 1.0) as currencyexchange,
                            add."CurrencyAmount",
                            add."DebitAmount",
                            add."CreditAmount",
                            add."IsDebit",
                            'Asset' as DocumentCategory
                        FROM ast_document ad
                        INNER JOIN ast_document_detail add ON ad."DocumentId" = add."DocumentId"
                        INNER JOIN ref_account a ON add."AccountId" = a."AccountId"
                        LEFT JOIN ref_client c ON add."ClientId" = c."ClientId"
                        LEFT JOIN ref_currency cur ON add."CurrencyId" = cur."CurrencyId"
                        INNER JOIN ref_document_type dt ON ad."DocumentTypeId" = dt."DocumentTypeId"
                        WHERE ad."DocumentId" IN (
                            SELECT DISTINCT "DocumentId" 
                            FROM ast_document_detail 
                            WHERE "AccountId" = %s AND "ClientId" = %s
                        )
                        AND ad."DocumentDate" >= %s 
                        AND ad."DocumentDate" <= %s 
                        AND ad."IsDelete" = false
                        AND add."ClientId" = %s
                        
                        ORDER BY "DocumentDate", "DocumentNo", "DocumentDetailId"
                        """, 
                        [account_id, client_id, begin_date, end_date, client_id,
                         account_id, client_id, begin_date, end_date, client_id,
                         account_id, client_id, begin_date, end_date, client_id])
                    else:
                        # Without client filter
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
                            COALESCE(cur."Currency_name", '') as currencyname,
                            COALESCE(cdd."CurrencyExchange", 1.0) as currencyexchange,
                            cdd."CurrencyAmount",
                            cdd."DebitAmount",
                            cdd."CreditAmount",
                            cdd."IsDebit",
                            'Cash' as DocumentCategory
                        FROM cash_document cd
                        INNER JOIN cash_document_detail cdd ON cd."DocumentId" = cdd."DocumentId"
                        INNER JOIN ref_account a ON cdd."AccountId" = a."AccountId"
                        LEFT JOIN ref_client c ON cdd."ClientId" = c."ClientId"
                        LEFT JOIN ref_currency cur ON cdd."CurrencyId" = cur."CurrencyId"
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
                            COALESCE(cur."Currency_name", '') as currencyname,
                            COALESCE(idd."CurrencyExchange", 1.0) as currencyexchange,
                            idd."CurrencyAmount",
                            idd."DebitAmount",
                            idd."CreditAmount",
                            idd."IsDebit",
                            'Inventory' as DocumentCategory
                        FROM inv_document id
                        INNER JOIN inv_document_detail idd ON id."DocumentId" = idd."DocumentId"
                        INNER JOIN ref_account a ON idd."AccountId" = a."AccountId"
                        LEFT JOIN ref_client c ON idd."ClientId" = c."ClientId"
                        LEFT JOIN ref_currency cur ON idd."CurrencyId" = cur."CurrencyId"
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
                            COALESCE(cur."Currency_name", '') as currencyname,
                            COALESCE(add."CurrencyExchange", 1.0) as currencyexchange,
                            add."CurrencyAmount",
                            add."DebitAmount",
                            add."CreditAmount",
                            add."IsDebit",
                            'Asset' as DocumentCategory
                        FROM ast_document ad
                        INNER JOIN ast_document_detail add ON ad."DocumentId" = add."DocumentId"
                        INNER JOIN ref_account a ON add."AccountId" = a."AccountId"
                        LEFT JOIN ref_client c ON add."ClientId" = c."ClientId"
                        LEFT JOIN ref_currency cur ON add."CurrencyId" = cur."CurrencyId"
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
                        """, 
                        [account_id, begin_date, end_date,
                         account_id, begin_date, end_date,
                         account_id, begin_date, end_date])
                    
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
                        
                        # Add detail to document (only include details that match the account)
                        if detail['AccountCode'] == account.AccountCode:
                            detail_info = {
                                'DetailId': detail['DocumentDetailId'],
                                'AccountCode': detail['AccountCode'],
                                'AccountName': detail['AccountName'],
                                'ClientCode': detail['clientcode'],
                                'ClientName': detail['clientname'],
                                'CurrencyName': detail.get('currencyname') or '',
                                'CurrencyExchange': float(detail.get('currencyexchange') or 1.0),
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
                        'client': client_info,
                        'total_debit': float(total_debit),
                        'total_credit': float(total_credit),
                        'documents': documents_list,
                        'date_range': {
                            'begin_date': begin_date,
                            'end_date': end_date
                        }
                    })
            finally:
                connections[db_alias].close()
        except Exception as e:
            print(f"SQL Error in subsidiary_ledger_detail: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Database error: {str(e)}'
            }, status=500)
        
    except Exception as e:
        print(f"Error in subsidiary_ledger_detail: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error generating subsidiary ledger: {str(e)}'
        }, status=500)
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
def api_templates_by_account_code(request):
    """API endpoint to get templates filtered by AccountCode (optional) and DocumentTypeIds (optional)"""
    try:
        account_code = request.GET.get('account_code')
        document_type_ids_param = request.GET.get('document_type_ids')
        
        # Build query
        templates_query = Ref_Template.objects.filter(IsDelete=False)
        
        # Filter by AccountCode if provided
        if account_code:
            try:
                account = Ref_Account.objects.get(AccountCode=account_code, IsDelete=False)
                templates_query = templates_query.filter(AccountId=account)
            except Ref_Account.DoesNotExist:
                # Account not found, return empty list
                return JsonResponse({
                    'success': True,
                    'templates': []
                })
        
        # Filter by DocumentTypeIds if provided
        if document_type_ids_param:
            try:
                document_type_ids = [int(x.strip()) for x in document_type_ids_param.split(',') if x.strip().isdigit()]
                if document_type_ids:
                    templates_query = templates_query.filter(DocumentTypeId__DocumentTypeId__in=document_type_ids)
            except (ValueError, AttributeError):
                pass  # Ignore invalid document_type_ids parameter
        
        templates = templates_query.select_related('AccountId', 'DocumentTypeId').order_by('TemplateName')
        
        templates_data = []
        for template in templates:
            templates_data.append({
                'TemplateId': template.TemplateId,
                'TemplateName': template.TemplateName,
                'AccountId': template.AccountId.AccountId if template.AccountId else None,
                'AccountCode': template.AccountId.AccountCode if template.AccountId else None,
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
                'AccountId': detail.AccountId.AccountId if detail.AccountId else None,
                'AccountCode': detail.AccountId.AccountCode if detail.AccountId else None,
                'AccountName': detail.AccountId.AccountName if detail.AccountId else None,
                'AccountTypeId': detail.AccountId.AccountTypeId.AccountTypeId if detail.AccountId and detail.AccountId.AccountTypeId else None,
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
@permission_required('core.add_cash_document', raise_exception=True)
@require_http_methods(["POST"])
def api_cash_import_bulk(request):
    """API endpoint for bulk importing cash documents"""
    from django.db import transaction
    import json
    
    try:
        data = json.loads(request.body)
        rows = data.get('rows', [])
        
        if not rows or len(rows) == 0:
            return JsonResponse({
                'success': False,
                'message': 'No rows provided for import'
            }, status=400)
        
        # Pre-validation: Check all required fields before starting transaction
        errors = []
        validated_rows = []
        
        for i, row in enumerate(rows):
            # Validate required fields
            if not row.get('DocumentTypeId'):
                errors.append(f'Row {i + 1}: DocumentTypeId is required')
                continue
            if not row.get('DocumentDate'):
                errors.append(f'Row {i + 1}: DocumentDate is required')
                continue
            if not row.get('Description'):
                errors.append(f'Row {i + 1}: Description is required')
                continue
            if not row.get('ClientId'):
                errors.append(f'Row {i + 1}: ClientId is required')
                continue
            if not row.get('AccountCode'):
                errors.append(f'Row {i + 1}: AccountCode is required')
                continue
            
            # Lookup AccountId from AccountCode
            try:
                account = Ref_Account.objects.get(AccountCode=row['AccountCode'], IsDelete=False)
                row['AccountId'] = account.AccountId
            except Ref_Account.DoesNotExist:
                errors.append(f'Row {i + 1}: AccountCode "{row["AccountCode"]}" not found')
                continue
            
            # Validate DocumentTypeId exists
            try:
                doc_type = Ref_Document_Type.objects.get(DocumentTypeId=row['DocumentTypeId'])
            except Ref_Document_Type.DoesNotExist:
                errors.append(f'Row {i + 1}: DocumentTypeId {row["DocumentTypeId"]} not found')
                continue
            
            # Validate ClientId exists
            try:
                client = RefClient.objects.get(ClientId=row['ClientId'], IsDelete=False)
            except RefClient.DoesNotExist:
                errors.append(f'Row {i + 1}: ClientId {row["ClientId"]} not found')
                continue
            
            # Calculate amounts
            debit_amount = float(row.get('DebitAmount', 0))
            credit_amount = float(row.get('CreditAmount', 0))
            currency_amount = debit_amount + credit_amount
            currency_mnt = debit_amount + credit_amount
            
            # Get TemplateId (can be null)
            template_id = row.get('TemplateId') if row.get('TemplateId') else None
            if template_id:
                try:
                    template = Ref_Template.objects.get(TemplateId=template_id, IsDelete=False)
                except Ref_Template.DoesNotExist:
                    template_id = None  # Ignore invalid TemplateId
            
            validated_rows.append({
                'row_index': i,
                'DocumentTypeId': row['DocumentTypeId'],
                'DocumentDate': row['DocumentDate'],
                'Description': row['Description'],
                'ClientId': row['ClientId'],
                'AccountId': account.AccountId,
                'TemplateId': template_id,
                'IsVat': bool(row.get('IsVat', False)),
                'CurrencyAmount': currency_amount,
                'CurrencyMNT': currency_mnt
            })
        
        # If any validation errors, return without creating any records
        if errors:
            return JsonResponse({
                'success': False,
                'message': 'Validation errors found',
                'errors': errors
            }, status=400)
        
        # All rows validated, proceed with transaction
        imported_count = 0
        document_numbers = []
        
        try:
            with transaction.atomic():
                for validated_row in validated_rows:
                    # Generate DocumentNo
                    document_type_id = validated_row['DocumentTypeId']
                    last_counter = Ref_Document_Counter.objects.filter(
                        DocumentTypeId=document_type_id
                    ).order_by('-DocumentNo').first()
                    
                    if last_counter:
                        import re
                        match = re.search(r'(\d+)$', last_counter.DocumentNo)
                        if match:
                            next_number = int(match.group(1)) + 1
                            prefix = last_counter.DocumentNo[:match.start()]
                            next_document_no = f"{prefix}{next_number:04d}"
                        else:
                            next_document_no = f"{last_counter.DocumentNo}001"
                    else:
                        doc_type = Ref_Document_Type.objects.get(DocumentTypeId=document_type_id)
                        prefix = doc_type.DocumentTypeCode[:4] if doc_type.DocumentTypeCode else "DOC"
                        next_document_no = f"{prefix}0001"
                    
                    document_numbers.append(next_document_no)
                    
                    # Create Cash_Document
                    cash_document = Cash_Document(
                        DocumentNo=next_document_no,
                        DocumentTypeId_id=validated_row['DocumentTypeId'],
                        DocumentDate=validated_row['DocumentDate'],
                        Description=validated_row['Description'],
                        IsLock=False,
                        IsDelete=False,
                        ModifiedBy=request.user,
                        CreatedBy=request.user,
                        ClientBankId=None,
                        CurrencyAmount=validated_row['CurrencyAmount'],
                        IsVat=validated_row['IsVat'],
                        IsPosted=False,
                        CurrencyId_id=1,  # MNT currency
                        ClientId_id=validated_row['ClientId'],
                        PaidClientId=None,
                        CurrencyExchange=1,
                        CurrencyMNT=validated_row['CurrencyMNT'],
                        AccountId_id=validated_row['AccountId'],
                        TemplateId_id=validated_row['TemplateId']
                    )
                    cash_document.save()
                    
                    # Create Ref_Document_Counter
                    Ref_Document_Counter.objects.create(
                        DocumentNo=next_document_no,
                        DocumentTypeId_id=document_type_id,
                        CreatedBy=request.user
                    )
                    
                    imported_count += 1
                
                # All rows imported successfully
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully imported {imported_count} document(s)',
                    'count': imported_count,
                    'document_numbers': document_numbers
                })
                
        except Exception as e:
            # Transaction will rollback automatically
            return JsonResponse({
                'success': False,
                'message': f'Error during import: {str(e)}'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Unexpected error: {str(e)}'
        }, status=500)


@login_required
@permission_required('core.add_cash_document', raise_exception=True)
@require_http_methods(["POST"])
def api_exchange_rate_adjustment_bulk(request):
    """API endpoint for bulk creating exchange rate adjustment documents"""
    from django.db import transaction
    import json
    import re
    from .models import Ref_Constant, Ref_Account, RefClient, Ref_Document_Type, Ref_Document_Counter, Cash_Document, Cash_DocumentDetail
    
    try:
        data = json.loads(request.body)
        rows = data.get('rows', [])  # Array of selected rows
        document_date = data.get('document_date')  # End date from filter
        
        if not rows or not document_date:
            return JsonResponse({
                'success': False,
                'message': 'Missing required data: rows and document_date are required'
            }, status=400)
        
        # Parse document_date to ensure it's a date object
        from datetime import datetime
        try:
            document_date_obj = datetime.strptime(document_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid document_date format. Use YYYY-MM-DD format.'
            }, status=400)
        
        # Get exchange gain/loss accounts from ref_constant
        try:
            gain_constant = Ref_Constant.objects.get(ConstantID=11)
            loss_constant = Ref_Constant.objects.get(ConstantID=12)
            gain_account_id = int(gain_constant.ConstantName)  # Convert ConstantName to integer
            loss_account_id = int(loss_constant.ConstantName)  # Convert ConstantName to integer
        except (Ref_Constant.DoesNotExist, ValueError) as e:
            return JsonResponse({
                'success': False,
                'message': f'Error getting exchange accounts from constants: {str(e)}'
            }, status=400)
        
        # Validate accounts exist
        try:
            gain_account = Ref_Account.objects.get(AccountId=gain_account_id, IsDelete=False)
            loss_account = Ref_Account.objects.get(AccountId=loss_account_id, IsDelete=False)
        except Ref_Account.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Exchange gain/loss accounts not found'
            }, status=400)
        
        # Document type ID = 12 (no validation needed)
        document_type_id = 12
        
        # Pre-validate all rows before transaction
        validated_rows = []
        errors = []
        
        for i, row in enumerate(rows):
            # Validate required fields
            if not row.get('accountcode'):
                errors.append(f'Row {i + 1}: AccountCode is required')
                continue
            if not row.get('clientcode'):
                errors.append(f'Row {i + 1}: ClientCode is required')
                continue
            if row.get('profit', 0) == 0 and row.get('loss', 0) == 0:
                errors.append(f'Row {i + 1}: Both profit and loss are zero, skipping')
                continue
            
            # Lookup AccountId from AccountCode
            try:
                account = Ref_Account.objects.get(AccountCode=row['accountcode'], IsDelete=False)
            except Ref_Account.DoesNotExist:
                errors.append(f'Row {i + 1}: AccountCode "{row["accountcode"]}" not found')
                continue
            
            # Lookup ClientId from ClientCode
            try:
                client = RefClient.objects.get(ClientCode=row['clientcode'], IsDelete=False)
            except RefClient.DoesNotExist:
                errors.append(f'Row {i + 1}: ClientCode "{row["clientcode"]}" not found')
                continue
            
            # Parse amounts
            profit = float(row.get('profit', 0)) or 0
            loss = float(row.get('loss', 0)) or 0
            
            if profit == 0 and loss == 0:
                continue  # Skip rows with no adjustment
            
            validated_rows.append({
                'row_index': i,
                'AccountId': account.AccountId,
                'AccountTypeId': int(row.get('accounttypeid')) if row.get('accounttypeid') else None,
                'ClientId': client.ClientId,
                'Profit': profit,
                'Loss': loss
            })
        
        # If any validation errors, return without creating any records
        if errors:
            return JsonResponse({
                'success': False,
                'message': 'Validation errors found',
                'errors': errors
            }, status=400)
        
        if not validated_rows:
            return JsonResponse({
                'success': False,
                'message': 'No valid rows to process'
            }, status=400)
        
        # All rows validated, proceed with transaction
        created_count = 0
        document_numbers = []
        deleted_count = 0
        
        try:
            with transaction.atomic():
                # Check for existing currency adjustment records and HARD DELETE them
                # DocumentTypeId=12 and DocumentDate=document_date
                existing_documents = Cash_Document.objects.filter(
                    DocumentTypeId=document_type_id,
                    DocumentDate=document_date_obj,
                    IsDelete=False  # Only check non-deleted records
                )
                
                if existing_documents.exists():
                    # Get document IDs for deletion
                    existing_document_ids = list(existing_documents.values_list('DocumentId', flat=True))
                    deleted_count = len(existing_document_ids)
                    
                    # Hard delete Cash_DocumentDetail records first (due to foreign key constraint)
                    Cash_DocumentDetail.objects.filter(
                        DocumentId__in=existing_document_ids
                    ).delete()
                    
                    # Hard delete Cash_Document records
                    existing_documents.delete()
                
                # Get document counter for this document type
                last_counter = Ref_Document_Counter.objects.filter(
                    DocumentTypeId=document_type_id
                ).order_by('-DocumentNo').first()
                
                for idx, validated_row in enumerate(validated_rows):
                    # Generate DocumentNo
                    if last_counter:
                        match = re.search(r'(\d+)$', last_counter.DocumentNo)
                        if match:
                            next_number = int(match.group(1)) + 1 + idx
                            prefix = last_counter.DocumentNo[:match.start()]
                            next_document_no = f"{prefix}{next_number:04d}"
                        else:
                            next_document_no = f"{last_counter.DocumentNo}{idx+1:03d}"
                    else:
                        # Get document type for prefix
                        try:
                            doc_type = Ref_Document_Type.objects.get(DocumentTypeId=document_type_id)
                            prefix = doc_type.DocumentTypeCode[:4] if doc_type.DocumentTypeCode else "EXCH"
                        except:
                            prefix = "EXCH"
                        next_document_no = f"{prefix}{idx+1:04d}"
                    
                    # Determine if profit or loss
                    is_profit = validated_row['Profit'] > 0
                    is_loss = validated_row['Loss'] > 0
                    
                    # Amount for document (Profit if profit, Loss if loss)
                    amount = validated_row['Profit'] if is_profit else validated_row['Loss']
                    is_debit = is_profit  # Profit = debit account, Loss = credit account
                    
                    # Create Cash_Document
                    # currencyExchange = 1, currencyId = 1, CurrencyMNT = amount, CurrencyAmount = amount
                    cash_document = Cash_Document(
                        DocumentNo=next_document_no,
                        DocumentTypeId_id=document_type_id,
                        DocumentDate=document_date_obj,
                        Description=f'Валютын ханшийн зөрүүний тохируулга',
                        IsLock=False,
                        IsDelete=False,
                        ModifiedBy=request.user,
                        CreatedBy=request.user,
                        ClientId_id=validated_row['ClientId'],
                        CurrencyId_id=1,  # Always 1 (MNT)
                        CurrencyAmount=amount,
                        CurrencyExchange=1.0,  # Always 1
                        CurrencyMNT=amount,
                        IsVat=False,
                        IsPosted=False,
                        AccountId_id=validated_row['AccountId'],
                        TemplateId=None
                    )
                    cash_document.save()
                    
                    # Create Ref_Document_Counter
                    Ref_Document_Counter.objects.create(
                        DocumentNo=next_document_no,
                        DocumentTypeId_id=document_type_id,
                        CreatedBy=request.user
                    )
                    
                    # Determine CashFlowId based on AccountTypeId
                    cash_flow_id = None
                    account_type_id = validated_row.get('AccountTypeId')
                    if account_type_id in [1, 2]:  # Cash accounts
                        if is_debit:
                            cash_flow_id = 55
                        else:
                            cash_flow_id = 56
                    
                    # Prepare Cash_DocumentDetail entries
                    details_to_create = []
                    
                    if is_profit:
                        # Profit case: Debit Account, Credit Gain Account
                        # Entry 1: Debit the account
                        details_to_create.append(Cash_DocumentDetail(
                            DocumentId=cash_document,
                            AccountId_id=validated_row['AccountId'],
                            ClientId_id=validated_row['ClientId'],
                            CurrencyId_id=1,  # Always 1 (MNT)
                            CurrencyExchange=1.0,  # Always 1
                            CurrencyAmount=validated_row['Profit'],
                            IsDebit=True,
                            DebitAmount=validated_row['Profit'],
                            CreditAmount=0,
                            ContractId=None,
                            CashFlowId_id=cash_flow_id
                        ))
                        # Entry 2: Credit gain account
                        details_to_create.append(Cash_DocumentDetail(
                            DocumentId=cash_document,
                            AccountId_id=gain_account_id,
                            ClientId_id=validated_row['ClientId'],
                            CurrencyId_id=1,  # Always 1 (MNT)
                            CurrencyExchange=1.0,  # Always 1
                            CurrencyAmount=validated_row['Profit'],
                            IsDebit=False,
                            DebitAmount=0,
                            CreditAmount=validated_row['Profit'],
                            ContractId=None,
                            CashFlowId=None
                        ))
                    elif is_loss:
                        # Loss case: Credit Account, Debit Loss Account
                        # Entry 1: Credit the account
                        details_to_create.append(Cash_DocumentDetail(
                            DocumentId=cash_document,
                            AccountId_id=validated_row['AccountId'],
                            ClientId_id=validated_row['ClientId'],
                            CurrencyId_id=1,  # Always 1 (MNT)
                            CurrencyExchange=1.0,  # Always 1
                            CurrencyAmount=validated_row['Loss'],
                            IsDebit=False,
                            DebitAmount=0,
                            CreditAmount=validated_row['Loss'],
                            ContractId=None,
                            CashFlowId_id=cash_flow_id
                        ))
                        # Entry 2: Debit loss account
                        details_to_create.append(Cash_DocumentDetail(
                            DocumentId=cash_document,
                            AccountId_id=loss_account_id,
                            ClientId_id=validated_row['ClientId'],
                            CurrencyId_id=1,  # Always 1 (MNT)
                            CurrencyExchange=1.0,  # Always 1
                            CurrencyAmount=validated_row['Loss'],
                            IsDebit=True,
                            DebitAmount=validated_row['Loss'],
                            CreditAmount=0,
                            ContractId=None,
                            CashFlowId=None
                        ))
                    
                    # Bulk create document details
                    if details_to_create:
                        Cash_DocumentDetail.objects.bulk_create(details_to_create)
                    
                    created_count += 1
                    document_numbers.append(next_document_no)
                
                # All rows imported successfully
                message = f'Successfully created {created_count} document(s)'
                if deleted_count > 0:
                    message += f'. Deleted {deleted_count} existing document(s) for the same period.'
                
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'count': created_count,
                    'deleted_count': deleted_count,
                    'document_numbers': document_numbers
                })
                
        except Exception as e:
            # Transaction will rollback automatically
            import traceback
            return JsonResponse({
                'success': False,
                'message': f'Error during creation: {str(e)}',
                'traceback': traceback.format_exc()
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'message': f'Unexpected error: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=500)
def api_account_lookup_by_code(request):
    """API endpoint to look up Ref_Account by AccountCode (case-insensitive exact match)"""
    account_code = request.GET.get('account_code')
    
    if not account_code:
        return JsonResponse({
            'success': False,
            'message': 'AccountCode is required'
        }, status=400)
    
    try:
        account = Ref_Account.objects.get(
            AccountCode__iexact=account_code,
            IsDelete=False
        )
        
        return JsonResponse({
            'success': True,
            'account': {
                'AccountId': account.AccountId,
                'AccountCode': account.AccountCode,
                'AccountName': account.AccountName
            }
        })
    except Ref_Account.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': f'Account with code "{account_code}" not found'
        }, status=404)
    except Ref_Account.MultipleObjectsReturned:
        # Should not happen with unique constraint, but handle gracefully
        account = Ref_Account.objects.filter(
            AccountCode__iexact=account_code,
            IsDelete=False
        ).first()
        return JsonResponse({
            'success': True,
            'account': {
                'AccountId': account.AccountId,
                'AccountCode': account.AccountCode,
                'AccountName': account.AccountName
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error looking up account: {str(e)}'
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
@permission_required('core.view_invdocument', raise_exception=True)
def get_inventory_documents_master(request):
    """API endpoint for inventory documents master table with date range filtering"""
    try:
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        selected_document = request.GET.get('selected_document', '')
        
        documents_query = Inv_Document.objects.select_related(
            'DocumentTypeId', 'ClientId', 'AccountId', 'WarehouseId', 'CreatedBy'
        ).filter(IsDelete=False)
        
        # If selected_document is provided, filter to only that document
        # This takes priority and will return a single record
        if selected_document and selected_document.strip():
            try:
                document_id = int(selected_document)
                documents_query = documents_query.filter(DocumentId=document_id)
                # Also apply date range filter if provided (ensures document is within range)
                if start_date:
                    documents_query = documents_query.filter(DocumentDate__gte=start_date)
                if end_date:
                    documents_query = documents_query.filter(DocumentDate__lte=end_date)
            except (ValueError, TypeError):
                documents_query = documents_query.none()
        else:
            # Normal filtering: apply date range if provided
            if start_date:
                documents_query = documents_query.filter(DocumentDate__gte=start_date)
            if end_date:
                documents_query = documents_query.filter(DocumentDate__lte=end_date)
        
        documents_query = documents_query.order_by('-DocumentId')
        
        documents_data = []
        for doc in documents_query:
            try:
                documents_data.append({
                    'DocumentId': doc.DocumentId,
                    'DocumentNo': doc.DocumentNo or '',
                    'DocumentTypeId': doc.DocumentTypeId.DocumentTypeId if doc.DocumentTypeId else None,
                    'DocumentTypeCode': doc.DocumentTypeId.DocumentTypeCode if doc.DocumentTypeId else '',
                    'ClientName': doc.ClientId.ClientName if doc.ClientId else '',
                    'ClientRegister': doc.ClientId.ClientRegister if doc.ClientId else '',
                    'DocumentDate': doc.DocumentDate.strftime('%Y-%m-%d') if doc.DocumentDate else '',
                    'Description': doc.Description or '',
                    'AccountCode': doc.AccountId.AccountCode if doc.AccountId else '',
                    'AccountName': doc.AccountId.AccountName if doc.AccountId else '',
                    'IsVat': bool(doc.IsVat) if doc.IsVat is not None else False,
                    'WarehouseCode': doc.WarehouseId.WarehouseCode if doc.WarehouseId else '',
                    'WarehouseName': doc.WarehouseId.WarehouseName if doc.WarehouseId else '',
                    'CostAmount': float(doc.CostAmount) if doc.CostAmount is not None else 0,
                    'PriceAmount': float(doc.PriceAmount) if doc.PriceAmount is not None else 0,
                    'CreatedByUsername': doc.CreatedBy.username if doc.CreatedBy else '',
                    'CreatedById': doc.CreatedBy.id if doc.CreatedBy else None,
                })
            except Exception as doc_error:
                logger.error(f"Error processing document {doc.DocumentId}: {str(doc_error)}")
                continue
        
        return JsonResponse({
            'success': True,
            'documents': documents_data,
            'count': len(documents_data)
        })
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error in get_inventory_documents_master: {str(e)}\n{error_trace}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@permission_required('core.view_ast_document', raise_exception=True)
def get_asset_documents_master(request):
    """API endpoint for asset documents master table with date range filtering"""
    try:
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        documents_query = Ast_Document.objects.select_related(
            'DocumentTypeId', 'ClientId', 'AccountId', 'CreatedBy'
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
                'IsVat': bool(doc.IsVat),
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
        logger.error(f"Error in get_asset_documents_master: {str(e)}")
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
        'DocumentTypeId', 'AccountId', 'CreatedBy'
    ).filter(IsDelete=False).order_by('-CreatedDate')
    
    # Get selected template ID for detail grids (AJAX request)
    selected_template_id = request.GET.get('selected_template')
    selected_template = None
    template_details = []
    
    if selected_template_id:
        try:
            selected_template = Ref_Template.objects.select_related(
                'DocumentTypeId', 'AccountId', 'CreatedBy'
            ).filter(IsDelete=False).get(TemplateId=selected_template_id)
            
            template_details = Ref_Template_Detail.objects.select_related(
                'AccountId', 'TemplateId', 'CashFlowId'
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
            # Ensure hard default: keep active on create
            template.IsDelete = False
            template.save()
            
            messages.success(request, 'Template created successfully.')
            return redirect('core:template_master_detail')
    else:
        form = Ref_TemplateForm()
    
    return render(request, 'core/template_form.html', {
        'form': form,
        'title': 'Загвар нэмэх',
        'submit_text': 'Нэмэх'
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
            # Ensure remains active unless explicitly deleted via delete action
            template.IsDelete = False
            template.save()
            messages.success(request, 'Template updated successfully.')
            return redirect('core:template_master_detail')
    else:
        form = Ref_TemplateForm(instance=template)
    
    return render(request, 'core/template_form.html', {
        'form': form,
        'title': 'Загвар засах',
        'submit_text': 'Шинэчлэх'
    })


@login_required
@permission_required('core.delete_ref_template', raise_exception=True)
def template_delete(request, pk):
    """Delete a template"""
    template = get_object_or_404(Ref_Template, pk=pk, IsDelete=False)
    
    # Check if user owns this template
    if template.CreatedBy != request.user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to delete this template.'
            }, status=403)
        messages.error(request, 'You do not have permission to delete this template.')
        return redirect('core:template_master_detail')
    
    # Check if template is used in any documents
    is_used_in_cash = Cash_Document.objects.filter(TemplateId=template, IsDelete=False).exists()
    is_used_in_inv = Inv_Document.objects.filter(TemplateId=template, IsDelete=False).exists()
    is_used_in_ast = Ast_Document.objects.filter(TemplateId=template, IsDelete=False).exists()
    
    if is_used_in_cash or is_used_in_inv or is_used_in_ast:
        error_message = 'Энэ загвараар гүйлгээ хийсэн байна. Эхлээд гүйлгээгээ устгана уу'
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': error_message
            }, status=400)
        
        # For regular POST requests, show error message and redirect
        messages.error(request, error_message)
        return redirect('core:template_master_detail')
    
    # Template is not used, proceed with deletion
        template.IsDelete = True
        template.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Template deleted successfully.'
        })
    
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
        'title': 'Загварын данс нэмэх',
        'submit_text': 'Нэмэх'
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
        'title': 'Загварын мөр шинэчлэх',
        'submit_text': 'Хадгалах'
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
