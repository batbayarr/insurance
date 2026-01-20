from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Ref_Account_Type(models.Model):
    """Account Type model for categorizing accounts"""
    AccountTypeId = models.SmallIntegerField(primary_key=True)
    AccountTypeCode = models.CharField(max_length=4, unique=True)
    AccountTypeName = models.CharField(max_length=150, unique=True)    
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
    ClientRegister = models.CharField(max_length=10, blank=True, null=True)
    IsVat = models.BooleanField(default=False)
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
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_assets',
        db_column='CreatedBy',
        default=1,
    )
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='modified_assets',
        db_column='ModifiedBy',
        default=1,
    )
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
    CumulatedDepreciation = models.DecimalField(max_digits=24, decimal_places=6, default=0, null=True, blank=True)
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
    TemplateName = models.CharField(max_length=150)
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


class Ref_Product_Group(models.Model):
    """Product Group model for categorizing insurance products"""
    ProductGroupId = models.AutoField(primary_key=True)
    ProductGroupName = models.CharField(max_length=250)
    ProductGroupCode = models.CharField(max_length=50)
    IsActive = models.BooleanField(default=True)
    DebitAccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='DebitAccountId',
        related_name='product_groups_debit',
        null=True,
        blank=True
    )
    CreditAccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='CreditAccountId',
        related_name='product_groups_credit',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'ins_ref_product_group'
        verbose_name = 'Product Group'
        verbose_name_plural = 'Product Groups'

    def __str__(self):
        return f"{self.ProductGroupCode} - {self.ProductGroupName}"


class Ref_Product_Type(models.Model):
    """Product Type model for categorizing insurance product types"""
    ProductTypeId = models.AutoField(primary_key=True)
    ProductTypeName = models.CharField(max_length=250)
    ProductTypeCode = models.CharField(max_length=50)
    ProductGroupId = models.ForeignKey(
        Ref_Product_Group,
        on_delete=models.PROTECT,
        db_column='ProductGroupId',
        related_name='product_types'
    )
    IsActive = models.BooleanField(default=True)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_product_types',
        db_column='CreatedBy'
    )
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='modified_product_types',
        db_column='ModifiedBy'
    )
    CreatedDate = models.DateTimeField(auto_now_add=True)
    ModifiedDate = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ins_ref_product_type'
        verbose_name = 'Product Type'
        verbose_name_plural = 'Product Types'

    def __str__(self):
        return f"{self.ProductTypeCode} - {self.ProductTypeName}"


class Ref_Product(models.Model):
    """Product model for insurance products"""
    ProductId = models.AutoField(primary_key=True)
    ProductName = models.CharField(max_length=150)
    ProductCode = models.CharField(max_length=50)
    ProductTypeId = models.ForeignKey(
        Ref_Product_Type,
        on_delete=models.PROTECT,
        db_column='ProductTypeId',
        related_name='products'
    )
    IsActive = models.BooleanField(default=True)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_products',
        db_column='CreatedBy'
    )
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='modified_products',
        db_column='ModifiedBy'
    )
    CreatedDate = models.DateTimeField(auto_now_add=True)
    ModifiedDate = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ins_ref_product'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return f"{self.ProductCode} - {self.ProductName}"


class Ref_Item_Type(models.Model):
    """Item Type model for categorizing items with hierarchical structure"""
    ItemTypeId = models.AutoField(primary_key=True)
    ItemTypeName = models.CharField(max_length=250)
    ItemTypeCode = models.CharField(max_length=50)
    IsActive = models.BooleanField(default=True)
    ParentId = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        db_column='ParentId',
        related_name='child_item_types',
        null=True,
        blank=True
    )
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_item_types',
        db_column='CreatedBy'
    )
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='modified_item_types',
        db_column='ModifiedBy'
    )
    CreatedDate = models.DateTimeField(auto_now_add=True)
    ModifiedDate = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ins_ref_item_type'
        verbose_name = 'Item Type'
        verbose_name_plural = 'Item Types'

    def __str__(self):
        return f"{self.ItemTypeCode} - {self.ItemTypeName}"


