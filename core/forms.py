from django import forms
from .models import Ref_Account_Type, Ref_Account, RefClientType, RefClient, Ref_Currency, Ref_Inventory_Type, Ref_Measurement, RefInventory, Ref_Document_Type, Ref_Warehouse, Cash_Document, Cash_DocumentDetail, Inv_Document, Inv_Document_Item, Ref_Client_Bank, RefAsset, Ref_Asset_Type, Ref_Asset_Card, Inv_Beginning_Balance, Ast_Document, Ast_Document_Item, Ast_Document_Detail, Ref_Asset_Depreciation_Account, Ref_Template, Ref_Template_Detail, Ref_CashFlow


class ClientBankIdSelect(forms.Select):
    """Custom select widget for Client Bank Account with client ID data attributes"""
    
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        
        # Add client ID as data attribute for JavaScript filtering
        if value and value != '':
            try:
                # Extract the actual value from ModelChoiceIteratorValue if needed
                actual_value = value
                if hasattr(value, 'value'):
                    actual_value = value.value
                
                bank_account = Ref_Client_Bank.objects.get(ClientBankId=actual_value)
                option['attrs']['data-client-id'] = str(bank_account.ClientId.ClientId)
            except (Ref_Client_Bank.DoesNotExist, ValueError, TypeError):
                pass
        
        return option


