from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Ref_Account_Type(models.Model):
    """Account Type model for categorizing accounts"""
    AccountTypeId = models.SmallIntegerField(primary_key=True)
    AccountTypeCode = models.CharField(max_length=4, unique=True)
    AccountTypeName = models.CharField(max_length=100, unique=True)    
    IsActive = models.BooleanField(default=True)
    StBalanceId = models.ForeignKey(
        'St_Balance',
        on_delete=models.PROTECT,
        db_column='StBalanceId',
        related_name='account_types',
        null=True,
        blank=True
    )
    StIncomeId = models.ForeignKey(
        'St_Income',
        on_delete=models.PROTECT,
        db_column='StIncomeId',
        related_name='account_types',
        null=True,
        blank=True
    )




    
    class Meta:
        db_table = 'ref_account_type'
        verbose_name = 'Account Type'
        verbose_name_plural = 'Account Types'

    def __str__(self):
        return self.AccountTypeName


class Ref_Account(models.Model):
    """Account model for the chart of accounts"""
    AccountId = models.AutoField(primary_key=True)
    AccountCode = models.CharField(max_length=20, unique=True)
    AccountName = models.CharField(max_length=200)
    AccountTypeId = models.ForeignKey(
        Ref_Account_Type, 
        on_delete=models.PROTECT,
        db_column='AccountTypeId',
        related_name='accounts'
    )
    CurrencyId = models.ForeignKey(
        'Ref_Currency',
        on_delete=models.PROTECT,
        db_column='CurrencyId',
        related_name='accounts',
        null=True,
        blank=True
    )
    IsDelete = models.BooleanField(default=False)
    CreatedDate = models.DateField(auto_now_add=True)
    ModifiedDate = models.DateField(auto_now=True)

    class Meta:
        db_table = 'ref_account'
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'

    def __str__(self):
        return f"{self.AccountCode} - {self.AccountName}"


class RefClientType(models.Model):
    """Client Type model for categorizing clients"""
    ClientTypeId = models.SmallIntegerField(primary_key=True)
    ClientTypeName = models.CharField(max_length=50, unique=True)
    IsActive = models.BooleanField(default=True)
    CreatedDate = models.DateField(auto_now_add=True)
    ModifiedDate = models.DateField(auto_now=True)

    class Meta:
        db_table = 'ref_client_type'
        verbose_name = 'Client Type'
        verbose_name_plural = 'Client Types'

    def __str__(self):
        return self.ClientTypeName


class RefClient(models.Model):
    """Client model for managing client information"""
    ClientId = models.AutoField(primary_key=True)
    ClientCode = models.CharField(max_length=5, unique=True)
    ClientName = models.CharField(max_length=100)
    ClientType = models.ForeignKey(
        RefClientType,
        on_delete=models.PROTECT,
        related_name='clients',
        null=False,
        blank=False,
        db_column='ClientTypeId'
    )
    ClientRegister = models.CharField(max_length=8, blank=True, null=True)
    CreatedBy = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='created_clients', db_column='CreatedBy')
    ModifiedBy = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='modified_clients', db_column='ModifiedBy')
    IsDelete = models.BooleanField(default=False)
    CreatedDate = models.DateField(auto_now_add=True)
    ModifiedDate = models.DateField(auto_now=True)

    class Meta:
        db_table = 'ref_client'
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return f"{self.ClientCode} - {self.ClientName}"


class Ref_Client_Bank(models.Model):
    """Client Bank model for managing client bank information"""
    ClientBankId = models.AutoField(primary_key=True)
    ClientId = models.ForeignKey(
        RefClient,
        on_delete=models.PROTECT,
        db_column='ClientId',
        related_name='client_banks'
    )
    BankName = models.CharField(max_length=45)
    BankAccount = models.CharField(max_length=45)
    IsActive = models.BooleanField(default=True)
    CreatedDate = models.DateField(auto_now_add=True)
    ModifiedDate = models.DateField(auto_now=True)

    class Meta:
        db_table = 'ref_client_bank'
        verbose_name = 'Client Bank'
        verbose_name_plural = 'Client Banks'

    def __str__(self):
        return f"{self.ClientId.ClientName} - {self.BankName} ({self.BankAccount})"


class Ref_Currency(models.Model):
    CurrencyId = models.SmallIntegerField(primary_key=True)
    Currency_name = models.CharField(max_length=6)
    DefaultValue = models.DecimalField(max_digits=10, decimal_places=4, default=10.4)
    IsActive = models.BooleanField(default=True)
    CreatedDate = models.DateField(auto_now_add=True, null=True, blank=True)
    ModifiedDate = models.DateField(auto_now=True, null=True, blank=True)

    class Meta:
        db_table = 'ref_currency'
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'

    def __str__(self):
        return f"{self.CurrencyId} - {self.Currency_name}"


class Ref_Inventory_Type(models.Model):
    """Inventory Type model for categorizing inventory types"""
    InventoryTypeId = models.AutoField(primary_key=True)
    InventoryTypeName = models.CharField(max_length=55)

    class Meta:
        db_table = 'ref_inventory_type'
        verbose_name = 'Inventory Type'
        verbose_name_plural = 'Inventory Types'

    def __str__(self):
        return self.InventoryTypeName


