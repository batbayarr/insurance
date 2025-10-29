/**
 * Silicon4 Accounting - Shared JavaScript Components
 * Behavior-only functions (styling handled by CSS)
 */

// Test if the file is loaded
console.log('✅ shared-components.js loaded successfully!');

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
            const mntAmount = parseFloat(amountField.value) || 0;
            const vatRate = parseFloat(vatRateField?.value) || config.vatRate;
            const isVat = isVatCheckbox.checked;
            
            if (isVat) {
                // VAT calculation: MNT Amount includes VAT, calculate VAT as portion of total
                // VAT = MNT Amount * (VAT Rate / (100 + VAT Rate))
                // This gives: VAT = 110000 * (10 / 110) = 10000
                const vatAmount = (mntAmount * vatRate) / (100 + vatRate);
                const baseAmount = mntAmount - vatAmount;
                
                if (vatAmountField) vatAmountField.value = vatAmount.toFixed(2);
                // MNT Amount remains the same (total including VAT)
                if (totalAmountField) totalAmountField.value = mntAmount.toFixed(2);
            } else {
                if (vatAmountField) vatAmountField.value = '0.00';
                // MNT Amount remains the same (no VAT)
                if (totalAmountField) totalAmountField.value = mntAmount.toFixed(2);
            }
        };

        // Add event listeners
        isVatCheckbox.addEventListener('change', calculateVAT);
        amountField.addEventListener('input', calculateVAT);
        if (vatRateField) {
            vatRateField.addEventListener('input', calculateVAT);
        }
        
        // Make calculateVAT function globally accessible
        window.Silicon4VAT = window.Silicon4VAT || {};
        window.Silicon4VAT.calculateVAT = calculateVAT;
        
        // Initial calculation
        calculateVAT();
    }
};

