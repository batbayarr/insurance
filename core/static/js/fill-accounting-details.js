/**
 * Generic FillAccountingDetails Function
 * Can be used across inventory, asset, and cash documents
 * 
 * @param {Object} config - Configuration object
 * @param {string} config.documentDataId - ID of the script tag containing document data
 * @param {string} config.firstTableId - ID of the first table (items/details)
 * @param {string} config.secondTableId - ID of the second table (accounting details)
 * @param {Array<number>} config.documentTypes - Array of document types that support VAT logic
 * @param {string} config.debugPrefix - Prefix for debug logging
 * @param {Function} config.addDetailRowFunction - Function to add detail rows (must be defined in each template)
 * @param {Function} config.updateBalanceDisplayFunction - Function to update balance display (must be defined in each template)
 */
function FillAccountingDetailsGeneric(config) {
    console.log('=== FillAccountingDetailsGeneric STARTED ===');
    console.log('Config:', config);
    
    const {
        documentDataId = 'document-data',
        firstTableId = 'details-tbody',
        secondTableId = 'details-accounting-tbody',
        documentTypes = [5, 6, 10, 11],
        debugPrefix = 'FillAccountingDetails',
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

    // Get document data
    const documentDataElement = document.getElementById(documentDataId);
    if (!documentDataElement) {
        console.error(`${debugPrefix}: Document data element '${documentDataId}' not found`);
        return;
    }

    const docData = JSON.parse(documentDataElement.textContent);
    
    // Step 1: Calculate TotalCost and TotalPrice from first table
    let totalCost = 0;
    let totalPrice = 0;
    
    const firstTable = document.getElementById(firstTableId);
    if (firstTable) {
        console.log(`${debugPrefix}: Calculating totals from first table...`);
        firstTable.querySelectorAll('tr').forEach((row, index) => {
            // Prefer already-computed displays to avoid drift with formatting/rounding
            const totalCostDisplayEl = row.querySelector('.total-cost-display');
            const totalPriceDisplayEl = row.querySelector('.total-price-display');
            
            let rowCost = parseFloat(totalCostDisplayEl?.value ?? totalCostDisplayEl?.textContent ?? '0') || 0;
            let rowPrice = parseFloat(totalPriceDisplayEl?.value ?? totalPriceDisplayEl?.textContent ?? '0') || 0;
            
            // Fallback: compute from qty * unit values if displays are missing
            if (!rowCost || !rowPrice) {
                const quantity = parseFloat(row.querySelector('.quantity-input')?.value || 0);
                const unitCost = parseFloat(row.querySelector('.unit-cost-input')?.value || 0);
                const unitPrice = parseFloat(row.querySelector('.unit-price-input')?.value || 0);
                if (!rowCost) rowCost = quantity * unitCost;
                if (!rowPrice) rowPrice = quantity * unitPrice;
                console.log(`Row ${index + 1} fallback compute: Qty=${quantity}, UnitCost=${unitCost}, UnitPrice=${unitPrice}`);
            }
            
            totalCost += rowCost;
            totalPrice += rowPrice;
            
            console.log(`Row ${index + 1}: RowCost=${rowCost}, RowPrice=${rowPrice}`);
        });
    }
    
    console.log(`${debugPrefix}: Calculated totals - TotalCost: ${totalCost}, TotalPrice: ${totalPrice}`);
    
    // Step 2: Calculate VAT amount using context processor rate
    const vatRate = parseFloat(docData.VatPercent) || 0;
    console.log(`${debugPrefix}: VAT Rate from docData.VatPercent:`, docData.VatPercent, 'Parsed:', vatRate);
    
    // Only apply VAT when IsVat is true; choose basis by document type
    // Asset documents (6, 11) use totalPrice, Inventory documents (5, 10) use totalCost
    const vatBasis = [6, 11].includes(docData.DocumentTypeId) ? totalPrice : totalCost;
    const vatAmount = docData.IsVat ? (vatBasis * vatRate) / 100 : 0;
    
    console.log(`${debugPrefix}: VAT Amount calculated:`, vatAmount, 'for document type:', docData.DocumentTypeId);
    
    // Step 3: Clear all rows from second table
    const detailsTbody = document.getElementById(secondTableId);
    if (!detailsTbody) {
        console.error(`${debugPrefix}: Second table '${secondTableId}' not found`);
        return;
    }
    detailsTbody.innerHTML = '';
    
    // Step 4: Check if template exists
    if (!docData.TemplateId || !docData.template_details || docData.template_details.length === 0) {
        console.log(`${debugPrefix}: No template selected or no template details available`);
        console.log('TemplateId:', docData.TemplateId);
        console.log('template_details:', docData.template_details);
        return;
    }
    
    console.log(`${debugPrefix}: Template found with ${docData.template_details.length} details`);
    console.log('First template detail:', docData.template_details[0]);
    
    // Step 5: Create rows from template details
    let rowCounter = 1;
    
    // Debug logging
    console.log(`${debugPrefix} Debug:`);
    console.log('DocumentTypeId:', docData.DocumentTypeId);
    console.log('IsVat:', docData.IsVat);
    console.log('AccountId:', docData.AccountId);
    console.log('VatAccountId:', docData.VatAccountId);
    console.log('TotalCost:', totalCost);
    console.log('TotalPrice:', totalPrice);
    console.log('VatRate:', vatRate);
    console.log('VatAmount:', vatAmount);
    
    console.log(`${debugPrefix}: Processing ${docData.template_details.length} template details...`);
    
    docData.template_details.forEach((templateDetail, index) => {
        // Determine CurrencyAmount based on rules
        let currencyAmount = 0;
        
        console.log(`Processing template detail ${index + 1}:`, {
            AccountId: templateDetail.AccountId,
            IsDebit: templateDetail.IsDebit,
            AccountCode: templateDetail.AccountCode,
            AccountName: templateDetail.AccountName,
            AccountTypeId: templateDetail.AccountTypeId
        });
        
        // Check if AccountTypeId exists
        if (!templateDetail.AccountTypeId) {
            console.warn(`Template detail ${index + 1} missing AccountTypeId, using fallback logic`);
        }
        
        // Apply logic based on document type
        // Asset documents (6, 11) use asset logic, Inventory documents (5, 10) use inventory logic
        if ([6, 11].includes(docData.DocumentTypeId)) {
            // Asset document logic
            const accountTypeId = templateDetail.AccountTypeId;
            
            console.log('Processing asset document:', {
                DocumentTypeId: docData.DocumentTypeId,
                AccountTypeId: accountTypeId,
                IsVat: docData.IsVat
            });
            
            if (!docData.IsVat) {
                // IsVat = false rules
                if ([3, 5, 42, 43].includes(accountTypeId) || 
                    (accountTypeId >= 69 && accountTypeId <= 77)) {
                    currencyAmount = totalPrice;
                    console.log(`Rule: IsVat=false, AccountTypeId=${accountTypeId}, CurrencyAmount=TotalPrice (${currencyAmount})`);
                } else if (accountTypeId === 92 || [8, 9, 11].includes(accountTypeId)) {
                    currencyAmount = totalCost;
                    console.log(`Rule: IsVat=false, AccountTypeId=${accountTypeId}, CurrencyAmount=TotalCost (${currencyAmount})`);
                }
            } else {
                // IsVat = true rules
                if ([3, 5, 42, 43].includes(accountTypeId)) {
                    currencyAmount = totalPrice + vatAmount;
                    console.log(`Rule: IsVat=true, AccountTypeId=${accountTypeId}, CurrencyAmount=TotalPrice+VatAmount (${currencyAmount})`);
                } else if (accountTypeId >= 69 && accountTypeId <= 77) {
                    currencyAmount = totalPrice;
                    console.log(`Rule: IsVat=true, AccountTypeId=${accountTypeId}, CurrencyAmount=TotalPrice (${currencyAmount})`);
                } else if ([6, 47].includes(accountTypeId)) {
                    currencyAmount = vatAmount;
                    console.log(`Rule: IsVat=true, AccountTypeId=${accountTypeId}, CurrencyAmount=VatAmount (${currencyAmount})`);
                } else if (accountTypeId === 92 || [8, 9, 11].includes(accountTypeId)) {
                    currencyAmount = totalCost;
                    console.log(`Rule: IsVat=true, AccountTypeId=${accountTypeId}, CurrencyAmount=TotalCost (${currencyAmount})`);
                }
            }
        } else if ([5, 10].includes(docData.DocumentTypeId)) {
            // Inventory document logic (existing, unchanged)
            if (!docData.IsVat) {
                // Rule: IsVat=false -> CurrencyAmount=TotalCost for all rows
                currencyAmount = totalCost;
                console.log('Rule: IsVat=false, CurrencyAmount =', currencyAmount);
            } else {
                // Rule: IsVat=true
                if (templateDetail.IsDebit) {
                    if (templateDetail.AccountId === docData.VatAccountId) {
                        // IsDebit=true and accountid=VatAccountId -> CurrencyAmount=VatAmount
                        currencyAmount = vatAmount;
                        console.log('Rule: VAT Account match, CurrencyAmount =', currencyAmount);
                    } else if (templateDetail.AccountId === docData.AccountId) {
                        // IsDebit=true and accountid=AccountId -> CurrencyAmount=TotalCost
                        currencyAmount = totalCost;
                        console.log('Rule: Main Account match, CurrencyAmount =', currencyAmount);
                    }
                } else {
                    // IsDebit=false
                    if (templateDetail.AccountId !== docData.AccountId && 
                        templateDetail.AccountId !== docData.VatAccountId) {
                        // accountid <> AccountId and accountid <> VatAccountId -> CurrencyAmount=TotalCost+VatAmount
                        currencyAmount = totalCost + vatAmount;
                        console.log('Rule: Other Account, CurrencyAmount =', currencyAmount);
                    }
                }
            }
        } else {
            // For non-specified document types, use total cost
            currencyAmount = totalCost;
            console.log('Rule: Non-specified document type, CurrencyAmount =', currencyAmount);
        }
        
        // Fallback: If currencyAmount is still 0 and we have data, use a default calculation
        if (currencyAmount === 0 && (totalCost > 0 || totalPrice > 0)) {
            console.warn('CurrencyAmount is 0, applying fallback calculation');
            if (templateDetail.IsDebit) {
                currencyAmount = totalCost; // Use total cost for debit entries
            } else {
                currencyAmount = totalCost; // Use total cost for credit entries too
            }
            console.log('Fallback CurrencyAmount =', currencyAmount);
        }
        
        // Final fallback: If still 0, use a simple distribution
        if (currencyAmount === 0) {
            console.warn('CurrencyAmount still 0, using simple distribution');
            currencyAmount = totalCost / docData.template_details.length;
            console.log('Simple distribution CurrencyAmount =', currencyAmount);
        }
        
        console.log('Final CurrencyAmount for row:', currencyAmount);
        
        // Ensure currencyAmount is a valid number
        if (isNaN(currencyAmount) || currencyAmount === null || currencyAmount === undefined) {
            console.warn('Invalid currencyAmount detected, setting to 0:', currencyAmount);
            currencyAmount = 0;
        }
        
        // Create new row using the provided function
        const rowData = {
            accountId: templateDetail.AccountId,
            accountDisplay: templateDetail.AccountCode + ' - ' + templateDetail.AccountName,
            clientId: docData.ClientId,
            clientDisplay: docData.ClientCode + ' - ' + docData.ClientName,
            documentId: docData.DocumentId,
            currencyId: 1,
            currencyExchange: 1,
            currencyAmount: currencyAmount.toFixed(6),
            isDebit: templateDetail.IsDebit,
            rowId: `auto_${rowCounter++}`
        };
        
        console.log('Calling addDetailRowFunction with data:', rowData);
        
        // Validate the function exists and call it
        if (typeof addDetailRowFunction === 'function') {
            addDetailRowFunction(rowData);
            console.log('addDetailRowFunction called successfully');
        } else {
            console.error('addDetailRowFunction is not a function:', typeof addDetailRowFunction);
        }
    });
    
    // Step 6: Calculate and display total debit and credit amounts
    console.log(`${debugPrefix}: Calling updateBalanceDisplayFunction...`);
    if (typeof updateBalanceDisplayFunction === 'function') {
        updateBalanceDisplayFunction();
        console.log(`${debugPrefix}: updateBalanceDisplayFunction called successfully`);
    } else {
        console.error('updateBalanceDisplayFunction is not a function:', typeof updateBalanceDisplayFunction);
    }
    
    // Log the totals for debugging
    console.log(`${debugPrefix} completed - totals updated`);
}

/**
 * Helper function to create event listeners for FillAccountingDetails
 * @param {Object} config - Same configuration object as FillAccountingDetails
 */
function setupFillAccountingDetailsListeners(config) {
    const {
        firstTableId = 'details-tbody',
        debugPrefix = 'FillAccountingDetails'
    } = config;

    // Attach event listeners to trigger FillAccountingDetails
    const firstTable = document.getElementById(firstTableId);
    if (firstTable) {
        firstTable.addEventListener('input', function(e) {
            if (e.target.matches('.quantity-input, .unit-cost-input, .unit-price-input')) {
                // Call the local FillAccountingDetails function instead of generic
                if (typeof window.FillAccountingDetails === 'function') {
                    window.FillAccountingDetails();
                } else {
                    console.error('Local FillAccountingDetails function not found');
                }
            }
        });

        firstTable.addEventListener('change', function(e) {
            if (e.target.matches('[name^="inventory_id_"]')) {
                // Call the local FillAccountingDetails function instead of generic
                if (typeof window.FillAccountingDetails === 'function') {
                    window.FillAccountingDetails();
                } else {
                    console.error('Local FillAccountingDetails function not found');
                }
            }
        });
    }
}