class Ref_Measurement(models.Model):
    """Measurement model for managing measurement units"""
    MeasurementId = models.SmallIntegerField(primary_key=True)
    MeasurementName = models.CharField(max_length=12)
    MeasurementAlternative = models.CharField(max_length=12, null=True, blank=True)
    MeasurementEquivalent = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    class Meta:
        db_table = 'ref_measurement'
        verbose_name = 'Measurement'
        verbose_name_plural = 'Measurements'

    def __str__(self):
        return self.MeasurementName


class Ref_Asset_Type(models.Model):
    """Asset Type model for categorizing asset types"""
    AssetTypeId = models.SmallIntegerField(primary_key=True)
    AssetTypeName = models.CharField(max_length=50)
    AssetTypeCode = models.CharField(max_length=2)
    IsActive = models.BooleanField(default=True)
    CreatedDate = models.DateField(auto_now_add=True)
    ModifiedDate = models.DateField(auto_now=True)

    class Meta:
        db_table = 'ref_asset_type'
        verbose_name = 'Asset Type'
        verbose_name_plural = 'Asset Types'

    def __str__(self):
        return self.AssetTypeName


class RefAsset(models.Model):
    """Asset model for managing assets"""
    AssetId = models.AutoField(primary_key=True)
    AssetCode = models.CharField(max_length=5, unique=True)
    AssetName = models.CharField(max_length=50)
    AssetTypeId = models.ForeignKey(
        Ref_Asset_Type,
        on_delete=models.PROTECT,
        db_column='AssetTypeId',
        related_name='assets'
    )
    CreatedBy = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_assets', default=1)
    ModifiedBy = models.ForeignKey(User, on_delete=models.PROTECT, related_name='modified_assets', default=1)
    IsDelete = models.BooleanField(default=False)
    CreatedDate = models.DateField(auto_now_add=True)
    ModifiedDate = models.DateField(auto_now=True)

    class Meta:
        db_table = 'ref_asset'
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'

    def __str__(self):
        return self.AssetName

class Ref_Asset_Card(models.Model):
    """Asset Card model for managing individual asset instances"""
    AssetCardId = models.AutoField(primary_key=True)
    AssetId = models.ForeignKey(
        RefAsset,
        on_delete=models.PROTECT,
        db_column='AssetId',
        related_name='asset_cards'
    )
    AssetCardCode = models.CharField(max_length=5)
    AssetCardName = models.CharField(max_length=50, default='')

    ManufacturedDate = models.DateField()
    ReceivedDate = models.DateField()
    MonthsToUse = models.SmallIntegerField()
    
    UnitCost = models.DecimalField(max_digits=24, decimal_places=6, default=0)   
    UnitPrice = models.DecimalField(max_digits=24, decimal_places=6, default=0)
    DailyExpense = models.DecimalField(max_digits=24, decimal_places=6, default=0)
    CreatedBy = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_asset_cards', db_column='CreatedBy')
    ModifiedBy = models.ForeignKey(User, on_delete=models.PROTECT, related_name='modified_asset_cards', db_column='ModifiedBy')
    CreatedDate = models.DateField(auto_now_add=True)
    ModifiedDate = models.DateField(auto_now=True)
    ClientId = models.ForeignKey(
        RefClient,
        on_delete=models.PROTECT,
        db_column='ClientId',
        related_name='asset_cards_client',
        null=True,
        blank=True
    )    

    class Meta:
        db_table = 'ref_asset_card'
        verbose_name = 'Asset Card'
        verbose_name_plural = 'Asset Cards'

    def __str__(self):
        return f"{self.AssetCardCode} - {self.AssetId.AssetName}"





class Ref_Document_Type(models.Model):
    """Document Type model for categorizing document types"""
    DocumentTypeId = models.SmallIntegerField(primary_key=True)
    DocumentTypeCode = models.CharField(max_length=8, unique=True, null=True, blank=True)
    Description = models.CharField(max_length=55)
    ParentId = models.SmallIntegerField(null=False, blank=False, default=0)
    IsDelete = models.BooleanField(default=False)    

    class Meta:
        db_table = 'ref_document_type'
        verbose_name = 'Document Type'
        verbose_name_plural = 'Document Types'

    def __str__(self):
        if self.DocumentTypeCode:
            return f"{self.DocumentTypeCode} - {self.Description}"
        return self.Description


class Ref_Document_Counter(models.Model):
    """Document Counter model for managing document numbering sequences"""
    DocumentCounterId = models.AutoField(primary_key=True)
    DocumentNo = models.CharField(max_length=10)
    DocumentTypeId = models.ForeignKey(
        Ref_Document_Type,
        on_delete=models.PROTECT,
        db_column='DocumentTypeId',
        related_name='document_counters'
    )
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_document_counters',
        db_column='CreatedBy'
    )
    CreatedDate = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'ref_document_counter'
        verbose_name = 'Document Counter'
        verbose_name_plural = 'Document Counters'

    def __str__(self):
        return f"{self.DocumentNo} - {self.DocumentTypeId.Description}"


class Ref_CashFlow(models.Model):
    """Cash Flow model for categorizing cash flow types"""
    CashFlowId = models.SmallIntegerField(primary_key=True)
    Description = models.CharField(max_length=60)
    IsActive = models.BooleanField(default=True)    

    class Meta:
        db_table = 'ref_cash_flow'
        verbose_name = 'Cash Flow'
        verbose_name_plural = 'Cash Flows'

    def __str__(self):
        return f"{self.CashFlowId} - {self.Description}"


