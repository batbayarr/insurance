# Generic FillAccountingDetails Function

This document explains how to use the generic `FillAccountingDetails` function across different document types (inventory, asset, cash).

## Overview

The `FillAccountingDetails` function automatically populates accounting details based on:
- Document items (first table)
- Template configuration
- VAT calculations
- Document type-specific business rules

## Usage

### 1. Include the Script

Add the generic function to your template:

```html
<!-- Include generic FillAccountingDetails function -->
<script src="{% static 'js/fill-accounting-details.js' %}"></script>
```

### 2. Define Required Helper Functions

Each template must define these functions:

```javascript
// Function to add a detail row to the accounting table
function addDetailRow(data) {
    const detailsTbody = document.getElementById('details-accounting-tbody');
    const newRow = document.createElement('tr');
    // ... implement row creation logic
    detailsTbody.appendChild(newRow);
    addEventListenersToDetailRow(newRow);
}

// Function to update balance display
function updateBalanceDisplay() {
    // ... implement balance calculation and display
}
```

### 3. Create Document Data Script

Include document data in a JSON script tag:

```html
<script id="document-data" type="application/json">
{
    "DocumentId": {{ document.DocumentId }},
    "DocumentTypeId": {{ document.DocumentTypeId.DocumentTypeId }},
    "AccountId": {{ document.AccountId.AccountId }},
    "TemplateId": {{ document.TemplateId.TemplateId }},
    "IsVat": {% if document.IsVat %}true{% else %}false{% endif %},
    "ClientId": {{ document.ClientId.ClientId }},
    "VatAccountId": {{ document.VatAccountId.AccountId }},
    "VatPercent": {{ VAT_RATE_PERCENT }},
    "template_details": [
        {% for td in template_details %}
        {
            "AccountId": {{ td.AccountId.AccountId }},
            "AccountCode": "{{ td.AccountId.AccountCode }}",
            "AccountName": "{{ td.AccountId.AccountName }}",
            "IsDebit": {% if td.IsDebit %}true{% else %}false{% endif %}
        }{% if not forloop.last %},{% endif %}
        {% endfor %}
    ],
    "ClientCode": "{{ document.ClientId.ClientCode }}",
    "ClientName": "{{ document.ClientId.ClientName }}"
}
</script>
```

### 4. Implement Document-Specific Function

Create a wrapper function that calls the generic function:

```javascript
// Document-specific FillAccountingDetails function
function FillAccountingDetails() {
    window.FillAccountingDetails({
        documentDataId: 'document-data',
        firstTableId: 'details-tbody',
        secondTableId: 'details-accounting-tbody',
        documentTypes: [5, 10], // Document types that support VAT logic
        debugPrefix: 'Inventory',
        addDetailRowFunction: addDetailRow,
        updateBalanceDisplayFunction: updateBalanceDisplay
    });
}
```

### 5. Setup Event Listeners

Use the generic setup function:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Setup event listeners using generic function
    setupFillAccountingDetailsListeners({
        documentDataId: 'document-data',
        firstTableId: 'details-tbody',
        secondTableId: 'details-accounting-tbody',
        documentTypes: [5, 10],
        debugPrefix: 'Inventory'
    });
});
```

## Configuration Options

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `documentDataId` | ID of script tag containing document data | `'document-data'` | `'asset-document-data'` |
| `firstTableId` | ID of first table (items/details) | `'details-tbody'` | `'asset-details-tbody'` |
| `secondTableId` | ID of second table (accounting) | `'details-accounting-tbody'` | `'asset-accounting-tbody'` |
| `documentTypes` | Array of document types supporting VAT | `[5, 10]` | `[3, 7]` for assets |
| `debugPrefix` | Prefix for debug logging | `'FillAccountingDetails'` | `'Asset'` |
| `addDetailRowFunction` | Function to add detail rows | Required | `addDetailRow` |
| `updateBalanceDisplayFunction` | Function to update balance | Required | `updateBalanceDisplay` |

## Document Type Examples

### Inventory Documents
```javascript
// Document types: 5, 10 (Invoice, Credit Note)
FillAccountingDetails({
    documentDataId: 'document-data',
    firstTableId: 'details-tbody',
    secondTableId: 'details-accounting-tbody',
    documentTypes: [5, 10],
    debugPrefix: 'Inventory',
    addDetailRowFunction: addDetailRow,
    updateBalanceDisplayFunction: updateBalanceDisplay
});
```

### Asset Documents
```javascript
// Document types: 3, 7 (Asset Purchase, Asset Sale)
FillAccountingDetails({
    documentDataId: 'asset-document-data',
    firstTableId: 'asset-details-tbody',
    secondTableId: 'asset-accounting-tbody',
    documentTypes: [3, 7],
    debugPrefix: 'Asset',
    addDetailRowFunction: addAssetDetailRow,
    updateBalanceDisplayFunction: updateAssetBalanceDisplay
});
```

### Cash Documents
```javascript
// Document types: 1, 2 (Cash Receipt, Cash Payment)
FillAccountingDetails({
    documentDataId: 'cash-document-data',
    firstTableId: 'cash-details-tbody',
    secondTableId: 'cash-accounting-tbody',
    documentTypes: [1, 2],
    debugPrefix: 'Cash',
    addDetailRowFunction: addCashDetailRow,
    updateBalanceDisplayFunction: updateCashBalanceDisplay
});
```

## Business Rules

The function applies different logic based on document type and VAT settings:

### VAT Document Types (5, 10 for inventory)
- **IsVat=false**: All rows get `CurrencyAmount = TotalCost`
- **IsVat=true**: 
  - VAT Account (Debit): `CurrencyAmount = VatAmount`
  - Main Account (Debit): `CurrencyAmount = TotalCost`
  - Other Accounts (Credit): `CurrencyAmount = TotalCost + VatAmount`

### Non-VAT Document Types
- All rows get `CurrencyAmount = TotalCost`

## Benefits

1. **Code Reusability**: Same logic across all document types
2. **Consistency**: Identical VAT calculations everywhere
3. **Maintainability**: Fix bugs in one place
4. **Configurability**: Easy to customize per document type
5. **Future-Proof**: Easy to add new document types

## Migration Guide

To migrate existing `FillAccountingDetails` functions:

1. **Extract Helper Functions**: Move `addDetailRow` and `updateBalanceDisplay` to template
2. **Add Script Include**: Include the generic function
3. **Create Wrapper**: Replace existing function with wrapper
4. **Update Event Listeners**: Use `setupFillAccountingDetailsListeners`
5. **Test**: Verify functionality works correctly

## Troubleshooting

### Common Issues

1. **Function Not Found**: Ensure script is included before usage
2. **Helper Functions Missing**: Define `addDetailRow` and `updateBalanceDisplay`
3. **Wrong Table IDs**: Verify table IDs match your template
4. **Document Data Missing**: Ensure JSON script tag exists with correct ID

### Debug Logging

The function includes extensive debug logging. Check browser console for:
- Document data values
- VAT calculations
- Template detail processing
- Final currency amounts