class Ref_Item(models.Model):
    """Item model for insurance items"""
    ItemId = models.AutoField(primary_key=True)
    ItemName = models.CharField(max_length=500)
    ItemCode = models.CharField(max_length=50)
    ItemTypeId = models.ForeignKey(
        Ref_Item_Type,
        on_delete=models.PROTECT,
        db_column='ItemTypeId',
        related_name='items'
    )
    IsActive = models.BooleanField(default=True)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_items',
        db_column='CreatedBy'
    )
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='modified_items',
        db_column='ModifiedBy'
    )
    CreatedDate = models.DateTimeField(auto_now_add=True)
    ModifiedDate = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ins_ref_item'
        verbose_name = 'Item'
        verbose_name_plural = 'Items'

    def __str__(self):
        return f"{self.ItemCode} - {self.ItemName}"


class Ref_Item_Question(models.Model):
    """Item Question model for insurance item questions"""
    ItemQuestionId = models.AutoField(primary_key=True)
    ItemQuestionName = models.CharField(max_length=200)
    ItemQuestionCode = models.CharField(max_length=50)
    ItemId = models.ForeignKey(
        Ref_Item,
        on_delete=models.PROTECT,
        db_column='ItemId',
        related_name='item_questions'
    )
    QuestionType = models.CharField(max_length=100)
    FieldType = models.CharField(max_length=100)
    FieldValue = models.CharField(max_length=100, null=True, blank=True)
    Order = models.IntegerField(db_column='Order')
    FieldMask = models.CharField(max_length=500, null=True, blank=True)
    IsActive = models.BooleanField(default=True)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_item_questions',
        db_column='CreatedBy'
    )
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='modified_item_questions',
        db_column='ModifiedBy'
    )
    CreatedDate = models.DateTimeField(auto_now_add=True)
    ModifiedDate = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ins_ref_item_question'
        verbose_name = 'Item Question'
        verbose_name_plural = 'Item Questions'
        ordering = ['Order', 'ItemQuestionCode']

    def __str__(self):
        return f"{self.ItemQuestionCode} - {self.ItemQuestionName}"


class Ref_Risk_Type(models.Model):
    """Risk Type model for categorizing insurance risks"""
    RiskTypeId = models.AutoField(primary_key=True)
    RiskTypeName = models.CharField(max_length=200)
    RiskTypeCode = models.CharField(max_length=50)
    IsActive = models.BooleanField(default=True)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_risk_types',
        db_column='CreatedBy'
    )
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='modified_risk_types',
        db_column='ModifiedBy'
    )
    CreatedDate = models.DateTimeField(auto_now_add=True)
    ModifiedDate = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ins_ref_risk_type'
        verbose_name = 'Risk Type'
        verbose_name_plural = 'Risk Types'

    def __str__(self):
        return f"{self.RiskTypeCode} - {self.RiskTypeName}"


class Ref_Risk(models.Model):
    """Risk model for insurance risks"""
    RiskId = models.AutoField(primary_key=True)
    RiskName = models.CharField(max_length=200)
    RiskCode = models.CharField(max_length=50)
    CategoryName = models.CharField(max_length=100, null=True, blank=True)
    RiskTypeId = models.ForeignKey(
        Ref_Risk_Type,
        on_delete=models.PROTECT,
        db_column='RiskTypeId',
        related_name='risks'
    )
    IsActive = models.BooleanField(default=True)
    IsCoreRisk = models.BooleanField(default=True)
    Description = models.CharField(max_length=500, null=True, blank=True)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_risks',
        db_column='CreatedBy'
    )
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='modified_risks',
        db_column='ModifiedBy'
    )
    CreatedDate = models.DateTimeField(auto_now_add=True)
    ModifiedDate = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ins_ref_risk'
        verbose_name = 'Risk'
        verbose_name_plural = 'Risks'

    def __str__(self):
        return f"{self.RiskCode} - {self.RiskName}"


