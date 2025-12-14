/**
 * Generic FillAccountingDetails Function
 * Tailored for asset documents (types 10 & 11)
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
        documentTypes = [10, 11],
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
    const documentTypeId = Number(docData.DocumentTypeId);

    if (documentTypeId === 11) {
        try {
            if (typeof window.calculateAllDepreciationAmounts === 'function') {
                window.calculateAllDepreciationAmounts();
            }
            if (typeof window.calculateAllEndingDepreciation === 'function') {
                window.calculateAllEndingDepreciation();
            }
            if (typeof window.updateSummaryRowTotals === 'function') {
                window.updateSummaryRowTotals();
            }
        } catch (err) {
            console.warn('Failed to refresh depreciation/summary totals before fill:', err);
        }
    }

    const getSummaryValue = (elementId) => {
        const el = document.getElementById(elementId);
        if (!el) {
            return null;
        }
        const rawText = (el.textContent ?? el.value ?? '').toString().replace(/,/g, '').trim();
        if (rawText === '') {
            return null;
        }
        const parsed = parseFloat(rawText);
        return Number.isNaN(parsed) ? null : parsed;
    };
    
    // Step 1: Calculate TotalCost, TotalPrice, and accumulated ending depreciation from first table
    let totalCost = 0;
    let totalPrice = 0;
    let totalEndingDep = 0;
    let totalDepAmount = 0;
    
    const firstTable = document.getElementById(firstTableId);
    if (firstTable) {
        console.log(`${debugPrefix}: Calculating totals from first table (ID: ${firstTableId})...`);
        const allRows = firstTable.querySelectorAll('tr');
        console.log(`${debugPrefix}: Found ${allRows.length} rows in table`);
        
        allRows.forEach((row, index) => {
            if (window.getComputedStyle(row).display === 'none') {
                return;
            }
            // Prefer already-computed displays to avoid drift with formatting/rounding
            const totalCostDisplayEl = row.querySelector('.total-cost-display');
            const totalPriceDisplayEl = row.querySelector('.total-price-display');
            
            let rowCost = 0;
            let rowPrice = 0;
            
            // Parse display values, removing thousands separators (commas) first
            if (totalCostDisplayEl) {
                const costValue = (totalCostDisplayEl.value ?? totalCostDisplayEl.textContent ?? '0').toString().replace(/,/g, '');
                rowCost = parseFloat(costValue) || 0;
            }
            
            // Fallback: compute from qty * unit values if displays are missing or zero
            if (!totalCostDisplayEl || rowCost === 0) {
                const quantity = parseFloat(row.querySelector('.quantity-input')?.value || 1); // Default to 1 for asset documents
                const unitCost = parseFloat(row.querySelector('.unit-cost-input')?.value || 0);
                if (unitCost > 0) { // Only require unitCost, quantity defaults to 1
                    rowCost = quantity * unitCost;
                    console.log(`Row ${index + 1} fallback compute cost: Qty=${quantity}, UnitCost=${unitCost}, RowCost=${rowCost}`);
                }
            }
            
            // For asset documents, ALWAYS calculate from quantity * unitPrice for accuracy
            // This ensures VAT calculation uses the correct totalPrice value
            // Do NOT use totalPriceDisplayEl value as it may be incorrect or stale
            const quantityInput = row.querySelector('.quantity-input');
            const unitPriceInput = row.querySelector('.unit-price-input');
            
            if (!unitPriceInput) {
                console.warn(`Row ${index + 1}: unit-price-input not found, skipping price calculation`);
                rowPrice = 0;
            } else {
                // Parse values, removing any formatting (commas, spaces)
                const quantityRaw = (quantityInput?.value || '1').toString().replace(/[,\s]/g, '');
                const unitPriceRaw = (unitPriceInput?.value || '0').toString().replace(/[,\s]/g, '');
                
                // Also check the displayed value for comparison
                const unitPriceDisplayed = unitPriceInput.getAttribute('value') || unitPriceInput.value;
                
                const quantity = parseFloat(quantityRaw) || 1; // Default to 1 for asset documents
                const unitPrice = parseFloat(unitPriceRaw) || 0;
                
                // Always recalculate from raw values, ignore any display value
                rowPrice = quantity * unitPrice;
                
                console.log(`Row ${index + 1} calculated price:`);
                console.log(`  - Quantity: ${quantity} (raw: "${quantityRaw}")`);
                console.log(`  - UnitPrice input.value: "${unitPriceInput.value}"`);
                console.log(`  - UnitPrice raw parsed: ${unitPrice} (raw: "${unitPriceRaw}")`);
                console.log(`  - RowPrice: ${rowPrice}`);
                
                // Validation: Warn if unitPrice seems unusually high (might be unitCost instead)
                if (unitPrice > 0 && unitPrice > 1000000) {
                    console.error(`Row ${index + 1}: ERROR - UnitPrice (${unitPrice}) seems unusually high! This might be unitCost instead of unitPrice. Expected value should match the displayed unit price in the table.`);
                }
            }

            const endingDepEl = row.querySelector('.ending-depreciation-display');
            if (endingDepEl) {
                const endingDepValue = (endingDepEl.value ?? endingDepEl.textContent ?? '0').toString().replace(/,/g, '');
                const numericEndingDep = parseFloat(endingDepValue) || 0;
                totalEndingDep += numericEndingDep;
            }

            const depAmountEl = row.querySelector('.depreciation-amount-display');
            if (depAmountEl) {
                const depAmountValue = (depAmountEl.value ?? depAmountEl.textContent ?? '0').toString().replace(/,/g, '');
                const numericDepAmount = parseFloat(depAmountValue) || 0;
                totalDepAmount += numericDepAmount;
            }
            
            // Accumulate totals (ensure we're adding numbers, not strings)
            totalCost = (Number(totalCost) || 0) + (Number(rowCost) || 0);
            totalPrice = (Number(totalPrice) || 0) + (Number(rowPrice) || 0);
            
            console.log(`Row ${index + 1}: RowCost=${rowCost}, RowPrice=${rowPrice}, Running totals: TotalCost=${totalCost}, TotalPrice=${totalPrice}`);
        });
    }
    
    // Final validation: ensure totals are numbers
    totalCost = Number(totalCost) || 0;
    totalPrice = Number(totalPrice) || 0;
    totalEndingDep = parseFloat(totalEndingDep.toFixed(6));
    
    console.log(`${debugPrefix}: Final totals after calculation: TotalCost=${totalCost}, TotalPrice=${totalPrice}, TotalEndingDep=${totalEndingDep}`);

    let doc11TotalCost = totalCost;
    let doc11EndingDep = totalEndingDep;
    let doc11DepAmount = totalDepAmount;

    if (documentTypeId === 11) {
        const summaryCost = getSummaryValue('sum-unit-cost');
        const summaryEndingDep = getSummaryValue('sum-ending-depreciation');
        const summaryDepAmount = getSummaryValue('sum-depreciation-amount');

        if (summaryCost !== null) {
            doc11TotalCost = summaryCost;
        }
        if (summaryEndingDep !== null) {
            doc11EndingDep = summaryEndingDep;
        }
        if (summaryDepAmount !== null) {
            doc11DepAmount = summaryDepAmount;
        }
    }
    
    // Step 2: Calculate VAT amount using context processor rate
    // VatPercent from document data is a percentage (e.g., 10 for 10%)
    // We need to divide by 100 to get the decimal rate for calculation
    const vatPercentRaw = (docData.VatPercent || '0').toString().replace(/[,\s]/g, '');
    const vatPercent = parseFloat(vatPercentRaw) || 0;
    
    // VAT calculation: (basis * percentage) / 100
    // Only apply VAT when IsVat is true; choose basis by document type
    // Asset issue (11) uses totalPrice, asset receipt (10) uses totalCost
    const vatBasis = documentTypeId === 11 ? totalPrice : totalCost;
    
    // Ensure all values are numbers
    const vatBasisNum = Number(vatBasis) || 0;
    const vatPercentNum = Number(vatPercent) || 0;
    
    // Calculate VAT: (basis * percentage) / 100
    const vatAmount = docData.IsVat ? (vatBasisNum * vatPercentNum) / 100 : 0;
    
    console.log(`${debugPrefix}: VAT Calculation Details:`);
    console.log(`  - DocumentTypeId: ${documentTypeId}`);
    console.log(`  - IsVat: ${docData.IsVat}`);
    console.log(`  - TotalCost: ${totalCost}`);
    console.log(`  - TotalPrice: ${totalPrice}`);
    console.log(`  - VatBasis: ${vatBasisNum} (${documentTypeId === 11 ? 'totalPrice' : 'totalCost'})`);
    console.log(`  - VatPercent: ${vatPercentNum}% (from docData.VatPercent: "${docData.VatPercent}")`);
    console.log(`  - VatAmount: ${vatAmount} = (${vatBasisNum} * ${vatPercentNum}) / 100`);
    
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
    console.log('VatPercent:', vatPercent);
    console.log('VatAmount:', vatAmount);
    
    console.log(`${debugPrefix}: Processing ${docData.template_details.length} template details...`);
    
    const netBookValue = Math.max(doc11TotalCost - doc11EndingDep, 0);

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
        
        const assetAccountId = docData.AccountId ? Number(docData.AccountId) : null;
        const depreciationAccountId = docData.DepreciationAccountId ? Number(docData.DepreciationAccountId) : null;
        const expenseAccountId = docData.ExpenseAccountId ? Number(docData.ExpenseAccountId) : null;
        let handledDoc11SpecialCase = false;

        if (documentTypeId === 11) {
            // Handle specific DocumentType 11 cases first
            if (assetAccountId && templateDetail.AccountId === assetAccountId) {
                currencyAmount = doc11TotalCost;
                handledDoc11SpecialCase = true;
                console.log('DocType 11 rule: asset account matched, using totalCost:', currencyAmount);
            } else if (depreciationAccountId && templateDetail.AccountId === depreciationAccountId) {
                currencyAmount = doc11EndingDep;
                handledDoc11SpecialCase = true;
                console.log('DocType 11 rule: depreciation account matched, using totalEndingDep:', currencyAmount);
            } else if (templateDetail.AccountTypeId === 83) {
                currencyAmount = templateDetail.IsDebit ? netBookValue : 0;
                handledDoc11SpecialCase = true;
                console.log('DocType 11 rule: accountType 83 matched, using net book value:', currencyAmount);
            }
            // Note: Don't force currencyAmount to 0 for other accounts - let the normal IsVat logic handle them
            // This allows VAT accounts (AccountTypeId 6, 47) and other account types to be processed correctly
        }

        // Apply logic based on document type (asset only) when special rule not triggered
        if (!handledDoc11SpecialCase && [10, 11].includes(documentTypeId)) {
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
                    // For DocumentTypeId=10, use totalCost; for DocumentTypeId=11, use totalPrice
                    currencyAmount = documentTypeId === 10 ? totalCost : totalPrice;
                    console.log(`Rule: IsVat=false, AccountTypeId=${accountTypeId}, CurrencyAmount=${documentTypeId === 10 ? 'TotalCost' : 'TotalPrice'} (${currencyAmount})`);
                } else if (accountTypeId === 83) {
                    currencyAmount = documentTypeId === 11 ? netBookValue : totalCost;
                    console.log(`Rule: IsVat=false, AccountTypeId=${accountTypeId}, CurrencyAmount=${documentTypeId === 11 ? 'NetBookValue' : 'TotalCost'} (${currencyAmount})`);
                } else if ([8, 9, 11].includes(accountTypeId)) {
                    currencyAmount = totalCost;
                    console.log(`Rule: IsVat=false, AccountTypeId=${accountTypeId}, CurrencyAmount=TotalCost (${currencyAmount})`);
                }
            } else {
                // IsVat = true rules
                // For DocumentType 10: use totalCost, For DocumentType 11: use totalPrice
                if ([3, 5, 42, 43].includes(accountTypeId)) {
                    // For DocumentTypeId=10, use totalCost + vatAmount; for DocumentTypeId=11, use totalPrice + vatAmount
                    const basis = documentTypeId === 10 ? totalCost : totalPrice;
                    currencyAmount = basis + vatAmount;
                    console.log(`Rule: IsVat=true, AccountTypeId=${accountTypeId}, CurrencyAmount=${documentTypeId === 10 ? 'TotalCost' : 'TotalPrice'}+VatAmount (${currencyAmount})`);
                } else if (accountTypeId >= 69 && accountTypeId <= 77) {
                    // For DocumentTypeId=10, use totalCost; for DocumentTypeId=11, use totalPrice
                    currencyAmount = documentTypeId === 10 ? totalCost : totalPrice;
                    console.log(`Rule: IsVat=true, AccountTypeId=${accountTypeId}, CurrencyAmount=${documentTypeId === 10 ? 'TotalCost' : 'TotalPrice'} (${currencyAmount})`);
                } else if ([6, 47].includes(accountTypeId)) {
                    currencyAmount = vatAmount;
                    console.log(`Rule: IsVat=true, AccountTypeId=${accountTypeId}, CurrencyAmount=VatAmount (${currencyAmount})`);
                } else if (accountTypeId === 83) {
                    currencyAmount = documentTypeId === 11 ? netBookValue : totalCost;
                    console.log(`Rule: IsVat=true, AccountTypeId=${accountTypeId}, CurrencyAmount=${documentTypeId === 11 ? 'NetBookValue' : 'TotalCost'} (${currencyAmount})`);
                } else if ([8, 9, 11].includes(accountTypeId)) {
                    currencyAmount = totalCost;
                    console.log(`Rule: IsVat=true, AccountTypeId=${accountTypeId}, CurrencyAmount=TotalCost (${currencyAmount})`);
                }
            }
        } else if (!handledDoc11SpecialCase) {
            // For non-specified document types, use total cost
            currencyAmount = totalCost;
            console.log('Rule: Non-specified document type, CurrencyAmount =', currencyAmount);
        }
        
        // Fallback: If currencyAmount is still 0 and we have data, use a default calculation
        // BUT: Don't override if we've already handled a special case (amount might legitimately be 0)
        if (!handledDoc11SpecialCase && currencyAmount === 0 && (totalCost > 0 || totalPrice > 0)) {
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