class Ref_AccountForm(forms.ModelForm):
    """Form for creating and editing accounts"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configure foreign key fields with proper querysets
        self.fields['AccountTypeId'].queryset = Ref_Account_Type.objects.all().order_by('AccountTypeCode')
        self.fields['CurrencyId'].queryset = Ref_Currency.objects.filter(IsActive=True).order_by('CurrencyId')
        
        # Make all fields required
        self.fields['AccountCode'].required = True
        self.fields['AccountName'].required = True
        self.fields['AccountTypeId'].required = True
        self.fields['CurrencyId'].required = True
        
        # Add empty choice for AccountTypeId
        self.fields['AccountTypeId'].empty_label = "--- ДАНСНЫ ТӨРӨЛ СОНГОХ ---"
        
        # Add empty choice for CurrencyId
        self.fields['CurrencyId'].empty_label = "--- ВАЛЮТ СОНГОХ ---"
    
    def clean_AccountCode(self):
        """Validate that AccountCode is unique"""
        account_code = self.cleaned_data.get('AccountCode')
        
        if account_code:
            # Check if an account with this code already exists
            # Exclude the current instance if we're updating
            query = Ref_Account.objects.filter(AccountCode=account_code)
            
            # If we're updating an existing account, exclude it from the check
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                raise forms.ValidationError(
                    f'Дансны код "{account_code}" бүртгэгдсэн байна. Өөр код оруулна уу.'
                )
        
        return account_code
    
    class Meta:
        model = Ref_Account
        fields = ['AccountCode', 'AccountName', 'AccountTypeId', 'CurrencyId']
        widgets = {
            'AccountCode': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'AccountName': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'AccountTypeId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-accounting-blue focus:border-accounting-blue sm:text-sm'
            }),
            'CurrencyId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            })
        }
        labels = {
            'AccountCode': 'Account Code',
            'AccountName': 'Account Name',
            'AccountTypeId': 'Account Type',
            'CurrencyId': 'Currency'
        }




class RefClientForm(forms.ModelForm):
    """Form for creating and editing clients"""
    
    ClientBankId = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select Bank Account (Optional)",
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
        }),
        label='Client Bank Account'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Ref_Client_Bank
        self.fields['ClientBankId'].queryset = Ref_Client_Bank.objects.filter(IsActive=True).order_by('BankName', 'BankAccount')
        
        # Configure ClientType field with active client types
        self.fields['ClientType'].queryset = RefClientType.objects.filter(IsActive=True).order_by('ClientTypeName')
        self.fields['ClientType'].empty_label = "Select Client Type"
        
        # Set field requirements based on model
        self.fields['ClientType'].required = True
        self.fields['ClientCode'].required = True
        self.fields['ClientName'].required = True
    
    def clean_ClientCode(self):
        """Custom validation for ClientCode"""
        client_code = self.cleaned_data.get('ClientCode')
        
        if not client_code:
            raise forms.ValidationError('Client code is required.')
        
        # Remove whitespace and convert to uppercase
        client_code = client_code.strip().upper()
        
        # Check length
        if len(client_code) < 2:
            raise forms.ValidationError('Client code must be at least 2 characters long.')
        
        if len(client_code) > 5:
            raise forms.ValidationError('Client code cannot exceed 5 characters.')
        
        # Check for uniqueness (exclude current instance if editing)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            # Editing existing client
            if RefClient.objects.filter(ClientCode=client_code).exclude(pk=instance.pk).exists():
                raise forms.ValidationError('A client with this code already exists.')
        else:
            # Creating new client
            if RefClient.objects.filter(ClientCode=client_code).exists():
                raise forms.ValidationError('A client with this code already exists.')
        
        return client_code
    
    def clean_ClientName(self):
        """Custom validation for ClientName"""
        client_name = self.cleaned_data.get('ClientName')
        
        if not client_name:
            raise forms.ValidationError('Client name is required.')
        
        # Remove extra whitespace
        client_name = ' '.join(client_name.strip().split())
        
        # Check length
        if len(client_name) < 2:
            raise forms.ValidationError('Client name must be at least 2 characters long.')
        
        if len(client_name) > 100:
            raise forms.ValidationError('Client name cannot exceed 100 characters.')
        
        return client_name
    
    class Meta:
        model = RefClient
        fields = ['ClientCode', 'ClientName', 'ClientType', 'ClientRegister', 'IsVat', 'IsDelete']
        widgets = {
            'ClientCode': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border border-gray-200 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm px-3 py-2',
                'maxlength': '5'
            }),
            'ClientName': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border border-gray-200 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm px-3 py-2',
                'maxlength': '100'
            }),
            'ClientType': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border border-gray-200 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm px-3 py-2'
            }),
            'ClientRegister': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border border-gray-200 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm px-3 py-2',
                'maxlength': '10'
            }),
            'IsVat': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-accounting-blue focus:ring-accounting-blue border-gray-200 rounded'
            }),
            'IsDelete': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-accounting-blue focus:ring-accounting-blue border-gray-200 rounded'
            })
        }
        labels = {
            'ClientCode': 'Client Code',
            'ClientName': 'Client Name',
            'ClientType': 'Client Type',
            'ClientRegister': 'Client Register',
            'IsVat': 'Is VAT',
            'IsDelete': 'Deleted'
        }


class Ref_Client_BankForm(forms.ModelForm):
    """Form for creating and editing client bank accounts"""
    
    def __init__(self, *args, **kwargs):
        client_id = kwargs.pop('client_id', None)
        super().__init__(*args, **kwargs)
        
        if client_id:
            self.fields['ClientId'].initial = client_id
    
    class Meta:
        model = Ref_Client_Bank
        fields = ['ClientId', 'BankName', 'BankAccount', 'IsActive']
        widgets = {
            'ClientId': forms.HiddenInput(),
            'BankName': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Банкны нэр',
                'maxlength': '45'
            }),
            'BankAccount': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Дансны дугаар',
                'maxlength': '45'
            }),
            'IsActive': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }
    
    def clean_BankName(self):
        bank_name = self.cleaned_data.get('BankName')
        if not bank_name or not bank_name.strip():
            raise forms.ValidationError('Банкны нэр заавал шаардлагатай.')
        return bank_name.strip()
    
    def clean_BankAccount(self):
        bank_account = self.cleaned_data.get('BankAccount')
        if not bank_account or not bank_account.strip():
            raise forms.ValidationError('Дансны дугаар заавал шаардлагатай.')
        return bank_account.strip()


class RefInventoryForm(forms.ModelForm):
    """Form for creating and editing inventory items"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configure foreign key fields with proper querysets
        self.fields['InventoryTypeId'].queryset = Ref_Inventory_Type.objects.all().order_by('InventoryTypeName')
        self.fields['MeasurementId'].queryset = Ref_Measurement.objects.all().order_by('MeasurementName')
        
        # Set required fields based on model requirements
        self.fields['InventoryTypeId'].empty_label = "Select Inventory Type"
        self.fields['InventoryTypeId'].required = True
        self.fields['MeasurementId'].empty_label = "Select Measurement Unit"
        self.fields['MeasurementId'].required = True
        self.fields['UnitCost'].required = True
        self.fields['UnitPrice'].required = True
    
    class Meta:
        model = RefInventory
        fields = ['InventoryCode', 'InventoryName', 'InventoryTypeId', 'MeasurementId', 'UnitCost', 'UnitPrice', 'IsActive']
        widgets = {
            'InventoryCode': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border border-gray-200 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm px-3 py-2',
                'maxlength': '5'
            }),
            'InventoryName': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border border-gray-200 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm px-3 py-2',
                'maxlength': '50'
            }),
            'InventoryTypeId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border border-gray-200 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm px-3 py-2'
            }),
            'MeasurementId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border border-gray-200 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm px-3 py-2'
            }),
            'UnitCost': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border border-gray-200 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm px-3 py-2',
                'step': '0.000001',
                'min': '0'
            }),
            'UnitPrice': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border border-gray-200 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm px-3 py-2',
                'step': '0.000001',
                'min': '0'
            }),
            'IsActive': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-accounting-blue focus:ring-accounting-blue border-gray-200 rounded'
            })
        }
        labels = {
            'InventoryCode': 'Inventory Code',
            'InventoryName': 'Inventory Name',
            'InventoryTypeId': 'Inventory Type',
            'MeasurementId': 'Measurement Unit',
            'UnitCost': 'Unit Cost',
            'UnitPrice': 'Unit Price',
            'IsActive': 'Active'
        }