class Ref_Ins_Client(models.Model):
    """Insurance Client model for managing insurance client information"""
    InsClientId = models.AutoField(primary_key=True)
    ClientId = models.ForeignKey(
        RefClient,
        on_delete=models.PROTECT,
        db_column='ClientId',
        related_name='ins_clients'
    )
    InsClientCode = models.CharField(max_length=50)
    OrgName = models.CharField(max_length=100, null=True, blank=True)
    OrgRegister = models.CharField(max_length=12, null=True, blank=True)
    IsOrg = models.BooleanField(default=False)
    DistrictId = models.IntegerField(null=True, blank=True)
    IsPolitics = models.BooleanField(default=False)
    IsInvestor = models.BooleanField(default=False)
    FirstName = models.CharField(max_length=100, null=True, blank=True)
    LastName = models.CharField(max_length=100, null=True, blank=True)
    Phone1 = models.CharField(max_length=20, null=True, blank=True)
    Phone2 = models.CharField(max_length=20, null=True, blank=True)
    Email = models.CharField(max_length=100, null=True, blank=True)
    DriverLicenceNo = models.CharField(max_length=50, null=True, blank=True)
    EmergencyContact = models.CharField(max_length=150, null=True, blank=True)
    Gender = models.CharField(max_length=50, null=True, blank=True)
    NationalityId = models.IntegerField(null=True, blank=True)
    PhotoPath = models.CharField(max_length=250, null=True, blank=True)
    IsActive = models.BooleanField(default=True)
    DriverLicentceYear = models.DateField(null=True, blank=True)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_ins_clients',
        db_column='CreatedBy'
    )
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='modified_ins_clients',
        db_column='ModifiedBy'
    )
    CreatedDate = models.DateTimeField(auto_now_add=True)
    ModifiedDate = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ins_ref_client'
        verbose_name = 'Insurance Client'
        verbose_name_plural = 'Insurance Clients'

    def __str__(self):
        if self.OrgName:
            return f"{self.InsClientCode} - {self.OrgName}"
        elif self.FirstName and self.LastName:
            return f"{self.InsClientCode} - {self.FirstName} {self.LastName}"
        return f"{self.InsClientCode}"


class Ref_Policy_Template(models.Model):
    """Policy Template model for insurance policy templates"""
    PolicyTemplateId = models.AutoField(primary_key=True)
    PolicyTemplateName = models.CharField(max_length=200)
    Description = models.CharField(max_length=200, null=True, blank=True)
    IsActive = models.BooleanField(default=True)
    FilePath = models.CharField(max_length=250, null=True, blank=True)
    IsDelete = models.BooleanField(default=False)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_policy_templates',
        db_column='CreatedBy'
    )
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='modified_policy_templates',
        db_column='ModifiedBy'
    )
    CreatedDate = models.DateTimeField(auto_now_add=True)
    ModifiedDate = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ins_ref_template'
        verbose_name = 'Policy Template'
        verbose_name_plural = 'Policy Templates'

    def __str__(self):
        return f"{self.PolicyTemplateName}"


class Ref_Template_Account(models.Model):
    """Template Account model for policy template accounting details"""
    TemplateAccountId = models.AutoField(primary_key=True)
    PolicyTemplateId = models.ForeignKey(
        Ref_Policy_Template,
        on_delete=models.PROTECT,
        db_column='PolicyTemplateId',
        related_name='template_accounts'
    )
    AccountId = models.ForeignKey(
        Ref_Account,
        on_delete=models.PROTECT,
        db_column='AccountId',
        related_name='template_accounts'
    )
    IsDebit = models.BooleanField()
    CashFlowId = models.ForeignKey(
        Ref_CashFlow,
        on_delete=models.PROTECT,
        db_column='CashFlowId',
        related_name='template_accounts',
        null=True,
        blank=True
    )
    CalculationType = models.BooleanField(default=False)

    class Meta:
        db_table = 'ins_ref_template_account'
        verbose_name = 'Template Account'
        verbose_name_plural = 'Template Accounts'

    def __str__(self):
        return f"{self.PolicyTemplateId.PolicyTemplateName} - {self.AccountId.AccountName} ({'Debit' if self.IsDebit else 'Credit'})"


class Ref_Template_Product(models.Model):
    """Template Product model linking templates to products"""
    TemplateProductId = models.AutoField(primary_key=True)
    TemplateId = models.ForeignKey(
        Ref_Policy_Template,
        on_delete=models.PROTECT,
        db_column='TemplateId',
        related_name='template_products'
    )
    ProductId = models.ForeignKey(
        Ref_Product,
        on_delete=models.PROTECT,
        db_column='ProductId',
        related_name='template_products'
    )

    class Meta:
        db_table = 'ins_ref_template_product'
        verbose_name = 'Template Product'
        verbose_name_plural = 'Template Products'

    def __str__(self):
        return f"{self.TemplateId.PolicyTemplateName} - {self.ProductId.ProductName}"


