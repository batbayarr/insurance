/**
 * Generic FillAccountingDetails Function for Cash Documents
 * Can be used across cash documents
 * Version: 2024-01-16 - Added flexible VAT account detection
 * 
 * @param {Object} config - Configuration object
 * @param {string} config.documentDataId - ID of the script tag containing document data
 * @param {string} config.firstTableId - ID of the first table (cash details)
 * @param {string} config.secondTableId - ID of the second table (accounting details) - same as first for cash
 * @param {Array<number>} config.documentTypes - Array of document types that support VAT logic
 * @param {string} config.debugPrefix - Prefix for debug logging
 * @param {Function} config.addDetailRowFunction - Function to add detail rows (must be defined in each template)
 * @param {Function} config.updateBalanceDisplayFunction - Function to update balance display (must be defined in each template)
 */

// Global state shared between template scripts and this helper so we know
// when auto-fill is running vs when the user is manually editing rows.
window.cashAutoFillState = window.cashAutoFillState || {
    isRunning: false,
    manualEditing: false
};
function FillAccountingDetailsCashGeneric(config) {
    const {
        documentDataId = 'document-data',
        firstTableId = 'details-tbody',
        secondTableId = 'details-tbody', // Cash documents use the same table
        documentTypes = [1, 2, 3, 4, 15, 16, 17, 18], // Cash document types
        debugPrefix = 'FillAccountingDetailsCash',
        addDetailRowFunction = null,
        updateBalanceDisplayFunction = null
    } = config;

    // Validate required functions
    if (!addDetailRowFunction) {
        console.error(`${debugPrefix}: addDetailRowFunction is required`);
        return;
    }
    
    if (!updateBalanceDisplayFunction) {
        console.error(`${debugPrefix}: updateBalanceDisplayFunction is required`);
        return;
    }
    
    console.log(`${debugPrefix}: Starting FillAccountingDetailsCashGeneric - Version 2024-01-16`);
    console.log(`${debugPrefix}: Config received:`, config);
    
    // Get document data
    const documentDataElement = document.getElementById(documentDataId);
    if (!documentDataElement) {
        console.error(`${debugPrefix}: Document data element '${documentDataId}' not found`);
        return;
    }

    const docData = JSON.parse(documentDataElement.textContent);
    
    // Check CurrencyId - only allow automatic filling for MNT (CurrencyId = 1)
    if (docData.CurrencyId && docData.CurrencyId > 1) {
        console.log(`${debugPrefix}: CurrencyId is ${docData.CurrencyId} (> 1), skipping automatic fill. Manual row management allowed.`);
        return;
    }
    
    // Step 1: Get TotalAmount from cash_document master table
    // Ensure proper precision handling for CurrencyAmount (24,6) and CurrencyExchange (10,2)
    const currencyAmount = parseFloat(docData.CurrencyAmount);
    const currencyExchange = parseFloat(docData.CurrencyExchange);
    const totalAmount = parseFloat((currencyAmount * currencyExchange).toFixed(6));
    
    // Step 2: Use VatAmount from form, calculate NetAmount (no VAT percentage calculation in generic JS)
    const vatAmount = parseFloat(docData.VatAmount) || 0; // Use form's VatAmount
    const netAmount = parseFloat((totalAmount - vatAmount).toFixed(6)); // Simple calculation: TotalAmount - VatAmount
    
    console.log('Using VatAmount from form, calculating NetAmount:');
    console.log('  CurrencyAmount (24,6):', currencyAmount, 'Type:', typeof currencyAmount);
    console.log('  CurrencyExchange (10,2):', currencyExchange, 'Type:', typeof currencyExchange);
    console.log('  TotalAmount (calculated):', totalAmount, 'Type:', typeof totalAmount);
    console.log('  VatAmount (from form):', vatAmount, 'Type:', typeof vatAmount);
    console.log('  NetAmount (calculated):', netAmount, 'Type:', typeof netAmount);
    console.log('  Raw VatAmount from docData:', docData.VatAmount, 'Type:', typeof docData.VatAmount);
    console.log('  DebugInfo from template:', docData.DebugInfo);
    console.log('  Expected VAT calculation: Total=990, VAT%=10, VAT Amount should be 90, Net Amount should be 900');
    
    // Step 3: Clear all rows from second table
    const detailsTbody = document.getElementById(secondTableId);
    if (!detailsTbody) {
        console.error(`${debugPrefix}: Second table '${secondTableId}' not found`);
        return;
    }
    
    // Check if there are existing detail rows before clearing
    // IMPORTANT: Only count rows with VALID numeric data-detail-id (actual saved records)
    // Temporary rows (created by view when no details exist) have empty/None data-detail-id
    const allRows = detailsTbody.querySelectorAll('tr');
    const existingRows = Array.from(allRows).filter(row => {
        // Get data-detail-id attribute value
        const detailId = row.getAttribute('data-detail-id');
        
        // Check if it's a valid numeric ID (not empty, not None, not undefined, is a number)
        const hasValidDetailId = detailId !== null && 
                                 detailId !== '' && 
                                 detailId !== 'undefined' && 
                                 detailId !== 'None' &&
                                 !isNaN(parseInt(detailId)) && // Must be a valid number
                                 parseInt(detailId) > 0; // Must be positive
        
        const isDeleted = row.classList.contains('deleted-row') || row.style.display === 'none';
        const isNewRow = row.classList.contains('new-row');
        
        // Only count as existing if it has a VALID detail ID (saved record) AND is not deleted AND is not new
        // Temporary rows won't have valid detail IDs, so they won't be counted
        const isValidExisting = hasValidDetailId && !isDeleted && !isNewRow;
        
        if (isValidExisting) {
            console.log(`${debugPrefix}: Found existing row with valid detail ID:`, detailId);
        } else if (row.classList.contains('existing-row') && !hasValidDetailId) {
            console.log(`${debugPrefix}: Found temporary row (existing-row class but no valid detail ID):`, detailId);
        }
        
        return isValidExisting;
    });
    
    console.log(`${debugPrefix}: Checking for existing rows - Total <tr> elements: ${allRows.length}, Valid existing rows (with detail ID): ${existingRows.length}`);
    
    if (existingRows.length > 0) {
        console.warn(`${debugPrefix}: Existing detail rows found (${existingRows.length} rows). Skipping auto-population to preserve existing data.`);
        return;
    }
    
    // Clear tbody - safe to do even if empty
    detailsTbody.innerHTML = '';
    console.log(`${debugPrefix}: Cleared tbody, ready to populate with template data`);
    
    // Step 4: Check if template exists
    console.log(`${debugPrefix}: Template check - TemplateId:`, docData.TemplateId, 'template_details:', docData.template_details);
    if (!docData.TemplateId || !docData.template_details || docData.template_details.length === 0) {
        console.log(`${debugPrefix}: No template selected or no template details available`);
        return;
    }
    
    // Step 5: Create rows from template details
    let rowCounter = 1;
    
    // Debug logging
    console.log(`${debugPrefix} Debug:`);
    console.log('DocumentTypeId:', docData.DocumentTypeId);
    console.log('IsVat:', docData.IsVat);
    console.log('AccountId:', docData.AccountId);
    console.log('VatAccountId:', docData.VatAccountId);
    console.log('TotalAmount:', totalAmount);
    console.log('NetAmount:', netAmount);
    console.log('VatPercent:', docData.VatPercent);
    console.log('VatAmount:', vatAmount);
    console.log('Template details count:', docData.template_details.length);
    console.log('Template details:', docData.template_details);
    
    // Check if addDetailRowFunction is available
    if (typeof addDetailRowFunction !== 'function') {
        console.error('addDetailRowFunction is not available!');
        return;
    }
    
    console.log('Starting to process', docData.template_details.length, 'template details');
    
    docData.template_details.forEach((templateDetail, index) => {
        console.log(`Processing template detail ${index + 1}/${docData.template_details.length}:`, templateDetail);
        console.log(`Template detail ${index + 1} raw data:`, JSON.stringify(templateDetail));
        // Determine CurrencyAmount and CashFlowId based on rules
        let currencyAmount = 0;
        let cashFlowId = null;
        
        console.log('Processing template detail:', {
            AccountId: templateDetail.AccountId,
            IsDebit: templateDetail.IsDebit,
            AccountCode: templateDetail.AccountCode,
            VatAccountId: docData.VatAccountId,
            DocumentTypeId: docData.DocumentTypeId,
            IsVat: docData.IsVat,
            AccountIdType: typeof templateDetail.AccountId,
            VatAccountIdType: typeof docData.VatAccountId,
            AccountIdEqualsVatAccountId: templateDetail.AccountId == docData.VatAccountId,
            AccountIdStrictEqualsVatAccountId: templateDetail.AccountId === docData.VatAccountId
        });
        
        // Use CashFlowId from template_detail (more flexible approach)
        cashFlowId = templateDetail.CashFlowId;
        console.log(`CashFlowId from template_detail:`, cashFlowId, 'Type:', typeof cashFlowId);
        
        // Apply VAT logic for document types 1, 2, 3, 4, 15, 16
        if ([1, 3, 15, 18].includes(docData.DocumentTypeId)) {
            // Document Types 1, 3, 15 (Income Documents - Payable VAT)
            if (!docData.IsVat) {
                // Case 1: IsVat=false -> CurrencyAmount=TotalAmount for all rows
                currencyAmount = totalAmount;
                console.log('Rule: Type 1/3/15, IsVat=false, CurrencyAmount =', currencyAmount, 'CashFlowId =', cashFlowId);
            } else {
                // IsVat=true
                if (templateDetail.IsDebit) {
                    // IsDebit=true
                    // Check if this template detail is a VAT account by comparing AccountId with document's VatAccountId
                    const isVatAccount = (parseInt(templateDetail.AccountId) === parseInt(docData.VatAccountId));
                    
                    console.log('VAT Account Check (Type 1/3/15, Debit):', {
                        isVatAccount: isVatAccount,
                        templateAccountId: parseInt(templateDetail.AccountId),
                        vatAccountId: parseInt(docData.VatAccountId)
                    });
                    
                    if (isVatAccount) {
                        // Case 3: IsDebit=true and accountid=VatAccountId -> CurrencyAmount=VatAmount
                        currencyAmount = vatAmount;
                        console.log('Rule: Type 1/3/15, IsVat=true, Debit, VAT Account Match, CurrencyAmount =', currencyAmount, 'CashFlowId =', cashFlowId);
                    } else if (templateDetail.AccountId === docData.AccountId) {
                        // Case 2: IsDebit=true and accountid=AccountId -> CurrencyAmount=TotalAmount
                        currencyAmount = totalAmount;
                        console.log('Rule: Type 1/3/15, IsVat=true, Debit, Main Account, CurrencyAmount =', currencyAmount, 'CashFlowId =', cashFlowId);
                    } else {
                        // Case 4: IsDebit=true and accountid<>VatAccountId and accountid<>AccountId -> CurrencyAmount=NetAmount
                        currencyAmount = netAmount;
                        console.log('Rule: Type 1/3/15, IsVat=true, Debit, Other Account, CurrencyAmount =', currencyAmount, 'CashFlowId =', cashFlowId);
                    }
                } else {
                    // IsDebit=false (Credit)
                    // Check if this template detail is a VAT account by comparing AccountId with document's VatAccountId
                    const isVatAccount = (parseInt(templateDetail.AccountId) === parseInt(docData.VatAccountId));
                    
                    console.log('VAT Account Check (Type 1/3/15, Credit):', {
                        isVatAccount: isVatAccount,
                        templateAccountId: parseInt(templateDetail.AccountId),
                        vatAccountId: parseInt(docData.VatAccountId)
                    });
                    
                    if (isVatAccount) {
                        // VAT account (Credit) -> CurrencyAmount=VatAmount
                        currencyAmount = vatAmount;
                        console.log('Rule: Type 1/3/15, IsVat=true, Credit, VAT Account, CurrencyAmount =', currencyAmount, 'CashFlowId =', cashFlowId);
                    } else if (templateDetail.AccountId === docData.AccountId) {
                        // Main account (Credit) -> CurrencyAmount=TotalAmount
                        currencyAmount = totalAmount;
                        console.log('Rule: Type 1/3/15, IsVat=true, Credit, Main Account, CurrencyAmount =', currencyAmount, 'CashFlowId =', cashFlowId);
                    } else {
                        // Other account (Credit) -> CurrencyAmount=NetAmount
                        currencyAmount = netAmount;
                        console.log('Rule: Type 1/3/15, IsVat=true, Credit, Other Account, CurrencyAmount =', currencyAmount, 'CashFlowId =', cashFlowId);
                    }
                }
            }
        } else if ([2, 4, 16, 17].includes(docData.DocumentTypeId)) {
            // Document Types 2, 4, 16 (Expense Documents - Receivable VAT)
            if (!docData.IsVat) {
                // Case 1: IsVat=false -> CurrencyAmount=TotalAmount for all rows
                currencyAmount = totalAmount;
                console.log('Rule: Type 2/4/16, IsVat=false, CurrencyAmount =', currencyAmount, 'CashFlowId =', cashFlowId);
            } else {
                // IsVat=true
                if (templateDetail.IsDebit) {
                    // IsDebit=true
                    // Check if this template detail is a VAT account by comparing AccountId with document's VatAccountId
                    const isVatAccount = (parseInt(templateDetail.AccountId) === parseInt(docData.VatAccountId));
                    const isVatAccountMatch = isVatAccount; // Same as isVatAccount since we're comparing the right fields
                    
                    console.log('VAT Account Check (Type 2/4/16):', {
                        isVatAccount: isVatAccount,
                        isVatAccountMatch: isVatAccountMatch,
                        templateAccountId: parseInt(templateDetail.AccountId),
                        vatAccountId: parseInt(docData.VatAccountId)
                    });
                    
                    if (isVatAccount && isVatAccountMatch) {
                        // Case 3: accountid=VatAccountId -> CurrencyAmount=VatAmount
                        currencyAmount = vatAmount;
                        console.log('Rule: Type 2/4/16, IsVat=true, Debit, VAT Account Match, CurrencyAmount =', currencyAmount, 'CashFlowId =', cashFlowId);
                    } else if (isVatAccount && !isVatAccountMatch) {
                        // Case 3b: VAT account but different ID -> CurrencyAmount=VatAmount (flexible approach)
                        currencyAmount = vatAmount;
                        console.log('Rule: Type 2/4/16, IsVat=true, Debit, VAT Account (flexible), CurrencyAmount =', currencyAmount, 'CashFlowId =', cashFlowId);
                    } else {
                        // Case 4: accountid<>VatAccountId -> CurrencyAmount=NetAmount
                        currencyAmount = netAmount;
                        console.log('Rule: Type 2/4/16, IsVat=true, Debit, Other Account, CurrencyAmount =', currencyAmount, 'CashFlowId =', cashFlowId);
                    }
                } else {
                    // IsDebit=false
                    if (templateDetail.AccountId === docData.AccountId) {
                        // Case 2: accountid=AccountId -> CurrencyAmount=TotalAmount
                        currencyAmount = totalAmount;
                        console.log('Rule: Type 2/4/16, IsVat=true, Credit, Main Account, CurrencyAmount =', currencyAmount, 'CashFlowId =', cashFlowId);
                    }
                }
            }
        } else {
            // For other document types, use total amount
            currencyAmount = totalAmount;
            console.log('Rule: Other document type, CurrencyAmount =', currencyAmount, 'CashFlowId =', cashFlowId);
        }
        
        // Convert currencyAmount based on CurrencyId and currencyExchange
        // If document currency is foreign currency (not MNT), convert from MNT back to foreign currency
        // BUT: Only convert if this row will use foreign currency (main account row)
        // Rows forced to MNT by bulkAdjustRows should keep currencyAmount in MNT
        const isForeignCurrency = docData.CurrencyId !== 1; // Assuming 1 is MNT
        const isMainAccount = parseInt(templateDetail.AccountId) === parseInt(docData.AccountId);
        
        // Only convert if document is foreign currency AND this is the main account row (will use foreign currency)
        // Other rows will be forced to MNT by bulkAdjustRows, so they should keep MNT amount
        if (isForeignCurrency && isMainAccount && currencyExchange > 0 && currencyAmount > 0) {
            // Store original MNT amount before conversion
            const originalMNTAmount = currencyAmount;
            // Convert from MNT equivalent back to foreign currency
            currencyAmount = currencyAmount / currencyExchange;
            console.log('Currency conversion applied (main account row):', {
                originalMNT: originalMNTAmount,
                convertedAmount: currencyAmount,
                currencyId: docData.CurrencyId,
                currencyExchange: currencyExchange
            });
        } else if (isForeignCurrency && !isMainAccount) {
            // Non-main account rows will be forced to MNT, so keep currencyAmount in MNT (no conversion)
            console.log('Currency conversion skipped (will be forced to MNT):', {
                currencyAmount: currencyAmount,
                accountId: templateDetail.AccountId,
                mainAccountId: docData.AccountId
            });
        }
        
        // Ensure currency amount has proper precision (6 decimal places)
        const finalCurrencyAmount = typeof currencyAmount === 'number' ? parseFloat(currencyAmount.toFixed(6)) : 0;
        console.log('Final CurrencyAmount for row:', finalCurrencyAmount, 'Type:', typeof finalCurrencyAmount, 'CashFlowId:', cashFlowId, 'Type:', typeof cashFlowId);
        
        // Determine currency exchange rate for this row
        // Non-main account rows will be forced to MNT, so use exchange=1.0
        const rowCurrencyExchange = isForeignCurrency && !isMainAccount ? 1.0 : docData.CurrencyExchange;
        const rowCurrencyId = isForeignCurrency && !isMainAccount ? 1 : docData.CurrencyId; // MNT for forced rows
        
        // Create new row using the provided function
        console.log(`${debugPrefix}: Creating row ${rowCounter} for template detail:`, templateDetail.AccountCode);
        try {
            addDetailRowFunction({
                accountId: templateDetail.AccountId,
                accountDisplay: templateDetail.AccountCode + ' - ' + templateDetail.AccountName,
                clientId: docData.ClientId,
                clientDisplay: docData.ClientCode + ' - ' + docData.ClientName,
                documentId: docData.DocumentId,
                currencyId: rowCurrencyId,
                currencyExchange: rowCurrencyExchange,
                currencyAmount: finalCurrencyAmount.toFixed(6),
                isDebit: templateDetail.IsDebit,
                cashFlowId: cashFlowId,
                rowId: `auto_${rowCounter++}`
            });
            console.log(`${debugPrefix}: Row ${rowCounter - 1} created successfully`);
        } catch (error) {
            console.error(`${debugPrefix}: Error creating row:`, error);
        }
    });
    
    console.log(`${debugPrefix}: Finished processing ${docData.template_details.length} template details`);
    
    // Step 6: Calculate and display total debit and credit amounts
    updateBalanceDisplayFunction();
    
    // Log the totals for debugging
    console.log(`${debugPrefix} completed - totals updated`);
}

