/**
 * Shared JavaScript Components for Silicon4 Accounting
 * Reusable functions across all templates
 * 
 * This file provides backward-compatible enhancements to existing functionality
 * All existing code will continue to work without modification
 */

// Global message system - enhances existing alert() calls
window.Silicon4Message = {
    show: function(message, type = 'info', duration = 3000) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `fixed top-4 right-4 px-4 py-2 rounded-md shadow-lg z-50 ${
            type === 'success' ? 'bg-green-100 text-green-800 border border-green-200' :
            type === 'error' ? 'bg-red-100 text-red-800 border border-red-200' :
            type === 'warning' ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' :
            'bg-blue-100 text-blue-800 border border-blue-200'
        }`;
        messageDiv.textContent = message;
        
        document.body.appendChild(messageDiv);
        
        setTimeout(() => {
            messageDiv.remove();
        }, duration);
    },
    
    success: function(message) { this.show(message, 'success'); },
    error: function(message) { this.show(message, 'error'); },
    warning: function(message) { this.show(message, 'warning'); },
    info: function(message) { this.show(message, 'info'); }
};

// Global balance validation utilities
window.Silicon4Balance = {
    /**
     * Generic function to validate debit/credit balance for document details
     * @param {string} tbodyId - ID of the table body containing the rows
     * @param {string} debitSelector - CSS selector for debit amount inputs
     * @param {string} creditSelector - CSS selector for credit amount inputs
     * @param {number} tolerance - Tolerance for floating point differences (default: 0.01)
     * @returns {Object} - {isBalanced: boolean, totalDebit: number, totalCredit: number, difference: number}
     */
    validateBalance: function(tbodyId, debitSelector, creditSelector, tolerance = 0.01) {
        const tbody = document.getElementById(tbodyId);
        if (!tbody) {
            console.error(`Table body with ID '${tbodyId}' not found`);
            return { isBalanced: false, totalDebit: 0, totalCredit: 0, difference: 0 };
        }

        const debitInputs = tbody.querySelectorAll(debitSelector);
        const creditInputs = tbody.querySelectorAll(creditSelector);
        
        let totalDebit = 0;
        let totalCredit = 0;

        // Sum up debit amounts
        debitInputs.forEach(input => {
            const value = parseFloat(input.value) || 0;
            totalDebit += value;
        });
        
        // Sum up credit amounts
        creditInputs.forEach(input => {
            const value = parseFloat(input.value) || 0;
            totalCredit += value;
        });

        const difference = Math.abs(totalDebit - totalCredit);
        const isBalanced = difference <= tolerance;

        return {
            isBalanced: isBalanced,
            totalDebit: totalDebit,
            totalCredit: totalCredit,
            difference: difference
        };
    },

    /**
     * Validate balance and show error message if not balanced
     * @param {string} tbodyId - ID of the table body
     * @param {string} debitSelector - CSS selector for debit inputs
     * @param {string} creditSelector - CSS selector for credit inputs
     * @param {string} errorMessage - Custom error message
     * @returns {boolean} - true if balanced, false if not
     */
    validateAndShowError: function(tbodyId, debitSelector, creditSelector, errorMessage = null) {
        const balanceCheck = this.validateBalance(tbodyId, debitSelector, creditSelector);
        
        if (!balanceCheck.isBalanced) {
            const message = errorMessage || `Document is not balanced. Difference: ${balanceCheck.difference.toFixed(2)}`;
                Silicon4Message.error(message);
            return false;
        }
        
        return true;
    },

    /**
     * Update balance display elements with current totals
     * @param {string} tbodyId - ID of the table body
     * @param {string} debitSelector - CSS selector for debit inputs
     * @param {string} creditSelector - CSS selector for credit inputs
     * @param {string} totalDebitElementId - ID of element to show total debit
     * @param {string} totalCreditElementId - ID of element to show total credit
     * @param {string} balanceStatusElementId - ID of element to show balance status
     */
    updateBalanceDisplay: function(tbodyId, debitSelector, creditSelector, totalDebitElementId, totalCreditElementId, balanceStatusElementId) {
        const balanceCheck = this.validateBalance(tbodyId, debitSelector, creditSelector);
        
        // Update total debit display
        const totalDebitElement = document.getElementById(totalDebitElementId);
        if (totalDebitElement) {
            totalDebitElement.textContent = balanceCheck.totalDebit.toFixed(2);
        }
        
        // Update total credit display
        const totalCreditElement = document.getElementById(totalCreditElementId);
        if (totalCreditElement) {
            totalCreditElement.textContent = balanceCheck.totalCredit.toFixed(2);
        }
            
        // Update balance status
        const balanceStatusElement = document.getElementById(balanceStatusElementId);
        if (balanceStatusElement) {
            if (balanceCheck.isBalanced) {
                balanceStatusElement.textContent = 'Balanced ✓';
                balanceStatusElement.className = 'text-green-600 font-bold';
            } else {
                balanceStatusElement.textContent = `Not Balanced (${balanceCheck.difference.toFixed(2)})`;
                balanceStatusElement.className = 'text-red-600 font-bold';
            }
        }
    }
};