class CurrencySelect(forms.Select):
    """Custom select widget for Currency with default value data attributes"""
    
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        
        # Add default value as data attribute for JavaScript
        if value and value != '':
            try:
                # Extract the actual value from ModelChoiceIteratorValue if needed
                actual_value = value
                if hasattr(value, 'value'):
                    actual_value = value.value
                
                currency = Ref_Currency.objects.get(CurrencyId=actual_value)
                option['attrs']['data-default-value'] = str(currency.DefaultValue)
            except (Ref_Currency.DoesNotExist, ValueError, TypeError):
                pass
        
        return option


class CashDocumentForm(forms.ModelForm):
    """Form for creating and editing cash documents"""
    
    ClientBankId = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label="Select Bank Account (Optional)",
        widget=ClientBankIdSelect(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
        }),
        label='Client Bank Account'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CurrencyId as a ModelChoiceField for foreign key relationship
        from .models import Ref_Currency
        self.fields['CurrencyId'] = forms.ModelChoiceField(
            queryset=Ref_Currency.objects.filter(IsActive=True).order_by('CurrencyId'),
            required=True,
            empty_label="Select Currency",
            widget=forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
            })
        )
        
        # Configure foreign key fields with proper querysets
        self.fields['DocumentTypeId'].queryset = Ref_Document_Type.objects.filter(IsDelete=False, DocumentTypeId__in=[1, 2, 3, 4, 15, 16]).order_by('DocumentTypeId')
        self.fields['ClientId'].queryset = RefClient.objects.filter(IsDelete=False).order_by('ClientCode')
        self.fields['AccountId'].queryset = Ref_Account.objects.filter(IsDelete=False).order_by('AccountCode')
        self.fields['AccountId'].required = True
        
        # Configure VatAccountId field
        self.fields['VatAccountId'].queryset = Ref_Account.objects.filter(IsDelete=False).order_by('AccountCode')
        self.fields['VatAccountId'].required = False
        self.fields['VatAccountId'].empty_label = "Select VAT Account (Optional)"
        
        # Configure TemplateId field
        from .models import Ref_Template
        self.fields['TemplateId'].queryset = Ref_Template.objects.filter(IsDelete=False).order_by('TemplateName')
        self.fields['TemplateId'].required = False
        self.fields['TemplateId'].empty_label = "Select Template (Optional)"
        
        # Configure ClientBankId queryset - filter by selected client if available
        from .models import Ref_Client_Bank
        if self.instance and self.instance.pk and self.instance.ClientId:
            # For existing documents, filter by the document's client
            self.fields['ClientBankId'].queryset = Ref_Client_Bank.objects.filter(
                IsActive=True, 
                ClientId=self.instance.ClientId
            ).order_by('BankName', 'BankAccount')
        else:
            # For new documents, show all active bank accounts
            self.fields['ClientBankId'].queryset = Ref_Client_Bank.objects.filter(IsActive=True).order_by('BankName', 'BankAccount')
        
        # Add HTMX attributes for dynamic form handling
        self.fields['DocumentNo'].widget.attrs.update({
            'hx-post': '/core/cashdocument/validate/',
            'hx-trigger': 'blur',
            'hx-target': '#document-no-error',
            'hx-swap': 'innerHTML'
        })
        
        # Ensure Description field is properly configured
        if 'Description' in self.fields:
            self.fields['Description'].required = True
            self.fields['Description'].widget.attrs.update({
                'required': 'required',
                'maxlength': '200'
            })
            
            # Add validation for AccountId
            self.fields['AccountId'].widget.attrs.update({
                'required': 'required'
            })
    
    def clean_AccountId(self):
        """Validate AccountId is provided"""
        account_id = self.cleaned_data.get('AccountId')
        if not account_id:
            raise forms.ValidationError('Account selection is required.')
        return account_id
    
    class Meta:
        model = Cash_Document
        fields = ['DocumentNo', 'DocumentTypeId', 'DocumentDate', 'Description', 'ClientId', 'ClientBankId', 'CurrencyId', 'CurrencyAmount', 'CurrencyExchange', 'CurrencyMNT', 'AccountId', 'TemplateId', 'IsVat', 'VatAccountId']
        widgets = {
            'DocumentNo': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'placeholder': 'Enter document number'
            }),
            'DocumentTypeId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'DocumentDate': forms.DateInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'type': 'date'
            }),
            'Description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'rows': 3,
                'placeholder': 'Enter document description'
            }),
            'ClientId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'CurrencyAmount': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'step': '0.000001',
                'placeholder': 'Enter currency amount'
            }),
            'CurrencyExchange': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'step': '0.0001',
                'placeholder': 'Enter exchange rate (default: 1.0000)'
            }),
            'CurrencyMNT': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm bg-gray-50 text-gray-600 cursor-not-allowed',
                'step': '0.000001',
                'placeholder': 'Auto-calculated',
                'readonly': True
            }),
            'AccountId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'TemplateId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            })
        }
        labels = {
            'DocumentNo': 'Document Number',
            'DocumentTypeId': 'Document Type',
            'DocumentDate': 'Document Date',
            'Description': 'Description',
            'ClientId': 'Client',
            'CurrencyId': 'Currency',
            'CurrencyAmount': 'Currency Amount',
            'CurrencyExchange': 'Exchange Rate (Multiplier)',
            'CurrencyMNT': 'MNT Amount',
            'AccountId': 'Account ID',
            'TemplateId': 'Template'
        }
    
    def clean_DocumentNo(self):
        document_no = self.cleaned_data.get('DocumentNo')
        if not document_no:
            raise forms.ValidationError('Document number is required.')
        
        # Ensure proper Unicode encoding
        try:
            document_no = str(document_no).encode('utf-8').decode('utf-8')
        except UnicodeEncodeError:
            raise forms.ValidationError('Document number contains invalid characters.')
        
        # Check for duplicate document numbers (excluding current instance if editing)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if Cash_Document.objects.filter(DocumentNo=document_no).exclude(pk=instance.pk).exists():
                raise forms.ValidationError('Document number already exists.')
        else:
            if Cash_Document.objects.filter(DocumentNo=document_no).exists():
                raise forms.ValidationError('Document number already exists.')
        
        return document_no
    
    def clean_Description(self):
        description = self.cleaned_data.get('Description')
        if description:
            # Ensure proper Unicode encoding
            try:
                description = str(description).encode('utf-8').decode('utf-8')
            except UnicodeEncodeError:
                raise forms.ValidationError('Description contains invalid characters.')
        return description
    