class Ref_Contract(models.Model):
    """Contract model for categorizing contract types"""
    ContractId = models.AutoField(primary_key=True)
    ContractCode = models.CharField(max_length=20)
    Description = models.CharField(max_length=50)
    IsActive = models.BooleanField(default=True)    

    class Meta:
        db_table = 'ref_contract'
        verbose_name = 'Contract'
        verbose_name_plural = 'Contracts'

    def __str__(self):
        return f"{self.ContractCode} - {self.Description}"


class Ref_Warehouse(models.Model):
    """Warehouse model for managing warehouse locations"""
    WarehouseId = models.SmallIntegerField(primary_key=True)
    WarehouseCode = models.CharField(max_length=5, unique=True)
    WarehouseName = models.CharField(max_length=20)    
    IsDelete = models.BooleanField(default=False)
    CreatedBy = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='created_warehouses')

    class Meta:
        db_table = 'ref_warehouse'
        verbose_name = 'Warehouse'
        verbose_name_plural = 'Warehouses'

    def __str__(self):
        return f"{self.WarehouseCode} - {self.WarehouseName}"


class Cash_Document(models.Model):
    """Cash Document model for managing cash transactions"""
    DocumentId = models.AutoField(primary_key=True)
    DocumentNo = models.CharField(max_length=18)
    DocumentTypeId = models.ForeignKey(
        Ref_Document_Type,
        on_delete=models.PROTECT,
        db_column='DocumentTypeId',
        related_name='cash_documents'
    )
    DocumentDate = models.DateField()
    Description = models.CharField(max_length=200, null=False, blank=False)
    IsLock = models.BooleanField(default=False)
    IsDelete = models.BooleanField(default=False)
    ModifiedBy = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='modified_cash_documents', db_column='ModifiedBy')
    ModifiedDate = models.DateField(auto_now=True)
    CreatedBy = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='created_cash_documents', db_column='CreatedBy')
    CreatedDate = models.DateField(auto_now_add=True)
    ClientId = models.ForeignKey(
        RefClient,
        on_delete=models.PROTECT,
        db_column='ClientId',
        related_name='cash_documents'
    )
    PaidClientId = models.ForeignKey(
        RefClient,
        on_delete=models.PROTECT,
        db_column='PaidClientId',
        related_name='paid_cash_documents',
        null=True,
        blank=True
    )
    ClientBankId = models.ForeignKey(
        Ref_Client_Bank,
        on_delete=models.PROTECT,
        db_column='ClientBankId',
        related_name='cash_documents',
        null=True,
        blank=True
    )
    CurrencyId = models.ForeignKey(
        Ref_Currency,
        on_delete=models.PROTECT,
        db_column='CurrencyId',
        related_name='cash_documents'
    )
    CurrencyAmount = models.DecimalField(max_digits=24, decimal_places=6)
    CurrencyExchange = models.DecimalField(max_digits=10, decimal_places=4, default=1.0)
    CurrencyMNT = models.DecimalField(max_digits=24, decimal_places=6, null=True, blank=True)
    IsVat = models.BooleanField(default=False)
    VatAccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='VatAccountId',
        related_name='vat_cash_documents',
        null=True,
        blank=True
    )
    TemplateId = models.ForeignKey(
        'Ref_Template',
        on_delete=models.PROTECT,
        db_column='TemplateId',
        related_name='cash_documents',
        null=True,
        blank=True
    )
    IsPosted = models.BooleanField(default=False)
    AccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='AccountId',
        related_name='cash_documents'
    )

    class Meta:
        db_table = 'cash_document'
        verbose_name = 'Cash Document'
        verbose_name_plural = 'Cash Documents'

    def __str__(self):
        return f"{self.DocumentNo} - {self.Description}"


class Cash_DocumentDetail(models.Model):
    """Cash Document Detail model for managing cash document line items"""
    DocumentDetailId = models.AutoField(primary_key=True)
    DocumentId = models.ForeignKey(
        Cash_Document,
        on_delete=models.PROTECT,
        db_column='DocumentId',
        related_name='document_details'
    )
    AccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='AccountId',
        related_name='cash_document_details'
    )
    ClientId = models.ForeignKey(
        RefClient,
        on_delete=models.PROTECT,
        db_column='ClientId',
        related_name='cash_document_details'
    )
    CurrencyId = models.ForeignKey(
        Ref_Currency,
        on_delete=models.PROTECT,
        db_column='CurrencyId',
        related_name='cash_document_details'
    )
    CurrencyExchange = models.DecimalField(max_digits=10, decimal_places=4)
    CurrencyAmount = models.DecimalField(max_digits=24, decimal_places=6)
    IsDebit = models.BooleanField()
    DebitAmount = models.DecimalField(max_digits=24, decimal_places=6)
    CreditAmount = models.DecimalField(max_digits=24, decimal_places=6)
    ContractId = models.ForeignKey(
        Ref_Contract,
        on_delete=models.PROTECT,
        db_column='ContractId',
        related_name='cash_document_details',
        null=True,
        blank=True
    )
    CashFlowId = models.ForeignKey(
        Ref_CashFlow,
        on_delete=models.PROTECT,
        db_column='CashFlowId',
        related_name='cash_document_details',
        null=True,
        blank=True
    )
 
    class Meta:
        db_table = 'cash_document_detail'
        verbose_name = 'Cash Document Detail'
        verbose_name_plural = 'Cash Document Details'
 
    def __str__(self):
        return f"{self.DocumentId.DocumentNo} - {self.AccountId.AccountName} - {self.ClientId.ClientName}"
   
    def save(self, *args, **kwargs):
        # DebitAmount and CreditAmount are calculated by the view layer
        # before saving (CurrencyAmount × CurrencyExchange). 
        # No auto-calculation needed here to avoid overwriting correct values.
        super().save(*args, **kwargs)