// Global form utilities
window.Silicon4Form = {
    showLoading: function(button, loadingText = 'Processing...') {
        if (!button) return;
        
        // Store original text
        button.dataset.originalText = button.innerHTML;
        
        // Show loading state
        button.disabled = true;
        button.innerHTML = `<span class="inline-flex items-center">
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            ${loadingText}
        </span>`;
    },
    
    hideLoading: function(button) {
        if (!button) return;
        
        button.disabled = false;
        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
        }
    },

    // Initialize form validation
    initFormValidation: function(formSelector, fieldRules) {
        const form = document.querySelector(formSelector);
        if (!form) return;
        
        // Add validation to each field
        Object.keys(fieldRules).forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                const rules = fieldRules[fieldName];
                
                // Add real-time validation
                field.addEventListener('blur', () => {
                    this.validateField(field, rules);
                });
                
                field.addEventListener('input', () => {
                    // Clear error state on input
                    field.classList.remove('border-red-500');
                });
            }
        });
    }
};

// Global print utilities
window.Silicon4Print = {
    document: function(documentId, documentNo, documentDate, description, createdBy, title = 'Document') {
        const printWindow = window.open('', '_blank', 'width=800,height=600');
        const printContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>${title} - ${documentNo}</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { text-align: center; margin-bottom: 30px; }
                    .document-info { margin-bottom: 20px; }
                    .info-row { margin: 10px 0; }
                    .label { font-weight: bold; width: 150px; display: inline-block; }
                    .footer { margin-top: 50px; text-align: center; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>${title}</h1>
                </div>
                
                <div class="document-info">
                    <div class="info-row">
                        <span class="label">Document ID:</span>
                        <span>${documentId}</span>
                </div>
                    <div class="info-row">
                        <span class="label">Document No:</span>
                        <span>${documentNo}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Date:</span>
                        <span>${documentDate}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Description:</span>
                        <span>${description}</span>
                    </div>
                    <div class="info-row">
                        <span class="label">Created By:</span>
                        <span>${createdBy}</span>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Silicon4 Accounting System</p>
                    <p>Printed: ${new Date().toLocaleString()}</p>
                </div>
            </body>
            </html>
        `;
        
        printWindow.document.write(printContent);
        printWindow.document.close();
        printWindow.focus();
    }
};

// Global filter utilities
window.Silicon4Filter = {
    debug: false,
    
    // Set debug mode
    setDebug: function(enabled) {
        this.debug = enabled;
    },
    
    // Log debug messages
    log: function(message, data = null) {
        if (this.debug) {
            console.log(`[Silicon4Filter] ${message}`, data || '');
        }
    },
    
    initialize: function(filterInputs, applyFunction) {
        this.log('Initializing filters', filterInputs);
        
        filterInputs.forEach(function(filterId) {
            const element = document.getElementById(filterId);
            if (element) {
                // Remove existing event listeners to prevent duplicates
                element.removeEventListener('input', applyFunction);
                element.removeEventListener('change', applyFunction);
                
                // Add new event listeners
                element.addEventListener('input', applyFunction);
                element.addEventListener('change', applyFunction);
                
                this.log(`Filter initialized: ${filterId}`, element);
            } else {
                console.warn(`Filter element not found: ${filterId}`);
            }
        }.bind(this));
        
        // Store the apply function
        this.applyFunction = applyFunction;
    },
    
    clear: function(filterInputs) {
        this.log('Clearing filters', filterInputs);
        
        filterInputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                input.value = '';
            }
        });
        
        // Re-apply filters to show all rows
        if (this.applyFunction) {
            this.applyFunction();
        }
    },
    
    apply: function(rows, filters, rowDataExtractor) {
        this.log('Applying filters', { rowCount: rows.length, filters: filters });
        
        rows.forEach(row => {
            const rowData = rowDataExtractor(row);
            let shouldShow = true;
            
            // Check each filter
            Object.keys(filters).forEach(filterKey => {
                const filterValue = filters[filterKey];
                if (filterValue && filterValue.trim() !== '') {
                    const cellValue = rowData[filterKey] || '';
                    if (!cellValue.toString().toLowerCase().includes(filterValue.toLowerCase())) {
                        shouldShow = false;
                    }
                }
            });
            
            row.style.display = shouldShow ? '' : 'none';
        });
    },

    // Enhanced row data extractor that handles different table structures
    createRowDataExtractor: function(columnMappings) {
        return function(row) {
            const cells = row.querySelectorAll('td');
            const rowData = {};
            
            Object.keys(columnMappings).forEach(filterKey => {
                const columnIndex = columnMappings[filterKey];
                if (columnIndex < cells.length) {
                    const cell = cells[columnIndex];
                    // Get text content, handling nested elements
                    rowData[filterKey] = cell.textContent.trim();
                }
            });
            
            return rowData;
        };
    },

    // Auto-detect column mappings from table headers
    autoDetectColumnMappings: function(tableSelector) {
        const table = document.querySelector(tableSelector);
        if (!table) {
            console.error('Table not found:', tableSelector);
            return {};
        }
        
        const headerRow = table.querySelector('thead tr');
        if (!headerRow) {
            console.error('Header row not found in table:', tableSelector);
            return {};
        }
        
        const headers = headerRow.querySelectorAll('th');
        const mappings = {};
        
        headers.forEach((header, index) => {
            const headerText = header.textContent.trim().toLowerCase();
            
            // Map common header patterns to filter keys
            if (headerText.includes('document') && headerText.includes('no')) {
                mappings['document-no'] = index;
            } else if (headerText.includes('type')) {
                mappings['document-type'] = index;
            } else if (headerText.includes('client') || headerText.includes('харилцагч')) {
                mappings['client'] = index;
            } else if (headerText.includes('date') || headerText.includes('огноо')) {
                mappings['date'] = index;
            } else if (headerText.includes('description') || headerText.includes('тайлбар') || headerText.includes('утга')) {
                mappings['description'] = index;
            } else if (headerText.includes('account') || headerText.includes('данс')) {
                mappings['account'] = index;
            } else if (headerText.includes('currency') || headerText.includes('валют')) {
                mappings['currency'] = index;
            } else if (headerText.includes('exchange') || headerText.includes('ханш')) {
                mappings['currency-exchange'] = index;
            } else if (headerText.includes('amount') || headerText.includes('дүн')) {
                mappings['mnt-amount'] = index;
            } else if (headerText.includes('user') || headerText.includes('хэрэглэгч') || headerText.includes('admin')) {
                mappings['created-by'] = index;
            }
        });
        
        this.log('Auto-detected column mappings', mappings);
        return mappings;
    },

    // Initialize filters with auto-detection
    initializeWithAutoDetection: function(tableSelector, filterInputs, customMappings = null) {
        const mappings = customMappings || this.autoDetectColumnMappings(tableSelector);
        const rowDataExtractor = this.createRowDataExtractor(mappings);
        
        const applyFunction = () => {
            const table = document.querySelector(tableSelector);
            if (!table) return;
            
            const rows = table.querySelectorAll('tbody tr');
            const filters = {};
            
            // Collect current filter values
            filterInputs.forEach(inputId => {
                const input = document.getElementById(inputId);
                if (input) {
                    const filterKey = inputId.replace('filter-', '');
                    filters[filterKey] = input.value;
                }
            });
            
            this.apply(rows, filters, rowDataExtractor);
        };
        
        this.initialize(filterInputs, applyFunction);
        return applyFunction;
    },

    // Enhanced filter with better error handling and debugging
    applyWithErrorHandling: function(rows, filters, rowDataExtractor) {
        try {
            this.apply(rows, filters, rowDataExtractor);
        } catch (error) {
            console.error('Error applying filters:', error);
            this.log('Filter application failed', { error: error.message, filters: filters });
        }
    }
};

// Global event handler utilities
window.Silicon4Events = {
    addOnce: function(element, event, handler) {
        if (element && !element.hasAttribute('data-event-listener-added')) {
            element.addEventListener(event, handler);
            element.setAttribute('data-event-listener-added', 'true');
        }
    }
};

// Global delete utilities
window.Silicon4Delete = {
    showModal: function(deleteUrl, itemName, callback) {
        const modal = document.getElementById('delete-modal');
        const modalText = document.getElementById('delete-modal-text');
        const confirmButton = document.getElementById('delete-confirm-btn');
        
        if (!modal || !modalText || !confirmButton) {
            console.error('Delete modal elements not found');
                    return;
                }
        
        // Update modal content
        modalText.textContent = `Are you sure you want to delete "${itemName}"?`;
        
        // Remove existing event listeners
        const newConfirmButton = confirmButton.cloneNode(true);
        confirmButton.parentNode.replaceChild(newConfirmButton, confirmButton);
        
        // Add new event listener
        newConfirmButton.addEventListener('click', function() {
        // Show loading state
            newConfirmButton.disabled = true;
            newConfirmButton.textContent = 'Deleting...';
            
            // Make delete request
            fetch(deleteUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/json',
                },
            })
            .then(response => {
                if (response.ok) {
                    Silicon4Message.success('Item deleted successfully');
                    if (callback) callback();
                    // Close modal
                    Silicon4Delete.closeModal();
                    // Reload page to reflect changes
                    window.location.reload();
                } else {
                    throw new Error('Delete failed');
                }
            })
            .catch(error => {
                console.error('Delete error:', error);
                Silicon4Message.error('Failed to delete item');
                newConfirmButton.disabled = false;
                newConfirmButton.textContent = 'Delete';
            });
        });
        
        // Show modal
        modal.classList.remove('hidden');
    },
    
    closeModal: function() {
        const modal = document.getElementById('delete-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }
};

// Global VAT utilities
window.Silicon4VAT = {
            init: function(options) {
                const config = {
                    isVatCheckboxId: options.isVatCheckboxId || 'customIsVat',
            vatRateFieldId: options.vatRateFieldId || 'customVatRate',
            amountFieldId: options.amountFieldId || 'customAmount',
                    vatAmountFieldId: options.vatAmountFieldId || 'customVatAmount',
            totalAmountFieldId: options.totalAmountFieldId || 'customTotalAmount',
            vatRate: options.vatRate || 10
        };
        
        const isVatCheckbox = document.getElementById(config.isVatCheckboxId);
        const vatRateField = document.getElementById(config.vatRateFieldId);
        const amountField = document.getElementById(config.amountFieldId);
        const vatAmountField = document.getElementById(config.vatAmountFieldId);
        const totalAmountField = document.getElementById(config.totalAmountFieldId);
        
        if (!isVatCheckbox || !amountField) {
            console.error('Required VAT calculation elements not found');
            return;
        }

        // Set default VAT rate
        if (vatRateField) {
            vatRateField.value = config.vatRate;
        }
        
        const calculateVAT = () => {
            const amount = parseFloat(amountField.value) || 0;
            const vatRate = parseFloat(vatRateField?.value) || config.vatRate;
            const isVat = isVatCheckbox.checked;
            
            if (isVat) {
                const vatAmount = (amount * vatRate) / 100;
                const totalAmount = amount + vatAmount;
                
                if (vatAmountField) vatAmountField.value = vatAmount.toFixed(2);
                if (totalAmountField) totalAmountField.value = totalAmount.toFixed(2);
                } else {
                if (vatAmountField) vatAmountField.value = '0.00';
                if (totalAmountField) totalAmountField.value = amount.toFixed(2);
            }
        };

        // Add event listeners
        isVatCheckbox.addEventListener('change', calculateVAT);
        amountField.addEventListener('input', calculateVAT);
        if (vatRateField) {
            vatRateField.addEventListener('input', calculateVAT);
        }
        
        // Initial calculation
        calculateVAT();
    }
};

// Global number formatting utilities
window.Silicon4NumberFormat = {
    /**
     * Format a number with specified decimal places
     * @param {number|string} value - The value to format
     * @param {number} minDecimals - Minimum decimal places
     * @param {number} maxDecimals - Maximum decimal places
     * @param {string} locale - Locale for formatting
     * @returns {string} - Formatted number string
     */
    formatNumber: function(value, minDecimals = 2, maxDecimals = 2, locale = 'en-US') {
        if (value === null || value === undefined || value === '' || value === '-') {
            return '-';
        }
        
            const num = parseFloat(value);
        if (isNaN(num)) {
            return '-';
        }
        
                return num.toLocaleString(locale, {
                    minimumFractionDigits: minDecimals,
                    maximumFractionDigits: maxDecimals
                });
    },

    /**
     * Format a number as currency
     * @param {number|string} value - The value to format
     * @returns {string} - Formatted currency string
     */
    formatCurrency: function(value) {
        return this.formatNumber(value, 2, 2);
    },

    /**
     * Format a number as exchange rate
     * @param {number|string} value - The value to format
     * @returns {string} - Formatted exchange rate string
     */
    formatExchangeRate: function(value) {
        return this.formatNumber(value, 2, 2);
    },

    /**
     * Format all numbers on the page with specified selector
     * @param {string} selector - CSS selector for elements to format
     * @param {number} minDecimals - Minimum decimal places
     * @param {number} maxDecimals - Maximum decimal places
     */
    formatNumbersOnPage: function(selector = '.number-format', minDecimals = 2, maxDecimals = 2) {
        const elements = document.querySelectorAll(selector);
        elements.forEach(function(element) {
            const value = element.textContent.trim();
            if (value && value !== '-') {
                // Only format if the value looks like a raw number (not already formatted)
                // Check if it contains commas or is already formatted
                if (!value.includes(',') && !isNaN(parseFloat(value))) {
                    element.textContent = Silicon4NumberFormat.formatNumber(value, minDecimals, maxDecimals);
                }
            }
        });
    },

    /**
     * Format currency values on the page
     */
    formatCurrencyOnPage: function() {
        const elements = document.querySelectorAll('.currency-format');
        elements.forEach(function(element) {
            const value = element.textContent.trim();
            if (value && value !== '-') {
                // Only format if the value looks like a raw number (not already formatted)
                if (!value.includes(',') && !isNaN(parseFloat(value))) {
                    element.textContent = Silicon4NumberFormat.formatNumber(value, 2, 2);
                }
            }
        });
    },

    /**
     * Format exchange rates on the page
     */
    formatExchangeOnPage: function() {
        const elements = document.querySelectorAll('.exchange-format');
        elements.forEach(function(element) {
            const value = element.textContent.trim();
            if (value && value !== '-') {
                // Only format if the value looks like a raw number (not already formatted)
                if (!value.includes(',') && !isNaN(parseFloat(value))) {
                    element.textContent = Silicon4NumberFormat.formatNumber(value, 2, 2);
                }
            }
        });
    },

    /**
     * Format account codes on the page
     */
    formatAccountOnPage: function() {
        const elements = document.querySelectorAll('.account-format');
        elements.forEach(function(element) {
            const value = element.textContent.trim();
            if (value && value !== '-') {
                // Limit account codes to maximum 9 characters
                const formattedValue = value.length > 9 ? value.substring(0, 9) : value;
                element.textContent = formattedValue;
            }
        });
    },

    /**
     * Initialize number formatting for the entire page
     */
    initializeNumberFormatting: function() {
        this.formatNumbersOnPage('.number-format');
        this.formatCurrencyOnPage();
        this.formatExchangeOnPage();
        this.formatAccountOnPage();
    }
};

// Global grid utilities
window.Silicon4Grid = {
    /**
     * Auto-adjust column widths based on content
     * @param {string} tableSelector - CSS selector for the table
     * @param {number} maxWidth - Maximum column width
     * @param {boolean} responsive - Whether to use responsive widths
     */
    autoAdjustColumnWidths: function(tableSelector, maxWidth = 300, responsive = false) {
        const table = document.querySelector(tableSelector);
        if (!table) return;

        const headerRow = table.querySelector('thead tr');
        if (!headerRow) return;

        const headers = headerRow.querySelectorAll('th');
        
        headers.forEach((header, index) => {
            const headerText = header.textContent.trim().toLowerCase();
            let minWidth = 100; // Increased default minimum width
            
            // Column widths are now handled by CSS with nth-child selectors
        });
    },

    /**
     * Apply user field width (for user filtering)
     * @param {string} tableSelector - CSS selector for the table
     */
    applyUserFieldWidth: function(tableSelector) {
        const userWidths = {
            'filter-created-by': 25 // Narrower for user field
        };
        
        this.forceFilterWidths(tableSelector, userWidths);
    },

    /**
     * Ensure account columns maintain their width
     * @param {string} tableSelector - CSS selector for the table
     */
    ensureAccountColumnWidth: function(tableSelector) {
        const table = document.querySelector(tableSelector);
        if (!table) {
            console.error(`[Silicon4Grid] Table not found: ${tableSelector}`);
            return;
        }

        const headerRow = table.querySelector('thead tr');
        if (!headerRow) {
            console.error(`[Silicon4Grid] Header row not found in table: ${tableSelector}`);
            return;
        }

        const headers = headerRow.querySelectorAll('th');
        
        headers.forEach((header, index) => {
            const headerText = header.textContent.trim().toLowerCase();
            
               if (headerText.includes('account') || headerText.includes('данс')) {
                   // Force account column width to 95px
                   header.style.setProperty('min-width', '95px', 'important');
                   header.style.setProperty('width', '95px', 'important');
                   header.style.setProperty('max-width', '95px', 'important');
                   
                   
                   // Also apply to corresponding data cells
                   const dataRows = table.querySelectorAll('tbody tr');
                   dataRows.forEach(row => {
                       const cells = row.querySelectorAll('td');
                       if (cells[index]) {
                           cells[index].style.setProperty('min-width', '95px', 'important');
                           cells[index].style.setProperty('width', '95px', 'important');
                           cells[index].style.setProperty('max-width', '95px', 'important');
                       }
                   });
               } else if (headerText.includes('type') || headerText.includes('төрөл')) {
                   // Force document type column width to 25px
                   header.style.setProperty('min-width', '25px', 'important');
                   header.style.setProperty('width', '25px', 'important');
                   header.style.setProperty('max-width', '25px', 'important');
                   
                   // Also apply to corresponding data cells
                   const dataRows = table.querySelectorAll('tbody tr');
                   dataRows.forEach(row => {
                       const cells = row.querySelectorAll('td');
                       if (cells[index]) {
                           cells[index].style.setProperty('min-width', '25px', 'important');
                           cells[index].style.setProperty('width', '25px', 'important');
                           cells[index].style.setProperty('max-width', '25px', 'important');
                       }
                   });
               }
        });
    },

    /**
     * Ensure user columns maintain their width
     * @param {string} tableSelector - CSS selector for the table
     */
    ensureUserColumnWidth: function(tableSelector) {
        const table = document.querySelector(tableSelector);
        if (!table) return;

        const headerRow = table.querySelector('thead tr');
        if (!headerRow) return;

        const headers = headerRow.querySelectorAll('th');
        
        headers.forEach((header, index) => {
            const headerText = header.textContent.trim().toLowerCase();
            
            if (headerText.includes('user') || headerText.includes('хэрэглэгч')) {
                // Force user column width to 30px
                header.style.setProperty('min-width', '30px', 'important');
                header.style.setProperty('width', '30px', 'important');
                header.style.setProperty('max-width', '30px', 'important');
                console.log(`[Silicon4Grid] ✅ Forced user column at index ${index} to 30px width`);
                
                // Also apply to corresponding data cells
                const dataRows = table.querySelectorAll('tbody tr');
                dataRows.forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells[index]) {
                        cells[index].style.setProperty('min-width', '30px', 'important');
                        cells[index].style.setProperty('width', '30px', 'important');
                        cells[index].style.setProperty('max-width', '30px', 'important');
                    }
                });
            }
        });
    },

    /**
     * Force specific widths for filter inputs
     * @param {string} tableSelector - CSS selector for the table
     * @param {Object} filterWidths - Object mapping filter IDs to widths
     */
    forceFilterWidths: function(tableSelector, filterWidths) {
        const table = document.querySelector(tableSelector);
        if (!table) return;

        Object.keys(filterWidths).forEach(filterId => {
            const filter = document.getElementById(filterId);
            if (filter) {
                const width = filterWidths[filterId];
                filter.style.width = width + 'px !important';
                filter.style.minWidth = width + 'px !important';
                filter.style.maxWidth = width + 'px !important';
            }
        });
    },

    /**
     * Initialize grid with configuration
     * @param {Object} config - Configuration object
     */
    initializeGrid: function(config) {
        const {
            tableSelector,
            autoAdjust = true,
            maxWidth = 300,
            forceFilterWidths = null
        } = config;

        if (!tableSelector) {
            console.error('Silicon4Grid.initializeGrid requires tableSelector');
            return;
        }

        // If autoAdjust is true, set up auto-adjustment
        if (autoAdjust) {
            this.autoAdjustColumnWidths(tableSelector, maxWidth, config.responsive || false);
        }
        
        
        // Apply forced filter widths if specified
        if (forceFilterWidths && typeof forceFilterWidths === 'object') {
            setTimeout(() => {
                this.forceFilterWidths(tableSelector, forceFilterWidths);
            }, 100);
        }
        
        // Ensure account columns maintain their width
        setTimeout(() => {
            this.ensureAccountColumnWidth(tableSelector);
        }, 200);
        
        // Ensure user columns maintain their width
        setTimeout(() => {
            this.ensureUserColumnWidth(tableSelector);
        }, 250);
        
        // Apply user field width (for user filtering)
        setTimeout(() => {
            this.applyUserFieldWidth(tableSelector);
        }, 150);
    }
};

// Generic CSS Classes for Tables
const Silicon4TableCSS = {
    /**
     * Initialize generic table CSS classes
     */
    initializeTableCSS: function() {
        // Add generic table cell styles
        const style = document.createElement('style');
        style.textContent = `
            .table-cell {
                padding: 0.25rem 1rem;
                white-space: nowrap;
                font-size: 0.875rem;
                color: #111827;
                border-right: 1px solid #e5e7eb;
                text-align: left; /* Default left alignment for text */
            }
            .table-cell-description {
                white-space: normal;
                max-width: 200px;
                text-align: left; /* Descriptions should be left-aligned */
            }
            .table-cell-right {
                text-align: right;
            }
            .table-cell-last {
                border-right: none;
            }
            
            /* Column width constraints - using nth-child selectors */
            /* Document type code column (Б) - 2nd column */
            th.table-cell:nth-child(2),
            td.table-cell:nth-child(2) {
                width: 25px !important;
                min-width: 25px !important;
                max-width: 25px !important;
                text-align: center;
            }
            
            /* VAT column (НӨТ) - 6th column */
            th.table-cell:nth-child(6),
            td.table-cell:nth-child(6) {
                width: 15px !important;
                min-width: 15px !important;
                max-width: 15px !important;
                text-align: center;
            }
            
            /* Currency column (Валют) - 8th column */
            th.table-cell:nth-child(8),
            td.table-cell:nth-child(8) {
                width: 30px !important;
                min-width: 30px !important;
                max-width: 30px !important;
                text-align: center;
            }
            
            /* User column (Хэр) - 12th column */
            th.table-cell:nth-child(12),
            td.table-cell:nth-child(12) {
                width: 15px !important;
                min-width: 15px !important;
                max-width: 15px !important;
                text-align: center;
            }
            
            /* Action column - 13th column */
            th.table-cell:nth-child(13),
            td.table-cell:nth-child(13) {
                width: 120px !important;
                min-width: 120px !important;
                max-width: 120px !important;
                text-align: center;
            }
            
            /* Filter input width constraints to match columns */
            td.table-cell:nth-child(2) .filter-input {
                width: 25px !important;
                min-width: 25px !important;
                max-width: 25px !important;
            }
            td.table-cell:nth-child(6) .filter-input {
                width: 15px !important;
                min-width: 15px !important;
                max-width: 15px !important;
            }
            td.table-cell:nth-child(8) .filter-input {
                width: 30px !important;
                min-width: 30px !important;
                max-width: 30px !important;
            }
            td.table-cell:nth-child(12) .filter-input {
                width: 15px !important;
                min-width: 15px !important;
                max-width: 15px !important;
            }
            
            /* Generic action button styling */
            .action-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: 0.25rem;
                border-radius: 0.25rem;
                border: none;
                background: none;
                cursor: pointer;
                transition: all 0.15s ease-in-out;
                width: 24px;
                height: 24px;
            }
            .action-btn:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
            .action-btn svg {
                width: 16px;
                height: 16px;
            }
            .action-btn.blue { color: #2563eb; }
            .action-btn.blue:hover { color: #1d4ed8; background-color: #dbeafe; }
            .action-btn.green { color: #16a34a; }
            .action-btn.green:hover { color: #15803d; background-color: #dcfce7; }
            .action-btn.red { color: #dc2626; }
            .action-btn.red:hover { color: #b91c1c; background-color: #fee2e2; }
            .action-btn.gray { color: #6b7280; cursor: not-allowed; }
            .action-btn.gray:hover { background-color: transparent; }
            
            /* Table header styling - capitalized but not bold */
            th.table-cell {
                text-transform: uppercase;
                font-weight: normal;
                font-size: 0.75rem;
                color: #6b7280;
            }
            
            /* Number formatting classes - right aligned */
            .currency-format,
            .exchange-format,
            .number-format {
                text-align: right !important;
                display: inline-block;
                width: 100%;
            }
            
            /* Account format - left aligned for codes */
            .account-format {
                text-align: left !important;
                display: inline-block;
                width: 100%;
            }
            
            /* Filter input styling - widths handled by JavaScript */
            .filter-input {
                padding: 0.25rem 0.5rem;
                font-size: 0.75rem;
                border: 1px solid #d1d5db;
                border-radius: 0.375rem;
                background-color: #ffffff;
                transition: all 0.15s ease-in-out;
                text-align: left;
            }
            .filter-input:focus {
                outline: none;
                border-color: #3b82f6;
                box-shadow: 0 0 0 1px #3b82f6;
            }
            .filter-input:hover {
                border-color: #9ca3af;
            }
            .filter-input-select {
                cursor: pointer;
            }
            
            /* Filter Clear Button */
            .filter-clear-btn {
                width: 100%;
                padding: 0.25rem 0.5rem;
                font-size: 0.75rem;
                background-color: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 0.375rem;
                cursor: pointer;
                transition: all 0.15s ease-in-out;
            }
            .filter-clear-btn:hover {
                background-color: #e5e7eb;
                border-color: #9ca3af;
            }
            .filter-clear-btn:focus {
                outline: none;
                border-color: #3b82f6;
                box-shadow: 0 0 0 1px #3b82f6;
            }
        `;
        document.head.appendChild(style);
    }
};

// Make Silicon4TableCSS available globally
window.Silicon4TableCSS = Silicon4TableCSS;

// Document Number Generator
const DocumentNumberGenerator = {
    /**
     * Get the next document number for a given document type
     * @param {number} documentTypeId - The document type ID
     * @param {string} documentNoFieldId - The ID of the document number input field
     * @param {function} callback - Optional callback function to execute after success
     */
    getNextDocumentNumber: function(documentTypeId, documentNoFieldId, callback) {
        console.log('getNextDocumentNumber called with:', documentTypeId, documentNoFieldId);
        if (!documentTypeId) {
            console.error('DocumentTypeId is required');
            return;
        }

        // Show loading state
        const documentNoField = document.getElementById(documentNoFieldId);
        console.log('Document number field found:', documentNoField);
        if (documentNoField) {
            documentNoField.value = 'Loading...';
            documentNoField.disabled = true;
        }

        // Make API call
        console.log('Making API call to:', `/core/api/get-next-document-number/?document_type_id=${documentTypeId}`);
        fetch(`/core/api/get-next-document-number/?document_type_id=${documentTypeId}`)
            .then(response => {
                console.log('API response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('API response data:', data);
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Update the document number field
                if (documentNoField) {
                    documentNoField.value = data.next_document_no;
                    documentNoField.disabled = false;
                    console.log('Document number updated to:', data.next_document_no);
                }
                
                // Execute callback if provided
                if (callback && typeof callback === 'function') {
                    callback(data);
                }
            })
            .catch(error => {
                console.error('Error fetching next document number:', error);
                
                // Reset field on error
                if (documentNoField) {
                    documentNoField.value = '';
                    documentNoField.disabled = false;
                }
                
                // Show user-friendly error message
                alert('Error generating document number. Please try again.');
            });
    },

    /**
     * Initialize document type change handler for a form
     * @param {string} documentTypeFieldId - The ID of the document type select field
     * @param {string} documentNoFieldId - The ID of the document number input field
     */
    initDocumentTypeHandler: function(documentTypeFieldId, documentNoFieldId) {
        console.log('DocumentNumberGenerator.initDocumentTypeHandler called with:', documentTypeFieldId, documentNoFieldId);
        const documentTypeField = document.getElementById(documentTypeFieldId);
        
        if (!documentTypeField) {
            console.error(`Document type field with ID '${documentTypeFieldId}' not found`);
            return;
        }
        
        console.log('Document type field found:', documentTypeField);

        // Add event listener for document type change
        documentTypeField.addEventListener('change', function() {
            const selectedDocumentTypeId = this.value;
            console.log('Document type changed to:', selectedDocumentTypeId);
            
            if (selectedDocumentTypeId) {
                console.log('Calling getNextDocumentNumber with:', selectedDocumentTypeId, documentNoFieldId);
                DocumentNumberGenerator.getNextDocumentNumber(
                    selectedDocumentTypeId, 
                    documentNoFieldId
                );
            } else {
                console.log('No document type selected, clearing document number');
                // Clear document number if no document type selected
                const documentNoField = document.getElementById(documentNoFieldId);
                if (documentNoField) {
                    documentNoField.value = '';
                }
            }
        });
    }
};

// Make DocumentNumberGenerator available globally
window.DocumentNumberGenerator = DocumentNumberGenerator;

// Auto-initialize number formatting when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize table CSS
    if (typeof window.Silicon4TableCSS !== 'undefined') {
        window.Silicon4TableCSS.initializeTableCSS();
    }
    
    // Initialize number formatting
    if (typeof window.Silicon4NumberFormat !== 'undefined') {
        window.Silicon4NumberFormat.initializeNumberFormatting();
    }
});