class InvDocumentForm(forms.ModelForm):
    """Form for creating and editing inventory documents"""
    
    def __init__(self, *args, **kwargs):
        parentid = kwargs.pop('parentid', None)
        super().__init__(*args, **kwargs)
        
        # Configure foreign key fields with proper querysets
        if parentid:
            self.fields['DocumentTypeId'].queryset = Ref_Document_Type.objects.filter(IsDelete=False, ParentId=parentid).order_by('DocumentTypeId')
        else:
            self.fields['DocumentTypeId'].queryset = Ref_Document_Type.objects.filter(IsDelete=False, ParentId=3).order_by('DocumentTypeId')
        self.fields['ClientId'].queryset = RefClient.objects.filter(IsDelete=False).order_by('ClientCode')
        self.fields['AccountId'].queryset = Ref_Account.objects.filter(IsDelete=False).order_by('AccountCode')
        self.fields['WarehouseId'].queryset = Ref_Warehouse.objects.filter(IsDelete=False).order_by('WarehouseCode')
        self.fields['VatAccountId'].queryset = Ref_Account.objects.filter(IsDelete=False).order_by('AccountCode')
        self.fields['TemplateId'].queryset = Ref_Template.objects.filter(IsDelete=False).order_by('TemplateName')
        
        # Add empty choice for optional fields
        self.fields['WarehouseId'].empty_label = "Select Warehouse (Optional)"
        self.fields['WarehouseId'].required = False
        self.fields['VatAccountId'].empty_label = "Select VAT Account (Optional)"
        self.fields['VatAccountId'].required = False
        self.fields['TemplateId'].empty_label = "Select Template (Optional)"
        self.fields['TemplateId'].required = False
        
        # Add HTMX attributes for dynamic form handling
        self.fields['DocumentNo'].widget.attrs.update({
            'hx-post': '/core/invdocument/validate/',
            'hx-trigger': 'blur',
            'hx-target': '#document-no-error',
            'hx-swap': 'innerHTML'
        })
    
    class Meta:
        model = Inv_Document
        fields = ['DocumentNo', 'DocumentTypeId', 'DocumentDate', 'AccountId', 'ClientId', 'TemplateId', 'Description', 'IsVat', 'VatAccountId', 'VatPercent', 'IsLock', 'WarehouseId', 'CostAmount', 'PriceAmount']
        widgets = {
            'DocumentNo': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'placeholder': 'Enter document number'
            }),
            'DocumentTypeId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'DocumentDate': forms.DateInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'type': 'date'
            }),
            'AccountId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'ClientId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'Description': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'placeholder': 'Enter document description'
            }),
            'IsVat': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-accounting-blue focus:ring-accounting-blue border-gray-300 rounded'
            }),
            'VatAccountId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'VatPercent': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'step': '0.01',
                'placeholder': 'Enter VAT percentage'
            }),
            'IsLock': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-accounting-blue focus:ring-accounting-blue border-gray-300 rounded'
            }),
            'WarehouseId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'CostAmount': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'step': '0.000001',
                'placeholder': 'Enter cost amount'
            }),
            'PriceAmount': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'step': '0.000001',
                'placeholder': 'Enter price amount'
            })
        }
        labels = {
            'DocumentNo': 'Document Number',
            'DocumentTypeId': 'Document Type',
            'DocumentDate': 'Document Date',
            'AccountId': 'Account',
            'ClientId': 'Client',
            'Description': 'Description',
            'IsVat': 'Is VAT',
            'VatAccountId': 'VAT Account',
            'VatPercent': 'VAT Percent',
            'IsLock': 'Is Locked',
            'WarehouseId': 'Warehouse',
            'CostAmount': 'Cost Amount',
            'PriceAmount': 'Price Amount'
        }
    
    def clean_DocumentNo(self):
        document_no = self.cleaned_data.get('DocumentNo')
        if not document_no:
            raise forms.ValidationError('Document number is required.')
        
        # Check for duplicate document numbers (excluding current instance if editing)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if Inv_Document.objects.filter(DocumentNo=document_no).exclude(pk=instance.pk).exists():
                raise forms.ValidationError('Document number already exists.')
        else:
            if Inv_Document.objects.filter(DocumentNo=document_no).exists():
                raise forms.ValidationError('Document number already exists.')
        
        return document_no