class Inv_Document(models.Model):
    """Inventory Document model for managing inventory transactions"""
    DocumentId = models.AutoField(primary_key=True)
    DocumentNo = models.CharField(max_length=20)
    DocumentTypeId = models.ForeignKey(
        Ref_Document_Type,
        on_delete=models.PROTECT,
        db_column='DocumentTypeId',
        related_name='inv_documents'
    )
    DocumentDate = models.DateField()
    AccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='AccountId',
        related_name='inv_documents'
    )
    ClientId = models.ForeignKey(
        RefClient,
        on_delete=models.PROTECT,
        db_column='ClientId',
        related_name='inv_documents'
    )
    TemplateId = models.ForeignKey(
        'Ref_Template',
        on_delete=models.PROTECT,
        db_column='TemplateId',
        related_name='inv_documents',
        null=True,
        blank=True
    )
    Description = models.CharField(max_length=200)
    IsVat = models.BooleanField(default=False, null=True, blank=True)
    VatAccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='VatAccountId',
        related_name='vat_inv_documents',
        null=True,
        blank=True
    )
    VatPercent = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    IsLock = models.BooleanField(default=False, null=True, blank=True)
    IsDelete = models.BooleanField(default=False)
    ModifiedBy = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='modified_inv_documents', db_column='ModifiedBy')
    ModifiedDate = models.DateField(auto_now=True)
    CreatedBy = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='created_inv_documents', db_column='CreatedBy')
    CreatedDate = models.DateField(auto_now_add=True)
    IsPosted = models.BooleanField(default=False, null=True, blank=True)
    WarehouseId = models.ForeignKey(
        Ref_Warehouse,
        on_delete=models.PROTECT,
        db_column='WarehouseId',
        related_name='inv_documents',
        null=True,
        blank=True
    )
    CostAmount = models.DecimalField(max_digits=24, decimal_places=6, null=True, blank=True)
    PriceAmount = models.DecimalField(max_digits=24, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = 'inv_document'
        verbose_name = 'Inventory Document'
        verbose_name_plural = 'Inventory Documents'

    def __str__(self):
        return f"{self.DocumentNo} - {self.Description}"


class RefInventory(models.Model):
    """Inventory model for managing inventory items"""
    InventoryId = models.AutoField(primary_key=True)
    InventoryCode = models.CharField(max_length=5, null=True, blank=True)
    InventoryName = models.CharField(max_length=50)
    InventoryTypeId = models.ForeignKey(
        Ref_Inventory_Type,
        on_delete=models.PROTECT,
        db_column='InventoryTypeId',
        related_name='inventories',
        null=False,
        blank=False
    )
    MeasurementId = models.ForeignKey(
        Ref_Measurement,
        on_delete=models.PROTECT,
        db_column='MeasurementId',
        related_name='inventories',
        null=False,        
        blank=False
    )
    UnitCost = models.DecimalField(max_digits=24, decimal_places=6, null=False, blank=False )
    UnitPrice = models.DecimalField(max_digits=24, decimal_places=6, null=False, blank=False)
    CreatedBy = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='created_inventories', db_column='CreatedBy')
    ModifiedBy = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='modified_inventories', db_column='ModifiedBy')
    IsActive = models.BooleanField(default=True)
    IsDelete = models.BooleanField(default=False)
    CreatedDate = models.DateField(auto_now_add=True)
    ModifiedDate = models.DateField(auto_now=True)

    class Meta:
        db_table = 'ref_inventory'
        verbose_name = 'Inventory'
        verbose_name_plural = 'Inventories'
        ordering = ['InventoryName']

    def __str__(self):
        if self.InventoryCode:
            return f"{self.InventoryCode} - {self.InventoryName}"
        return self.InventoryName


class Inv_Document_Item(models.Model):
    """Inventory Document Item model for managing inventory document line items"""
    DocumentItemId = models.AutoField(primary_key=True)
    DocumentId = models.ForeignKey(
        Inv_Document,
        on_delete=models.PROTECT,
        db_column='DocumentId',
        related_name='document_items'
    )
    InventoryId = models.ForeignKey(
        RefInventory,
        on_delete=models.PROTECT,
        db_column='InventoryId',
        related_name='document_items'
    )
    Quantity = models.DecimalField(max_digits=24, decimal_places=6)
    UnitCost = models.DecimalField(max_digits=24, decimal_places=6)
    UnitPrice = models.DecimalField(max_digits=24, decimal_places=6)

    class Meta:
        db_table = 'inv_document_item'
        verbose_name = 'Inventory Document Item'
        verbose_name_plural = 'Inventory Document Items'

    def __str__(self):
        return f"{self.DocumentId.DocumentNo} - {self.InventoryId.InventoryName} - Qty: {self.Quantity}"