class Ref_Template_Product_Item(models.Model):
    """Template Product Item model linking template products to items"""
    TemplateProductItemId = models.AutoField(primary_key=True)
    TemplateProductId = models.ForeignKey(
        Ref_Template_Product,
        on_delete=models.PROTECT,
        db_column='TemplateProductId',
        related_name='template_product_items'
    )
    ItemId = models.ForeignKey(
        Ref_Item,
        on_delete=models.PROTECT,
        db_column='ItemId',
        related_name='template_product_items'
    )

    class Meta:
        db_table = 'ins_ref_template_product_item'
        verbose_name = 'Template Product Item'
        verbose_name_plural = 'Template Product Items'

    def __str__(self):
        return f"{self.TemplateProductId} - {self.ItemId.ItemName}"


class Ref_Template_Product_Item_Risk(models.Model):
    """Template Product Item Risk model linking template product items to risks with commission"""
    TemplateProductItemRiskId = models.AutoField(primary_key=True)
    TemplateProductItemId = models.ForeignKey(
        Ref_Template_Product_Item,
        on_delete=models.PROTECT,
        db_column='TemplateProductItemId',
        related_name='template_product_item_risks'
    )
    RiskId = models.ForeignKey(
        Ref_Risk,
        on_delete=models.PROTECT,
        db_column='RiskId',
        related_name='template_product_item_risks'
    )
    CommPercent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'ins_ref_template_product_item_risk'
        verbose_name = 'Template Product Item Risk'
        verbose_name_plural = 'Template Product Item Risks'

    def __str__(self):
        return f"{self.TemplateProductItemId} - {self.RiskId.RiskName} ({self.CommPercent}%)"


class Ref_Template_Design(models.Model):
    """Template Design model for policy template field design configuration"""
    DesignId = models.AutoField(primary_key=True)
    PolicyTemplateId = models.ForeignKey(
        Ref_Policy_Template,
        on_delete=models.PROTECT,
        db_column='PolicyTemplateId',
        related_name='template_designs'
    )
    TableNameEng = models.CharField(max_length=60)
    TableNameMon = models.CharField(max_length=60)
    FieldNameEng = models.CharField(max_length=60)
    FieldNameMon = models.CharField(max_length=60)
    IsStatic = models.BooleanField(default=False)
    IsActive = models.BooleanField(default=True)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_template_designs',
        db_column='CreatedBy'
    )
    CreatedDate = models.DateField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'ins_ref_template_design'
        verbose_name = 'Template Design'
        verbose_name_plural = 'Template Designs'

    def __str__(self):
        return f"{self.PolicyTemplateId.PolicyTemplateName} - {self.TableNameEng}.{self.FieldNameEng}"


class Ref_Branch(models.Model):
    """Branch model for insurance branches"""
    BranchId = models.AutoField(primary_key=True)
    BranchCode = models.CharField(max_length=4)
    BranchName = models.CharField(max_length=50)
    DirectorName = models.CharField(max_length=15, null=True, blank=True)
    IsActive = models.BooleanField(default=True)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_branches',
        db_column='CreatedBy'
    )
    CreatedDate = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ins_ref_branch'
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'

    def __str__(self):
        return f"{self.BranchCode} - {self.BranchName}"


class Ref_Channel(models.Model):
    """Channel model for insurance channels"""
    ChannelId = models.AutoField(primary_key=True)
    ChannelName = models.CharField(max_length=50)
    IsActive = models.BooleanField(default=True)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_channels',
        db_column='CreatedBy'
    )
    CreatedDate = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ins_ref_channel'
        verbose_name = 'Channel'
        verbose_name_plural = 'Channels'

    def __str__(self):
        return f"{self.ChannelName}"


class Ref_Branch_User(models.Model):
    """Branch User model for managing user-branch-channel relationships"""
    UserBranchId = models.AutoField(primary_key=True)
    UserId = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column='UserId',
        related_name='branch_users'
    )
    ChannelId = models.ForeignKey(
        Ref_Channel,
        on_delete=models.PROTECT,
        db_column='ChannelId',
        related_name='branch_users'
    )
    BranchId = models.ForeignKey(
        Ref_Branch,
        on_delete=models.PROTECT,
        db_column='BranchId',
        related_name='branch_users'
    )
    IsActive = models.BooleanField(default=True)
    CreatedDate = models.DateTimeField(auto_now_add=True)
    ModifiedDate = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ins_ref_branch_user'
        verbose_name = 'Branch User'
        verbose_name_plural = 'Branch Users'

    def __str__(self):
        return f"{self.UserId.username} - {self.BranchId.BranchName} ({self.ChannelId.ChannelName})"