class RefAssetForm(forms.ModelForm):
    """Form for creating and editing assets"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configure foreign key fields with proper querysets
        self.fields['AssetTypeId'].queryset = Ref_Asset_Type.objects.filter(IsActive=True).order_by('AssetTypeName')
    
    class Meta:
        model = RefAsset
        fields = ['AssetCode', 'AssetName', 'AssetTypeId', 'IsDelete']
        widgets = {
            'AssetCode': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'maxlength': '5',
                'placeholder': 'Enter asset code'
            }),
            'AssetName': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'maxlength': '50',
                'placeholder': 'Enter asset name'
            }),
            'AssetTypeId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'IsDelete': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-accounting-blue focus:ring-accounting-blue border-gray-300 rounded'
            })
        }
        labels = {
            'AssetCode': 'Asset Code',
            'AssetName': 'Asset Name',
            'AssetTypeId': 'Asset Type',
            'IsDelete': 'Deleted'
        }


class Ref_Asset_CardForm(forms.ModelForm):
    """Form for creating and editing asset cards"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configure foreign key fields with proper querysets
        self.fields['AssetId'].queryset = RefAsset.objects.filter(IsDelete=False).order_by('AssetCode')
        self.fields['ClientId'].queryset = RefClient.objects.filter(IsDelete=False).order_by('ClientCode')
        self.fields['ClientId'].required = False
        self.fields['ClientId'].empty_label = "Select Client (Optional)"
    
    def clean(self):
        """Calculate DailyExpense before validation if UnitCost and MonthsToUse are provided"""
        from decimal import Decimal, ROUND_HALF_UP
        
        cleaned_data = super().clean()
        unit_cost = cleaned_data.get('UnitCost')
        months_to_use = cleaned_data.get('MonthsToUse')
        daily_expense = cleaned_data.get('DailyExpense')
        
        # Calculate DailyExpense if UnitCost and MonthsToUse are provided
        if unit_cost is not None and months_to_use is not None and months_to_use > 0:
            # DailyExpense = UnitCost / (MonthsToUse * 30 days per month)
            # Use Decimal for precise calculation and rounding
            unit_cost_decimal = Decimal(str(unit_cost))
            months_to_use_decimal = Decimal(str(months_to_use))
            calculated_daily_expense = unit_cost_decimal / (months_to_use_decimal * Decimal('30'))
            
            # Round to 6 decimal places to match the model field's decimal_places=6
            # This ensures it fits within max_digits=24, decimal_places=6 constraint
            calculated_daily_expense = calculated_daily_expense.quantize(
                Decimal('0.000001'), 
                rounding=ROUND_HALF_UP
            )
            
            cleaned_data['DailyExpense'] = calculated_daily_expense
        elif unit_cost is not None and months_to_use is not None and months_to_use <= 0:
            raise forms.ValidationError({
                'MonthsToUse': 'Months to Use must be greater than 0 to calculate Daily Expense.'
            })
        elif daily_expense is None or daily_expense == 0:
            # If DailyExpense is not provided and cannot be calculated, raise an error
            if unit_cost is None or months_to_use is None:
                raise forms.ValidationError({
                    'DailyExpense': 'Daily expense should be calculated before submit. Please provide Unit Cost and Months to Use, or enter Daily Expense manually.'
                })
        
        return cleaned_data
    
    class Meta:
        model = Ref_Asset_Card
        fields = ['AssetId', 'AssetCardCode', 'AssetCardName', 'ManufacturedDate', 'ReceivedDate', 'MonthsToUse', 'UnitCost', 'UnitPrice', 'DailyExpense', 'ClientId']
        widgets = {
            'AssetId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'AssetCardCode': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'maxlength': '5',
                'placeholder': 'Enter asset card code'
            }),
            'AssetCardName': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'maxlength': '50',
                'placeholder': 'Enter asset card name'
            }),
            'ManufacturedDate': forms.DateInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'type': 'date'
            }),
            'ReceivedDate': forms.DateInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'type': 'date'
            }),
            'MonthsToUse': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'placeholder': 'Enter months to use'
            }),
            'UnitCost': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'step': '0.000001',
                'placeholder': 'Enter unit cost'
            }),
            'UnitPrice': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'step': '0.000001',
                'placeholder': 'Enter unit price'
            }),
            'DailyExpense': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'step': '0.000001',
                'placeholder': 'Enter daily expense'
            }),
            'ClientId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            })
        }
        labels = {
            'AssetId': 'Asset',
            'AssetCardCode': 'Asset Card Code',
            'AssetCardName': 'Asset Card Name',
            'ManufacturedDate': 'Manufactured Date',
            'ReceivedDate': 'Received Date',
            'MonthsToUse': 'Months to Use',
            'UnitCost': 'Unit Cost',
            'UnitPrice': 'Unit Price',
            'DailyExpense': 'Daily Expense',
            'ClientId': 'Client'
        }