class Inv_Document_Detail(models.Model):
    """Inventory Document Detail model for managing inventory document accounting details"""
    DocumentDetailId = models.AutoField(primary_key=True)
    DocumentId = models.ForeignKey(
        Inv_Document,
        on_delete=models.PROTECT,
        db_column='DocumentId',
        related_name='document_details'
    )
    AccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='AccountId',
        related_name='inv_document_details'
    )
    ClientId = models.ForeignKey(
        RefClient,
        on_delete=models.PROTECT,
        db_column='ClientId',
        related_name='inv_document_details',
        null=True,
        blank=True
    )
    CurrencyId = models.ForeignKey(
        Ref_Currency,
        on_delete=models.PROTECT,
        db_column='CurrencyId',
        related_name='inv_document_details',
        null=True,
        blank=True
    )
    CurrencyExchange = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    CurrencyAmount = models.DecimalField(max_digits=24, decimal_places=6)
    IsDebit = models.BooleanField()
    DebitAmount = models.DecimalField(max_digits=24, decimal_places=6, default=0)
    CreditAmount = models.DecimalField(max_digits=24, decimal_places=6, default=0)

    class Meta:
        db_table = 'inv_document_detail'
        verbose_name = 'Inventory Document Detail'
        verbose_name_plural = 'Inventory Document Details'

    def __str__(self):
        return f"{self.DocumentId.DocumentNo} - {self.AccountId.AccountName} - {self.CurrencyAmount}"



class Ref_Period(models.Model):
    """Period model for managing accounting periods"""
    PeriodId = models.SmallIntegerField(primary_key=True)
    QuarterId = models.SmallIntegerField()
    PeriodName = models.CharField(max_length=17)
    BeginDate = models.DateField()
    EndDate = models.DateField()
    IsLock = models.BooleanField(default=False, help_text="Whether this period is locked for transactions")

    class Meta:
        db_table = 'ref_period'
        verbose_name = 'Period'
        verbose_name_plural = 'Periods'

    def __str__(self):
        return f"{self.PeriodId} - {self.PeriodName}"


class Ref_Constant(models.Model):
    """Constant model for storing system constants and configuration values"""
    ConstantID = models.SmallIntegerField(primary_key=True)
    ConstantDescription = models.CharField(max_length=60)
    ConstantName = models.CharField(max_length=60)

    class Meta:
        db_table = 'ref_constant'
        verbose_name = 'Constant'
        verbose_name_plural = 'Constants'

    def __str__(self):
        return f"{self.ConstantName} - {self.ConstantDescription}"


class Inv_Beginning_Balance(models.Model):
    """Inventory Beginning Balance model for managing initial inventory balances"""
    BeginningBalanceId = models.AutoField(primary_key=True, db_column='BeginningBalanceId')
    AccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='AccountId',
        related_name='inv_beginning_balances'
    )
    InventoryId = models.ForeignKey(
        RefInventory,
        on_delete=models.PROTECT,
        db_column='InventoryId',
        related_name='inv_beginning_balances'
    )
    Quantity = models.DecimalField(max_digits=24, decimal_places=6)
    UnitCost = models.DecimalField(max_digits=24, decimal_places=6)
    UnitPrice = models.DecimalField(max_digits=24, decimal_places=6)
    WarehouseId = models.ForeignKey(
        Ref_Warehouse,
        on_delete=models.PROTECT,
        db_column='WarehouseId',
        related_name='inv_beginning_balances'
    )
    EmployeeId = models.IntegerField(null=True, blank=True)
    CreatedDate = models.DateField(auto_now_add=True)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column='CreatedBy',
        related_name='created_inv_beginning_balances'
    )
    ModifiedDate = models.DateField(auto_now=True)
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column='ModifiedBy',
        related_name='modified_inv_beginning_balances'
    )
    IsDelete = models.BooleanField(default=False)

    class Meta:
        db_table = 'inv_beginning_balance'
        verbose_name = 'Inventory Beginning Balance'
        verbose_name_plural = 'Inventory Beginning Balances'
        indexes = [
            models.Index(fields=['AccountId']),
            models.Index(fields=['InventoryId']),
            models.Index(fields=['WarehouseId']),
            models.Index(fields=['EmployeeId']),
            models.Index(fields=['CreatedDate']),
            models.Index(fields=['IsDelete']),
        ]

    def __str__(self):
        return f"{self.InventoryId.InventoryName} - {self.Quantity} @ {self.UnitCost}"

    def save(self, *args, **kwargs):
        # Set ModifiedBy to CreatedBy if not specified
        if not self.ModifiedBy_id and self.CreatedBy_id:
            self.ModifiedBy = self.CreatedBy
        super().save(*args, **kwargs)