class Policy_Main(models.Model):
    """Policy Main model for insurance policies"""
    PolicyId = models.AutoField(primary_key=True)
    PolicyNo = models.CharField(max_length=25)
    ClientId = models.ForeignKey(
        RefClient,
        on_delete=models.PROTECT,
        db_column='ClientId',
        related_name='policies'
    )
    AgentId = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        db_column='AgentId',
        related_name='agent_policies'
    )
    PolicyTemplateId = models.ForeignKey(
        Ref_Policy_Template,
        on_delete=models.PROTECT,
        db_column='PolicyTemplateId',
        related_name='policies'
    )
    BeginDate = models.DateField()
    EndDate = models.DateField()
    CurrencyId = models.ForeignKey(
        Ref_Currency,
        on_delete=models.PROTECT,
        db_column='CurrencyId',
        related_name='policies'
    )
    CurrencyExchange = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    CurrencyAmount = models.DecimalField(max_digits=24, decimal_places=6, null=True, blank=True)
    AgentBranchId = models.ForeignKey(
        Ref_Branch,
        on_delete=models.PROTECT,
        db_column='AgentBranchId',
        related_name='policies'
    )
    AgentChannelId = models.ForeignKey(
        Ref_Channel,
        on_delete=models.PROTECT,
        db_column='AgentChannelId',
        related_name='policies'
    )
    DirectorName = models.CharField(max_length=15, null=True, blank=True)
    IsActive = models.BooleanField(default=True)
    IsLock = models.BooleanField(default=False)
    IsPosted = models.BooleanField(default=False)
    ApprovedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='approved_policies',
        db_column='ApprovedBy',
        null=True,
        blank=True
    )
    Description = models.CharField(max_length=60, null=True, blank=True)
    StatusId = models.SmallIntegerField(null=True, blank=True)
    CreatedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='created_policies',
        db_column='CreatedBy'
    )
    ModifiedBy = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='modified_policies',
        db_column='ModifiedBy'
    )
    CreatedDate = models.DateTimeField(auto_now_add=True)
    ModifiedDate = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ins_policy_main'
        verbose_name = 'Policy'
        verbose_name_plural = 'Policies'

    def __str__(self):
        return f"{self.PolicyNo}"


class Policy_Main_Coinsurance(models.Model):
    """Policy Coinsurance model for policy coinsured clients"""
    PolicyCoInsuredId = models.AutoField(primary_key=True)
    PolicyId = models.ForeignKey(
        Policy_Main,
        on_delete=models.PROTECT,
        db_column='PolicyId',
        related_name='coinsurance'
    )
    ClientId = models.ForeignKey(
        RefClient,
        on_delete=models.PROTECT,
        db_column='ClientId',
        related_name='coinsurance_policies'
    )
    Description = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        db_table = 'ins_policy_main_coinsurance'
        verbose_name = 'Policy Coinsurance'
        verbose_name_plural = 'Policy Coinsurance'

    def __str__(self):
        return f"{self.PolicyId.PolicyNo} - {self.ClientId.ClientName}"


class Policy_Main_Schedule(models.Model):
    """Policy Payment Schedule model for policy payment schedules"""
    PolicyPaymentScheduleId = models.AutoField(primary_key=True)
    PolicyId = models.ForeignKey(
        Policy_Main,
        on_delete=models.PROTECT,
        db_column='PolicyId',
        related_name='payment_schedules'
    )
    DueDate = models.DateField()
    Amount = models.DecimalField(max_digits=24, decimal_places=6)

    class Meta:
        db_table = 'ins_policy_main_schedule'
        verbose_name = 'Policy Payment Schedule'
        verbose_name_plural = 'Policy Payment Schedules'

    def __str__(self):
        return f"{self.PolicyId.PolicyNo} - {self.DueDate} - {self.Amount}"