class InvBeginningBalanceForm(forms.ModelForm):
    """Form for creating and editing inventory beginning balances"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configure foreign key fields with proper querysets
        self.fields['AccountId'].queryset = Ref_Account.objects.filter(IsDelete=False).order_by('AccountCode')
        self.fields['InventoryId'].queryset = RefInventory.objects.filter(IsActive=True, IsDelete=False).order_by('InventoryName')
        self.fields['WarehouseId'].queryset = Ref_Warehouse.objects.filter(IsDelete=False).order_by('WarehouseCode')
        
        # Set required fields
        self.fields['AccountId'].required = True
        self.fields['InventoryId'].required = True
        self.fields['WarehouseId'].required = True
        self.fields['Quantity'].required = True
        self.fields['UnitCost'].required = True
        self.fields['UnitPrice'].required = True
        
        # Make EmployeeId optional
        self.fields['EmployeeId'].required = False
    
    class Meta:
        model = Inv_Beginning_Balance
        fields = ['AccountId', 'InventoryId', 'Quantity', 'UnitCost', 'UnitPrice', 'WarehouseId', 'EmployeeId']
        widgets = {
            'AccountId': forms.HiddenInput(),  # Will be populated by modal selection
            'InventoryId': forms.HiddenInput(),  # Will be populated by modal selection
            'Quantity': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'step': '0.000001',
                'min': '0',
                'placeholder': 'Enter quantity'
            }),
            'UnitCost': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'step': '0.000001',
                'min': '0',
                'placeholder': 'Enter unit cost'
            }),
            'UnitPrice': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'step': '0.000001',
                'min': '0',
                'placeholder': 'Enter unit price'
            }),
            'WarehouseId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'EmployeeId': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'placeholder': 'Optional employee ID'
            })
        }
        labels = {
            'AccountId': 'Account',
            'InventoryId': 'Inventory',
            'Quantity': 'Quantity',
            'UnitCost': 'Unit Cost',
            'UnitPrice': 'Unit Price',
            'WarehouseId': 'Warehouse',
            'EmployeeId': 'Employee ID'
        }
    
    def clean_Quantity(self):
        """Validate quantity is positive"""
        quantity = self.cleaned_data.get('Quantity')
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError('Quantity must be greater than 0.')
        return quantity
    
    def clean_UnitCost(self):
        """Validate unit cost is positive"""
        unit_cost = self.cleaned_data.get('UnitCost')
        if unit_cost is not None and unit_cost <= 0:
            raise forms.ValidationError('Unit cost must be greater than 0.')
        return unit_cost
    
    def clean_UnitPrice(self):
        """Validate unit price is positive"""
        unit_price = self.cleaned_data.get('UnitPrice')
        if unit_price is not None and unit_price <= 0:
            raise forms.ValidationError('Unit price must be greater than 0.')
        return unit_price


class AstDocumentForm(forms.ModelForm):
    """Form for creating and editing asset documents"""
    
    def __init__(self, *args, **kwargs):
        parentid = kwargs.pop('parentid', None)
        super().__init__(*args, **kwargs)
        
        # Configure foreign key fields with proper querysets
        if parentid:
            self.fields['DocumentTypeId'].queryset = Ref_Document_Type.objects.filter(IsDelete=False, ParentId=parentid).order_by('DocumentTypeId')
        else:
            # Asset documents use document types 10 and 11
            self.fields['DocumentTypeId'].queryset = Ref_Document_Type.objects.filter(IsDelete=False, DocumentTypeId__in=[10, 11]).order_by('DocumentTypeId')
        self.fields['ClientId'].queryset = RefClient.objects.filter(IsDelete=False).order_by('ClientCode')
        self.fields['AccountId'].queryset = Ref_Account.objects.filter(IsDelete=False).order_by('AccountCode')
        self.fields['VatAccountId'].queryset = Ref_Account.objects.filter(IsDelete=False).order_by('AccountCode')
        self.fields['TemplateId'].queryset = Ref_Template.objects.filter(IsDelete=False).order_by('TemplateName')
        
        # Add empty choice for optional fields
        self.fields['VatAccountId'].empty_label = "Select VAT Account (Optional)"
        self.fields['VatAccountId'].required = False
        self.fields['TemplateId'].empty_label = "Select Template (Optional)"
        self.fields['TemplateId'].required = False
        
        # Add HTMX attributes for dynamic form handling
        self.fields['DocumentNo'].widget.attrs.update({
            'hx-post': '/core/astdocument/validate/',
            'hx-trigger': 'blur',
            'hx-target': '#document-no-error',
            'hx-swap': 'innerHTML'
        })
    
    class Meta:
        model = Ast_Document
        fields = ['DocumentNo', 'DocumentTypeId', 'DocumentDate', 'AccountId', 'ClientId', 'TemplateId', 'Description', 'IsVat', 'VatAccountId', 'VatPercent', 'IsLock', 'CostAmount', 'PriceAmount']
        widgets = {
            'DocumentNo': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'placeholder': 'Enter document number'
            }),
            'DocumentTypeId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'DocumentDate': forms.DateInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'type': 'date'
            }),
            'AccountId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'ClientId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'Description': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'placeholder': 'Enter document description'
            }),
            'IsVat': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-accounting-blue focus:ring-accounting-blue border-gray-300 rounded'
            }),
            'VatAccountId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'VatPercent': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'step': '0.01',
                'placeholder': 'Enter VAT percentage'
            }),
            'IsLock': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-accounting-blue focus:ring-accounting-blue border-gray-300 rounded'
            }),
            'CostAmount': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'step': '0.000001',
                'placeholder': 'Enter cost amount'
            }),
            'PriceAmount': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm',
                'step': '0.000001',
                'placeholder': 'Enter price amount'
            })
        }
        labels = {
            'DocumentNo': 'Document Number',
            'DocumentTypeId': 'Document Type',
            'DocumentDate': 'Document Date',
            'AccountId': 'Account',
            'ClientId': 'Client',
            'Description': 'Description',
            'IsVat': 'Is VAT',
            'VatAccountId': 'VAT Account',
            'VatPercent': 'VAT Percent',
            'IsLock': 'Is Locked',
            'CostAmount': 'Cost Amount',
            'PriceAmount': 'Price Amount'
        }


class Ref_Asset_Depreciation_AccountForm(forms.ModelForm):
    """Form for creating and editing asset depreciation accounts"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configure foreign key fields with proper querysets
        self.fields['AssetAccountId'].queryset = Ref_Account.objects.filter(IsDelete=False).order_by('AccountCode')
        self.fields['DepreciationAccountId'].queryset = Ref_Account.objects.filter(IsDelete=False).order_by('AccountCode')
        self.fields['ExpenseAccountId'].queryset = Ref_Account.objects.filter(IsDelete=False).order_by('AccountCode')
        
        # Add empty choices for required fields
        self.fields['AssetAccountId'].empty_label = "Select Asset Account"
        self.fields['DepreciationAccountId'].empty_label = "Select Depreciation Account"
        self.fields['ExpenseAccountId'].empty_label = "Select Expense Account"
    
    class Meta:
        model = Ref_Asset_Depreciation_Account
        fields = ['AssetAccountId', 'DepreciationAccountId', 'ExpenseAccountId', 'IsDelete']
        widgets = {
            'AssetAccountId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'DepreciationAccountId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'ExpenseAccountId': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-accounting-blue focus:ring-accounting-blue sm:text-sm'
            }),
            'IsDelete': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-accounting-blue focus:ring-accounting-blue border-gray-300 rounded'
            })
        }
        labels = {
            'AssetAccountId': 'Asset Account',
            'DepreciationAccountId': 'Depreciation Account',
            'ExpenseAccountId': 'Expense Account',
            'IsDelete': 'Is Deleted'
        }