class Ast_Beginning_Balance(models.Model):
    """Asset Beginning Balance model for managing initial asset balances"""
    BeginningBalanceId = models.AutoField(primary_key=True, db_column='BeginningBalanceId')
    AccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='AccountId',
        related_name='ast_beginning_balances'
    )
    AssetCardId = models.ForeignKey(
        Ref_Asset_Card,
        on_delete=models.PROTECT,
        db_column='AssetCardId',
        related_name='ast_beginning_balances'
    )
    Quantity = models.IntegerField()
    UnitCost = models.DecimalField(max_digits=24, decimal_places=6)
    UnitPrice = models.DecimalField(max_digits=24, decimal_places=6)
    CumulatedDepreciation = models.DecimalField(max_digits=24, decimal_places=6, default=0, null=True, blank=True)
    ClientId = models.ForeignKey(
        RefClient,
        on_delete=models.PROTECT,
        db_column='ClientId',
        related_name='ast_beginning_balances',
        null=True,
        blank=True
    )
    CreatedDate = models.DateField(auto_now_add=True)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column='CreatedBy',
        related_name='created_ast_beginning_balances'
    )
    ModifiedDate = models.DateField(auto_now=True)
               
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column='ModifiedBy',
        related_name='modified_ast_beginning_balances'
    )
    IsDelete = models.BooleanField(default=False)

    class Meta:
        db_table = 'ast_beginning_balance'
        verbose_name = 'Asset Beginning Balance'
        verbose_name_plural = 'Asset Beginning Balances'
        indexes = [
            models.Index(fields=['AccountId']),
            models.Index(fields=['AssetCardId']),
            models.Index(fields=['ClientId']),
            models.Index(fields=['CreatedDate']),
            models.Index(fields=['IsDelete']),
        ]

    def __str__(self):
        return f"{self.AssetCardId.AssetCardCode} - {self.Quantity} @ {self.UnitCost}"

    def save(self, *args, **kwargs):
        # Set ModifiedBy to CreatedBy if not specified
        if not self.ModifiedBy_id and self.CreatedBy_id:
            self.ModifiedBy = self.CreatedBy
        super().save(*args, **kwargs)


class Ref_Asset_Depreciation_Account(models.Model):
    """Asset Depreciation Account model for managing asset depreciation account mappings"""
    AstDepId = models.AutoField(primary_key=True)
    AssetAccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='AssetAccountId',
        related_name='asset_depreciation_asset_accounts'
    )
    DepreciationAccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='DepreciationAccountId',
        related_name='asset_depreciation_depreciation_accounts'
    )
    ExpenseAccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='ExpenseAccountId',
        related_name='asset_depreciation_expense_accounts'
    )
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column='CreatedBy',
        related_name='created_asset_depreciation_accounts'
    )
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column='ModifiedBy',
        related_name='modified_asset_depreciation_accounts'
    )
    CreatedDate = models.DateField(auto_now_add=True)
    ModifiedDate = models.DateField(auto_now=True)
    IsDelete = models.BooleanField(default=False)

    class Meta:
        db_table = 'ref_asset_depreciation_account'
        verbose_name = 'Asset Depreciation Account'
        verbose_name_plural = 'Asset Depreciation Accounts'

    def __str__(self):
        return f"Asset Depreciation Mapping - {self.AstDepId}"

    def save(self, *args, **kwargs):
        # Set ModifiedBy to CreatedBy if not specified
        if not self.ModifiedBy_id and self.CreatedBy_id:
            self.ModifiedBy = self.CreatedBy
        super().save(*args, **kwargs)


class CashBeginningBalance(models.Model):
    """Cash Beginning Balance model for managing initial cash balances"""
    BeginningBalanceID = models.AutoField(primary_key=True, db_column='BeginningBalanceId')
    AccountID = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='AccountId',
        related_name='cash_beginning_balances'
    )
    ClientID = models.ForeignKey(
        RefClient,
        on_delete=models.PROTECT,
        db_column='ClientId',
        related_name='cash_beginning_balances'        
    )
    CurrencyID = models.ForeignKey(
        Ref_Currency,
        on_delete=models.PROTECT,
        db_column='CurrencyId',
        related_name='cash_beginning_balances'
    )
    CurrencyExchange = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    CurrencyAmount = models.DecimalField(max_digits=24, decimal_places=6, default=0)
    CreatedDate = models.DateField(auto_now_add=True)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column='CreatedBy',
        related_name='created_cash_beginning_balances'
    )
    ModifiedDate = models.DateField(auto_now=True)
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column='ModifiedBy',
        related_name='modified_cash_beginning_balances'
        
    )
    IsDelete = models.BooleanField(default=False)

    class Meta:
        db_table = 'cash_beginning_balance'
        verbose_name = 'Cash Beginning Balance'
        verbose_name_plural = 'Cash Beginning Balances'
        indexes = [
            models.Index(fields=['AccountID']),
            models.Index(fields=['ClientID']),
            models.Index(fields=['CurrencyID']),
            models.Index(fields=['CreatedDate']),
            models.Index(fields=['IsDelete']),
        ]

    def __str__(self):
        return f"{self.AccountID.AccountName} - {self.CurrencyAmount} {self.CurrencyID.Currency_name}"

    def save(self, *args, **kwargs):
        # Set ModifiedBy to CreatedBy if not specified
        if not self.ModifiedBy_id and self.CreatedBy_id:
            self.ModifiedBy = self.CreatedBy
        super().save(*args, **kwargs)