class Policy_Main_Files(models.Model):
    """Policy Files model for policy attachments"""
    PolicyAttachmentId = models.AutoField(primary_key=True)
    PolicyId = models.ForeignKey(
        Policy_Main,
        on_delete=models.PROTECT,
        db_column='PolicyId',
        related_name='policy_files'
    )
    FileName = models.CharField(max_length=50)
    FilePath = models.CharField(max_length=100)

    class Meta:
        db_table = 'ins_policy_main_files'
        verbose_name = 'Policy File'
        verbose_name_plural = 'Policy Files'

    def __str__(self):
        return f"{self.PolicyId.PolicyNo} - {self.FileName}"


class Policy_Main_Product(models.Model):
    """Policy Product model linking policies to products"""
    PolicyMainProductId = models.AutoField(primary_key=True)
    PolicyMainId = models.ForeignKey(
        Policy_Main,
        on_delete=models.PROTECT,
        db_column='PolicyMainId',
        related_name='policy_products'
    )
    ProductId = models.ForeignKey(
        Ref_Product,
        on_delete=models.PROTECT,
        db_column='ProductId',
        related_name='policy_products'
    )

    class Meta:
        db_table = 'ins_policy_main_product'
        verbose_name = 'Policy Product'
        verbose_name_plural = 'Policy Products'

    def __str__(self):
        return f"{self.PolicyMainId.PolicyNo} - {self.ProductId.ProductName if self.ProductId else 'N/A'}"


class Policy_Main_Product_Item(models.Model):
    """Policy Product Item model for policy product items with dates and valuation"""
    PolicyMainProductItemId = models.AutoField(primary_key=True)
    PolicyMainProductId = models.ForeignKey(
        Policy_Main_Product,
        on_delete=models.PROTECT,
        db_column='PolicyMainProductId',
        related_name='product_items'
    )
    ItemId = models.ForeignKey(
        Ref_Item,
        on_delete=models.PROTECT,
        db_column='ItemId',
        related_name='policy_product_items'
    )
    BeginDate = models.DateField(null=True, blank=True)
    EndDate = models.DateField(null=True, blank=True)
    Valuation = models.DecimalField(max_digits=24, decimal_places=6, null=True, blank=True)
    CommPercent = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    CommAmount = models.DecimalField(max_digits=24, decimal_places=6, null=True, blank=True)

    class Meta:
        db_table = 'ins_policy_main_product_item'
        verbose_name = 'Policy Product Item'
        verbose_name_plural = 'Policy Product Items'

    def __str__(self):
        return f"{self.PolicyMainProductId} - {self.ItemId.ItemName if self.ItemId else 'N/A'}"


class Policy_Main_Product_Item_Risk(models.Model):
    """Policy Product Item Risk model for policy product item risks"""
    PolicyMainProductItemRiskId = models.AutoField(primary_key=True)
    PolicyMainProductItemId = models.ForeignKey(
        Policy_Main_Product_Item,
        on_delete=models.PROTECT,
        db_column='PolicyMainProductItemId',
        related_name='item_risks'
    )
    RiskId = models.ForeignKey(
        Ref_Risk,
        on_delete=models.PROTECT,
        db_column='RiskId',
        related_name='policy_product_item_risks'
    )
    RiskPercent = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)

    class Meta:
        db_table = 'ins_policy_main_product_item_risk'
        verbose_name = 'Policy Product Item Risk'
        verbose_name_plural = 'Policy Product Item Risks'

    def __str__(self):
        return f"{self.PolicyMainProductItemId} - {self.RiskId.RiskName if self.RiskId else 'N/A'}"


class Policy_Main_Product_Item_Question(models.Model):
    """Policy Product Item Question model for policy product item questions with answers"""
    PolicyMainProductItemQuestionId = models.AutoField(primary_key=True)
    PolicyMainProductItemId = models.ForeignKey(
        Policy_Main_Product_Item,
        on_delete=models.PROTECT,
        db_column='PolicyMainProductItemId',
        related_name='item_questions'
    )
    ItemQuestionId = models.ForeignKey(
        Ref_Item_Question,
        on_delete=models.PROTECT,
        db_column='ItemQuestionId',
        related_name='policy_product_item_questions'
    )
    Answer = models.CharField(max_length=300, null=True, blank=True)

    class Meta:
        db_table = 'ins_policy_main_product_item_question'
        verbose_name = 'Policy Product Item Question'
        verbose_name_plural = 'Policy Product Item Questions'

    def __str__(self):
        return f"{self.PolicyMainProductItemId} - {self.ItemQuestionId.ItemQuestionName if self.ItemQuestionId else 'N/A'}"