class Ref_TemplateForm(forms.ModelForm):
    """Form for creating and editing templates"""
    
    class Meta:
        model = Ref_Template
        fields = ['TemplateName', 'DocumentTypeId', 'AccountId', 'IsDelete']
        widgets = {
            'TemplateName': forms.TextInput(attrs={
                'class': 'form-control border border-gray-200 rounded-md px-3 py-2 w-full',
                'placeholder': 'Enter template name',
                'maxlength': '150'
            }),
            'DocumentTypeId': forms.Select(attrs={
                'class': 'form-control border border-gray-200 rounded-md px-3 py-2 w-full'
            }),
            'AccountId': forms.Select(attrs={
                'class': 'form-control border border-gray-200 rounded-md px-3 py-2 w-full'
            }),
            'IsDelete': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'TemplateName': 'ЗАГВАРЫН НЭР',
            'DocumentTypeId': 'БАРИМТЫН ТӨРӨЛ',
            'AccountId': 'ДАНС',
            'IsDelete': 'Идэвхитэй'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active document types
        self.fields['DocumentTypeId'].queryset = Ref_Document_Type.objects.filter(IsDelete=False)
        # Filter active accounts and order by AccountCode
        self.fields['AccountId'].queryset = Ref_Account.objects.filter(IsDelete=False).order_by('AccountCode')
        # AccountId is required - no empty_label needed


class Ref_Template_DetailForm(forms.ModelForm):
    """Form for creating and editing template details"""
    
    class Meta:
        model = Ref_Template_Detail
        fields = ['AccountId', 'IsDebit', 'CashFlowId']
        widgets = {
            'AccountId': forms.Select(attrs={
                'class': 'form-control border border-gray-200 rounded-md px-3 py-2 w-full'
            }),
            'CashFlowId': forms.Select(attrs={
                'class': 'form-control border border-gray-200 rounded-md px-3 py-2 w-full'
            }),
            'IsDebit': forms.CheckboxInput(attrs={
                'class': 'form-check-input h-4 w-4 text-accounting-blue focus:ring-accounting-blue border-gray-200 rounded'
            })
        }
        labels = {
            'AccountId': 'ДАНС',
            'IsDebit': 'ДЕБИТ/КРЕДИТ',
            'CashFlowId': 'МӨНГӨН ГҮЙЛГЭЭНИЙ МӨР'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active accounts and order by AccountCode ascending
        self.fields['AccountId'].queryset = Ref_Account.objects.filter(IsDelete=False).order_by('AccountCode')
        # Filter active cash flows
        self.fields['CashFlowId'].queryset = Ref_CashFlow.objects.filter(IsActive=True)
        # Set empty label for CashFlowId
        self.fields['CashFlowId'].empty_label = "Мөнгөн гүйлгээний төрөл сонгоно уу"