class Ast_Document(models.Model):
    """Asset Document model for managing Asset transactions"""
    DocumentId = models.AutoField(primary_key=True)
    DocumentNo = models.CharField(max_length=20)
    DocumentTypeId = models.ForeignKey(
        Ref_Document_Type,
        on_delete=models.PROTECT,
        db_column='DocumentTypeId',
        related_name='ast_documents'
    )
    DocumentDate = models.DateField()
    AccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='AccountId',
        related_name='ast_documents'
    )
    ClientId = models.ForeignKey(
        RefClient,
        on_delete=models.PROTECT,
        db_column='ClientId',
        related_name='ast_documents'
    )
    TemplateId = models.ForeignKey(
        'Ref_Template',
        on_delete=models.PROTECT,
        db_column='TemplateId',
        related_name='ast_documents',
        null=True,
        blank=True
    )
    Description = models.CharField(max_length=200)
    IsVat = models.BooleanField(default=False, null=True, blank=True)
    VatAccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='VatAccountId',
        related_name='vat_ast_documents',
        null=True,
        blank=True
    )
    VatPercent = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    IsLock = models.BooleanField(default=False, null=True, blank=True)
    IsDelete = models.BooleanField(default=False)
    ModifiedBy = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='modified_ast_documents', db_column='ModifiedBy')
    ModifiedDate = models.DateField(auto_now=True)
    CreatedBy = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='created_ast_documents', db_column='CreatedBy')
    CreatedDate = models.DateField(auto_now_add=True)
    IsPosted = models.BooleanField(default=False, null=True, blank=True)
    CostAmount = models.DecimalField(max_digits=24, decimal_places=6, null=True, blank=True)
    PriceAmount = models.DecimalField(max_digits=24, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = 'ast_document'
        verbose_name = 'Asset Document'
        verbose_name_plural = 'Asset Documents'

    def __str__(self):
        return f"{self.DocumentNo} - {self.Description}"


class Ast_Document_Detail(models.Model):
    """Asset Document Detail model for managing asset document accounting details"""
    DocumentDetailId = models.AutoField(primary_key=True)
    DocumentId = models.ForeignKey(
        Ast_Document,
        on_delete=models.PROTECT,
        db_column='DocumentId',
        related_name='document_details'
    )
    AccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='AccountId',
        related_name='ast_document_details'
    )
    ClientId = models.ForeignKey(
        RefClient,
        on_delete=models.PROTECT,
        db_column='ClientId',
        related_name='ast_document_details',
        null=True,
        blank=True
    )
    CurrencyId = models.ForeignKey(
        Ref_Currency,
        on_delete=models.PROTECT,
        db_column='CurrencyId',
        related_name='ast_document_details',
        null=True,
        blank=True
    )
    CurrencyExchange = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    CurrencyAmount = models.DecimalField(max_digits=24, decimal_places=6)
    IsDebit = models.BooleanField()
    DebitAmount = models.DecimalField(max_digits=24, decimal_places=6, default=0)
    CreditAmount = models.DecimalField(max_digits=24, decimal_places=6, default=0)

    class Meta:
        db_table = 'ast_document_detail'
        verbose_name = 'Asset Document Detail'
        verbose_name_plural = 'Asset Document Details'

    def __str__(self):
        return f"{self.DocumentId.DocumentNo} - {self.AccountId.AccountName} - {self.CurrencyAmount}"


class Ast_Document_Item(models.Model):
    """Asset Document Item model for managing Asset document line items"""
    DocumentItemId = models.AutoField(primary_key=True)
    DocumentId = models.ForeignKey(
        Ast_Document,
        on_delete=models.PROTECT,
        db_column='DocumentId',
        related_name='document_items'
    )
    AssetCardId = models.ForeignKey(
        Ref_Asset_Card,
        on_delete=models.PROTECT,
        db_column='AssetCardId',
        related_name='document_items'
    )
    Quantity = models.DecimalField(max_digits=24, decimal_places=6)
    UnitCost = models.DecimalField(max_digits=24, decimal_places=6)
    UnitPrice = models.DecimalField(max_digits=24, decimal_places=6)

    class Meta:
        db_table = 'ast_document_item'
        verbose_name = 'Asset Document Item'
        verbose_name_plural = 'Asset Document Items'

    def __str__(self):
        return f"{self.DocumentId.DocumentNo} - {self.AssetCardId.assetCardName} - Qty: {self.Quantity}"


class AstDepreciationExpense(models.Model):
    """Asset Depreciation Expense model for managing asset depreciation calculations"""
    AstDepExpId = models.AutoField(primary_key=True, db_column='AstDepExpId')
    AssetCardId = models.ForeignKey(
        Ref_Asset_Card,
        on_delete=models.PROTECT,
        db_column='AssetCardId',
        related_name='depreciation_expenses'
    )
    PeriodId = models.ForeignKey(
        Ref_Period,
        on_delete=models.PROTECT,
        db_column='PeriodId',
        related_name='depreciation_expenses'
    )
    ExpenseDay = models.SmallIntegerField()
    DepreciationDate = models.DateField(null=True, blank=True)
    ExpenseAmount = models.DecimalField(max_digits=24, decimal_places=6)
    DocumentId = models.ForeignKey(
        Ast_Document,
        on_delete=models.PROTECT,
        db_column='DocumentId',
        related_name='depreciation_expenses',
        null=True,
        blank=True
    )
    DebitAccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='DebitAccountId',
        related_name='depreciation_debit_expenses'
    )
    CreditAccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='CreditAccountId',
        related_name='depreciation_credit_expenses'
    )
    AccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='AccountId',
        related_name='depreciation_expenses'
    )
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column='CreatedBy',
        related_name='created_depreciation_expenses'
    )
    CreatedDate = models.DateField(auto_now_add=True)
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column='ModifiedBy',
        related_name='modified_depreciation_expenses',
        null=True,
        blank=True
    )
    ModifiedDate = models.DateField(auto_now=True)

    class Meta:
        db_table = 'ast_depreciation_expense'
        verbose_name = 'Asset Depreciation Expense'
        verbose_name_plural = 'Asset Depreciation Expenses'
        indexes = [
            models.Index(fields=['AssetCardId']),
            models.Index(fields=['PeriodId']),
            models.Index(fields=['ExpenseDay']),
            models.Index(fields=['CreatedDate']),
        ]

    def __str__(self):
        return f"{self.AssetCardId.AssetCardName} - Period {self.PeriodId.PeriodName} - Amount: {self.ExpenseAmount}"