// Global namespace for Silicon4 components
window.Silicon4Message = {
    // Generic message templates
    templates: {
        success: {
            'item-saved': 'Item saved successfully',
            'item-deleted': 'Item deleted successfully',
            'item-updated': 'Item updated successfully',
            'item-created': 'Item created successfully',
            'operation-completed': 'Operation completed successfully',
            'data-saved': 'Data saved successfully',
            'changes-saved': 'Changes saved successfully',
            'export-success': 'Data exported successfully',
            'import-success': 'Data imported successfully',
            'backup-success': 'Backup created successfully',
            'restore-success': 'Data restored successfully'
        },
        error: {
            'operation-failed': 'Operation failed. Please try again.',
            'save-failed': 'Failed to save. Please try again.',
            'delete-failed': 'Failed to delete item.',
            'load-failed': 'Failed to load data.',
            'validation-failed': 'Please fix the errors before submitting.',
            'network-error': 'Network error. Please check your connection.',
            'permission-denied': 'You do not have permission to perform this action.',
            'required-fields': 'Please fill in all required fields.',
            'account-required': 'Please select an account.',
            'currency-required': 'Please select a currency.',
            'document-type-required': 'Please select a document type.',
            'validation-error': 'An error occurred during validation. Please try again.',
            'load-clients-failed': 'Error loading clients. Please try again or contact support.',
            'load-assets-failed': 'Error loading asset cards. Please try again or contact support.',
            'load-inventory-failed': 'Error loading inventory items. Please try again or contact support.'
        },
        info: {
            'loading': 'Loading...',
            'processing': 'Processing...',
            'please-wait': 'Please wait...'
        },
        warning: {
            'unsaved-changes': 'You have unsaved changes.',
            'confirm-action': 'Please confirm this action.',
            'data-loss': 'This action may cause data loss.'
        }
    },

    /**
     * Show success message
     * @param {string} message - Message to display (can be template key or custom message)
     */
    success: function(message) {
        const finalMessage = this.templates.success[message] || message;
        this.show(finalMessage, 'success');
    },

    /**
     * Show error message
     * @param {string} message - Message to display (can be template key or custom message)
     */
    error: function(message) {
        const finalMessage = this.templates.error[message] || message;
        this.show(finalMessage, 'error');
    },

    /**
     * Show info message
     * @param {string} message - Message to display (can be template key or custom message)
     */
    info: function(message) {
        const finalMessage = this.templates.info[message] || message;
        this.show(finalMessage, 'info');
    },

    /**
     * Show warning message
     * @param {string} message - Message to display (can be template key or custom message)
     */
    warning: function(message) {
        const finalMessage = this.templates.warning[message] || message;
        this.show(finalMessage, 'warning');
    },

    /**
     * Show generic success message
     * @param {string} itemType - Type of item (e.g., 'Document', 'Record', 'Data')
     * @param {string} action - Action performed (e.g., 'saved', 'deleted', 'updated')
     */
    genericSuccess: function(itemType = 'Item', action = 'saved') {
        const message = `${itemType} ${action} successfully`;
        this.show(message, 'success');
    },

    /**
     * Display message with specified type
     * @param {string} message - Message to display
     * @param {string} type - Message type (success, error, info, warning)
     */
    show: function(message, type = 'info') {
        // Remove any existing messages of the same type
        const existingMessage = document.getElementById(`silicon4-message-${type}`);
        if (existingMessage) {
            existingMessage.remove();
        }
        
        // Define colors and icons for each type
        const typeConfig = {
            success: {
                bgColor: 'bg-green-500',
                icon: `<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />`,
                title: 'Success'
            },
            error: {
                bgColor: 'bg-red-500',
                icon: `<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />`,
                title: 'Error'
            },
            warning: {
                bgColor: 'bg-yellow-500',
                icon: `<path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />`,
                title: 'Warning'
            },
            info: {
                bgColor: 'bg-blue-500',
                icon: `<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />`,
                title: 'Information'
            }
        };
        
        const config = typeConfig[type] || typeConfig.info;
        
        // Create message element
        const messageEl = document.createElement('div');
        messageEl.id = `silicon4-message-${type}`;
        messageEl.className = `fixed top-4 right-4 ${config.bgColor} text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-md`;
        messageEl.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        ${config.icon}
                    </svg>
                    <span class="font-medium">${config.title}</span>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                </button>
            </div>
            <div class="mt-2 text-sm">${message}</div>
        `;

        // Add to page
        document.body.appendChild(messageEl);

        // Auto-remove after 8 seconds
        setTimeout(() => {
            if (messageEl.parentElement) {
                messageEl.remove();
            }
        }, 8000);
    }
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
                balanceStatusElement.textContent = 'balanced ✓';
                balanceStatusElement.className = 'text-green-600 font-bold';
            } else {
                balanceStatusElement.textContent = `not balanced (${balanceCheck.difference.toFixed(2)})`;
                balanceStatusElement.className = 'text-red-600 font-bold';
            }
        }
    },

};

// Test if Silicon4Balance is available
console.log('✅ Silicon4Balance object created:', typeof window.Silicon4Balance);

// Number formatting removed - handled by CSS

// Global form utilities
window.Silicon4Form = {
    showLoading: function(button, loadingText = 'Processing...') {
        if (!button) return;
        
        // Store original text
        button.dataset.originalText = button.innerHTML;
        
        // Show loading state
        button.disabled = true;
        button.innerHTML = `<span class="loading-spinner">
            <svg class="spinner-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="spinner-circle" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="spinner-path" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
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


    /**
     * Initialize form validation
     * @param {string} formSelector - CSS selector for the form
     * @param {Object} fieldRules - Object mapping field names to validation rules
     */
    initFormValidation: function(formSelector, fieldRules) {
        const form = document.querySelector(formSelector);
        if (!form) return;
        
        // Basic form validation - simplified version
        form.addEventListener('submit', (e) => {
            let isFormValid = true;
            let errorMessages = [];
            
            Object.keys(fieldRules).forEach(fieldName => {
                const field = form.querySelector(`[name="${fieldName}"]`);
                if (field) {
                    const rules = fieldRules[fieldName];
                    const value = field.value.trim();
                    
                    // Required validation
                    if (rules.required && !value) {
                        isFormValid = false;
                        errorMessages.push(`${fieldName} is required`);
                    }
                    
                    // Number validation
                    if (rules.number && value && isNaN(parseFloat(value))) {
                        isFormValid = false;
                        errorMessages.push(`${fieldName} must be a valid number`);
                    }
                }
            });
            
            if (!isFormValid) {
                e.preventDefault();
                Silicon4Message.error('validation-failed');
            }
        });
    }
};

// Grid initialization and behavior
window.Silicon4Grid = {
    /**
     * Initialize grid with configuration
     * @param {Object} config - Configuration object
     */
    initializeGrid: function(config) {
        const {
            tableSelector,
            responsive = true
        } = config;

        const table = document.querySelector(tableSelector);
        if (!table) {
            console.warn(`[Silicon4Grid] Table not found: ${tableSelector}`);
                    return;
                }
        
        console.log(`[Silicon4Grid] Initializing grid: ${tableSelector}`);

        // Apply responsive behavior if enabled
        if (responsive) {
            this.makeResponsive(table);
        }

        // Column widths handled by CSS

        // Number formatting handled by CSS
    },

    /**
     * Make table responsive
     * @param {HTMLElement} table - Table element
     */
    makeResponsive: function(table) {
        // Add responsive wrapper if not present
        if (!table.parentElement.classList.contains('overflow-x-auto')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'overflow-x-auto';
            table.parentElement.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    }
};

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
                Silicon4Message.error('operation-failed');
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

};

// Initialize components when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Silicon4Components] Initializing...');
    
    // Initialize document number generator if on form page
    if (document.getElementById('id_DocumentTypeId')) {
        DocumentNumberGenerator.initDocumentTypeHandler('id_DocumentTypeId', 'id_DocumentNo');
    }
    
    // Number formatting handled by CSS
    
    console.log('[Silicon4Components] Initialization complete');
});

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
        newConfirmButton.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent default form submission
            e.stopPropagation();
            
            // Show loading state
            newConfirmButton.disabled = true;
            newConfirmButton.textContent = 'Deleting...';
            
            // Get CSRF token (try meta tag first, then form input as fallback)
            let csrfToken = document.querySelector('meta[name="csrf-token"]');
            let csrfValue = '';
            
            if (csrfToken) {
                csrfValue = csrfToken.getAttribute('content');
            } else {
                // Fallback to form input
                const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
                if (csrfInput) {
                    csrfValue = csrfInput.value;
                }
            }
            
            if (!csrfValue) {
                console.error('CSRF token not found');
                Silicon4Message.error('permission-denied');
                newConfirmButton.disabled = false;
                newConfirmButton.textContent = 'Delete';
                return;
            }
            
            // Make delete request
            fetch(deleteUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfValue,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'csrfmiddlewaretoken=' + encodeURIComponent(csrfValue)
            })
            .then(response => {
                if (response.ok) {
                    Silicon4Message.success('item-deleted');
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
                Silicon4Message.error('delete-failed');
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