/**
 * Helper function to create event listeners for FillAccountingDetailsCash
 * @param {Object} config - Same configuration object as FillAccountingDetailsCash
 */
function setupFillAccountingDetailsCashListeners(config) {
    const {
        firstTableId = 'details-tbody',
        debugPrefix = 'FillAccountingDetailsCash'
    } = config;

    const firstTable = document.getElementById(firstTableId);
    if (!firstTable) {
        console.warn(`${debugPrefix}: first table '${firstTableId}' not found for listener setup`);
        return;
    }

    const guardAutoFill = (callback) => {
        return function guardedHandler(event) {
            const state = window.cashAutoFillState || {};
            if (state.isRunning || state.manualEditing) {
                return;
            }
            callback(event);
        };
    };

    const triggerFill = () => {
        if (typeof window.FillAccountingDetails === 'function') {
            window.FillAccountingDetails();
        } else {
            console.error('Local FillAccountingDetails function not found');
        }
    };

    const inputHandler = guardAutoFill((e) => {
        if (e.target.matches('input[name*="currency_amount"], input[name*="currency_exchange"]')) {
            triggerFill();
        }
    });

    const changeHandler = guardAutoFill((e) => {
        if (e.target.matches('select[name*="currency_id"]')) {
            triggerFill();
        }
    });

    firstTable.addEventListener('input', inputHandler);
    firstTable.addEventListener('change', changeHandler);

    // expose a reset utility so templates can re-enable auto-fill if needed
    window.resetCashAutoFillState = function resetCashAutoFillState() {
        window.cashAutoFillState = window.cashAutoFillState || {};
        window.cashAutoFillState.manualEditing = false;
    };
}

// Make the function available globally
window.FillAccountingDetailsCashGeneric = FillAccountingDetailsCashGeneric;