class Ref_Template(models.Model):
    """Template model for document templates"""
    TemplateId = models.SmallAutoField(primary_key=True)
    TemplateName = models.CharField(max_length=70)
    DocumentTypeId = models.ForeignKey(
        Ref_Document_Type,
        on_delete=models.PROTECT,
        db_column='DocumentTypeId',
        related_name='templates'
    )
    AccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='AccountId',
        related_name='templates',
        
    )
    # Keep IsVat to satisfy existing DB NOT NULL constraint; default to False
    IsVat = models.BooleanField(default=False, db_column='IsVat')
    
    IsDelete = models.BooleanField(default=False)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_templates',
        db_column='CreatedBy'
    )
    CreatedDate = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'ref_template'
        verbose_name = 'Template'
        verbose_name_plural = 'Templates'
        indexes = [
            models.Index(fields=['DocumentTypeId']),
            models.Index(fields=['IsDelete']),
            models.Index(fields=['CreatedDate']),
        ]

    def __str__(self):
        return f"{self.TemplateName} - {self.DocumentTypeId.Description}"


class Ref_Template_Detail(models.Model):
    """Template Detail model for template details"""
    TemplateDetailId = models.SmallAutoField(primary_key=True)
    AccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='AccountId',
        related_name='template_details'
    )
    IsDebit = models.BooleanField(null=True, blank=True)
    CashFlowId = models.ForeignKey(
        Ref_CashFlow,
        on_delete=models.PROTECT,
        db_column='CashFlowId',
        related_name='template_details',
        null=True,
        blank=True
    )
    TemplateId = models.ForeignKey(
        Ref_Template,
        on_delete=models.CASCADE,
        db_column='TemplateId',
        related_name='template_details'
    )

    class Meta:
        db_table = 'ref_template_detail'
        verbose_name = 'Template Detail'
        verbose_name_plural = 'Template Details'
        indexes = [
            models.Index(fields=['TemplateId']),
            models.Index(fields=['AccountId']),
            models.Index(fields=['IsDebit']),
        ]


class St_Balance(models.Model):
    """Stock Balance model for managing stock balances"""
    StbalanceId = models.SmallIntegerField(primary_key=True)
    StbalanceCode = models.CharField(max_length=30)
    StbalanceName = models.CharField(max_length=150)
    BeginBalance = models.DecimalField(max_digits=24, decimal_places=6, default=0)
    EndBalance = models.DecimalField(max_digits=24, decimal_places=6, default=0)
    Order = models.SmallIntegerField()

    class Meta:
        db_table = 'st_balance'
        verbose_name = 'Stock Balance'
        verbose_name_plural = 'Stock Balances'
        ordering = ['Order', 'StbalanceCode']

    def __str__(self):
        return f"{self.StbalanceCode} - {self.StbalanceName}"


class St_Income(models.Model):
    StIncomeId = models.SmallIntegerField(primary_key=True)
    StIncome = models.CharField(max_length=30)
    StIncomeName = models.CharField(max_length=150)
    EndBalance = models.DecimalField(max_digits=24, decimal_places=6, null=True, blank=True)
    Order = models.SmallIntegerField()

    class Meta:
        db_table = 'st_income'
        verbose_name = 'Stock Income'
        verbose_name_plural = 'Stock Incomes'
        ordering = ['Order', 'StIncome']


class St_CashFlow(models.Model):
    """Cash Flow Statement model for managing cash flow categories"""
    StCashFlowId = models.SmallIntegerField(primary_key=True, db_column='StCashFlowId')
    StCashFlowCode = models.CharField(max_length=30, db_column='StCashFlowCode')
    StCashFlowName = models.CharField(max_length=150, db_column='StCashFlowName')
    EndBalance = models.DecimalField(max_digits=24, decimal_places=6, default=0, db_column='EndBalance')
    Order = models.SmallIntegerField(db_column='Order')
    IsVisible = models.BooleanField(default=True, db_column='IsVisible')
 
    class Meta:
        db_table = 'st_cashflow'
        verbose_name = 'Cash Flow Category'
        verbose_name_plural = 'Cash Flow Categories'
        ordering = ['Order', 'StCashFlowCode']
 
    def __str__(self):
        return f"{self.StCashFlowCode} - {self.StCashFlowName}"         