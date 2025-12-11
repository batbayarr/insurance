/**
 * Silicon4 Simple Soft Delete
 * Lightweight soft delete functionality using JavaScript and API
 */

class Silicon4SoftDelete {
    constructor() {
        this.isDeleting = false; // Flag to prevent concurrent delete operations
        this.filterClearTimeout = null; // Track timeout to clear it if needed
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Handle delete button clicks
        document.addEventListener('click', (e) => {
            // Check if the clicked element or its parent has data-soft-delete
            const deleteButton = e.target.closest('[data-soft-delete]');
            if (deleteButton) {
                e.preventDefault();
                e.stopPropagation();
                this.handleDeleteClick(deleteButton);
            }
        });

        // Handle delete form submission - use capture phase and prevent ALL propagation
        document.addEventListener('submit', (e) => {
            if (e.target.matches('#delete-form')) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                // Prevent any default browser behavior
                if (e.cancelable) {
                    e.preventDefault();
                }
                this.handleDeleteSubmit(e.target);
                return false;
            }
        }, true); // Use capture phase to catch it early
    }

    handleDeleteClick(button) {
        const itemId = button.dataset.itemId;
        const itemName = button.dataset.itemName || 'item';
        const deleteUrl = button.dataset.deleteUrl || button.href;
        
        // Show confirmation modal
        this.showDeleteModal(itemId, itemName, deleteUrl);
    }

    showDeleteModal(itemId, itemName, deleteUrl) {
        // Update modal content
        const modal = document.getElementById('delete-modal');
        const modalText = document.getElementById('delete-modal-text');
        const deleteForm = document.getElementById('delete-form');
        
        if (modalText) {
            modalText.textContent = `Та "${itemName}" устгахдаа итгэлтэй байна уу?.`;
        }
        
        if (deleteForm) {
            deleteForm.action = deleteUrl;
            deleteForm.dataset.itemId = itemId;
            deleteForm.dataset.itemName = itemName;
        }
        
        // Show modal
        if (modal) {
            modal.classList.remove('hidden');
        } else {
            console.error('Delete modal not found!');
        }
    }

    async handleDeleteSubmit(form) {
        // Prevent concurrent delete operations
        if (this.isDeleting) {
            return;
        }
        
        const itemId = form.dataset.itemId;
        const itemName = form.dataset.itemName;
        const deleteUrl = form.action;
        
        // Set flag IMMEDIATELY to prevent any filtering during delete
        const cashDocContainer = document.getElementById('cash-document-container');
        const pathIncludesCashDocs = window.location.pathname.includes('/cashdocuments/');
        
        // Clear any existing timeout from previous delete operations
        if (this.filterClearTimeout) {
            clearTimeout(this.filterClearTimeout);
            this.filterClearTimeout = null;
        }
        
        if (pathIncludesCashDocs && cashDocContainer) {
            window.skipFilterAfterDelete = true;
        }
        
        this.isDeleting = true;
        
        try {
            // Show loading state
            this.showLoading(true);
            
            // Make API call
            const response = await fetch(deleteUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    item_id: itemId,
                    item_name: itemName
                })
            });
            
            // Check if response is ok
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            // Clear loading state immediately (but don't close modal yet for cash docs)
            this.showLoading(false);
            
            if (result.success) {
                // Check if we're on cash document master detail page (cache DOM check)
                // Be very explicit to avoid false positives
                const cashDocContainer = document.getElementById('cash-document-container');
                const pathIncludesCashDocs = window.location.pathname.includes('/cashdocuments/');
                const hasAllDocumentsData = typeof allDocumentsData !== 'undefined' && Array.isArray(allDocumentsData);
                
                // CRITICAL: If we're on cashdocuments path, NEVER reload - always use instant delete
                // This prevents accidental reloads even if detection fails
                if (pathIncludesCashDocs && cashDocContainer) {
                    
                    // Set a flag to prevent applyFrontendFilter from re-rendering after delete
                    window.skipFilterAfterDelete = true;
                    
                    // Use instant delete even if allDocumentsData is not yet loaded
                    // This is safer than risking a reload
                    // Immediate DOM update - no delays
                    try {
                        // Single DOM query - cache the row
                        const row = document.querySelector(`tr[data-document-id="${itemId}"]`);
                        if (row) {
                            // Batch all style updates at once
                            row.style.cssText = 'opacity: 0.5; text-decoration: line-through; pointer-events: none; cursor: default;';
                            row.classList.add('deleted-row');
                            
                            // Hide action buttons (use for loop for better performance)
                            const actionButtons = row.querySelectorAll('button');
                            for (let i = 0; i < actionButtons.length; i++) {
                                actionButtons[i].style.display = 'none';
                            }
                            
                            // Update action cell - use textContent instead of innerHTML to avoid triggering observers
                            const actionCell = row.querySelector('td:last-child');
                            if (actionCell) {
                                // Clear existing content without using innerHTML
                                while (actionCell.firstChild) {
                                    actionCell.removeChild(actionCell.firstChild);
                                }
                                // Create and append new element
                                const deletedSpan = document.createElement('span');
                                deletedSpan.className = 'text-red-500 text-xs font-medium';
                                deletedSpan.textContent = '(Устгагдсан)';
                                actionCell.appendChild(deletedSpan);
                            }
                        }
                        
                        // Mark as deleted in data arrays (optimized with early exit)
                        const markAsDeleted = (arr) => {
                            if (Array.isArray(arr)) {
                                for (let i = 0; i < arr.length; i++) {
                                    if (arr[i].DocumentId == itemId) {
                                        arr[i].IsDelete = true;
                                        break; // Early exit
                                    }
                                }
                            }
                        };
                        
                        // Only mark in arrays if they exist
                        if (hasAllDocumentsData) {
                            markAsDeleted(allDocumentsData);
                            if (typeof filteredData !== 'undefined') {
                                markAsDeleted(filteredData);
                            }
                            if (typeof pageData !== 'undefined') {
                                markAsDeleted(pageData);
                            }
                        }
                        
                        // Skip detail container manipulation entirely - just mark row as deleted
                        // The detail grid will be cleared naturally when user selects another document
                        // Any manipulation of detail container might trigger observers or reloads
                    } catch (domError) {
                        console.error('Error updating DOM after delete:', domError);
                    }
                    
                    // Clear any existing timeout from previous delete operations
                    if (this.filterClearTimeout) {
                        clearTimeout(this.filterClearTimeout);
                        this.filterClearTimeout = null;
                    }
                    
                    // CRITICAL: If the deleted document has details loaded, clear selected_document from URL
                    // This prevents applyFrontendFilter from trying to reload details for deleted document
                        const urlParams = new URLSearchParams(window.location.search);
                        const selectedDocumentId = urlParams.get('selected_document');
                        if (selectedDocumentId == itemId) {
                        // Remove selected_document from URL to prevent reload triggers
                        urlParams.delete('selected_document');
                        const newUrl = urlParams.toString() 
                            ? `${window.location.pathname}?${urlParams.toString()}`
                            : window.location.pathname;
                            window.history.replaceState({}, '', newUrl);
                            
                            // Clear detail container
                        const detailContainer = document.getElementById('detail-grid-container');
                        if (detailContainer) {
                            detailContainer.innerHTML = '';
                        }
                    }
                    
                    // After delete, remove selected_document from URL and refresh data
                    this.filterClearTimeout = setTimeout(() => {
                        try {
                            // CRITICAL: Remove selected_document from URL FIRST before any refresh operations
                            const currentUrlParams = new URLSearchParams(window.location.search);
                            const hasSelectedDocument = currentUrlParams.has('selected_document');
                            
                            if (hasSelectedDocument) {
                                currentUrlParams.delete('selected_document');
                                const cleanUrl = currentUrlParams.toString() 
                                    ? `${window.location.pathname}?${currentUrlParams.toString()}`
                                    : window.location.pathname;
                                window.history.replaceState({}, '', cleanUrl);
                            }
                            
                            // Clear filters first (like the refresh button does)
                            if (typeof clearAllClientSideFilters === 'function') {
                                clearAllClientSideFilters(true); // Preserve selected_document (already cleared above)
                            }
                            
                            // Get date inputs and call fetchDocuments directly
                            const startDateInput = document.getElementById('start-date');
                            const endDateInput = document.getElementById('end-date');
                            
                            if (!startDateInput || !endDateInput) {
                                console.error('[SoftDelete] Cannot trigger refresh - date inputs not found!', {
                                    hasStartDate: !!startDateInput,
                                    hasEndDate: !!endDateInput
                                });
                                // Clear flag even on error
                                window.skipFilterAfterDelete = false;
                                this.filterClearTimeout = null;
                                return;
                            }
                            
                            const startDate = startDateInput.value;
                            const endDate = endDateInput.value;
                            
                            if (!startDate || !endDate) {
                                console.error('[SoftDelete] Date inputs are empty!', { startDate, endDate });
                                // Clear flag even on error
                                window.skipFilterAfterDelete = false;
                                this.filterClearTimeout = null;
                                return;
                            }
                            
                            // CRITICAL: Clear BOTH flags BEFORE calling fetchDocuments
                            // This ensures applyFrontendFilter can run when fetchDocuments completes
                            window.skipFilterAfterDelete = false;
                            if (window.Silicon4SoftDelete) {
                                window.Silicon4SoftDelete.isDeleting = false;
                            }
                            
                            // Directly call fetchDocuments (same as what the button does)
                            // fetchDocuments is defined in the global scope in cashdocument_master_detail.html
                            // CRITICAL: Pass null as third parameter to ensure it doesn't use selected_document
                            if (typeof fetchDocuments === 'function') {
                                // Explicitly pass null to prevent fetchDocuments from using selected_document
                                // Even though we removed it from URL, this ensures it's not used
                                const fetchPromise = fetchDocuments(startDate, endDate, null);
                                if (fetchPromise && typeof fetchPromise.then === 'function') {
                                    fetchPromise
                                        .catch((error) => {
                                            console.error('[SoftDelete] Error in fetchDocuments:', error);
                                            // Ensure flags are cleared on error so UI can recover
                                            window.skipFilterAfterDelete = false;
                                            if (window.Silicon4SoftDelete) {
                                                window.Silicon4SoftDelete.isDeleting = false;
                                            }
                                        });
                                }
                            } else {
                                console.error('[SoftDelete] fetchDocuments function not found! Trying button click...');
                                // Fallback: try clicking the button
                                const refreshButton = document.getElementById('apply-date-filter');
                                if (refreshButton) {
                                    refreshButton.click();
                                } else {
                                    console.error('[SoftDelete] Refresh button not found!');
                                    // Clear flag on error
                                    window.skipFilterAfterDelete = false;
                                }
                            }
                        } catch (error) {
                            console.error('[SoftDelete] Error during refresh:', error);
                        } finally {
                            // Clear the timeout reference
                            this.filterClearTimeout = null;
                        }
                    }, 200); // Small delay to ensure DOM updates are complete
                    
                    // Close modal AFTER refresh is set up (for cash document pages)
                    this.closeModal();
                    
                    // CRITICAL: Reset isDeleting flag BEFORE returning so applyFrontendFilter can run
                    // This ensures that when fetchDocuments completes and calls applyFrontendFilter,
                    // it won't be blocked by the isDeleting check
                    this.isDeleting = false;
                    return;
                }
                
                // Only reach here if NOT on cash document page
                    // For other pages, use the existing reload behavior
                this.removeItemFromList(itemId);
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                
            } else {
                console.error('Delete failed - result.success is false:', result);
                // Only show error message for non-cash document pages
                const cashDocContainer = document.getElementById('cash-document-container');
                const pathIncludesCashDocs = window.location.pathname.includes('/cashdocuments/');
                if (!(pathIncludesCashDocs && cashDocContainer)) {
                this.showErrorMessage(result.message || 'Error deleting item');
                }
            }
            
        } catch (error) {
            console.error('Delete error:', error);
            console.error('Error stack:', error.stack);
            this.showLoading(false);
            this.closeModal();
            // Only show error message for non-cash document pages
            const cashDocContainer = document.getElementById('cash-document-container');
            const pathIncludesCashDocs = window.location.pathname.includes('/cashdocuments/');
            if (!(pathIncludesCashDocs && cashDocContainer)) {
                this.showErrorMessage(`Network error occurred while deleting item: ${error.message}`);
            }
        } finally {
            // Always reset the flag and clear any pending timeouts
            this.isDeleting = false;
            if (this.filterClearTimeout) {
                clearTimeout(this.filterClearTimeout);
                this.filterClearTimeout = null;
            }
            // Also clear the skipFilterAfterDelete flag on error
            window.skipFilterAfterDelete = false;
        }
    }

    removeItemFromList(itemId) {
        // Try to remove the item from the current list
        const itemRow = document.querySelector(`[data-item-id="${itemId}"]`);
        if (itemRow) {
            itemRow.style.opacity = '0.5';
            itemRow.style.textDecoration = 'line-through';
            
            // Add deleted indicator
            const deletedIndicator = document.createElement('span');
            deletedIndicator.className = 'text-red-500 text-sm ml-2';
            deletedIndicator.textContent = '(Deleted)';
            itemRow.appendChild(deletedIndicator);
        }
    }

    showSuccessMessage(message) {
        // Use message modal for success messages
        if (typeof showMessageModal === 'function') {
            showMessageModal(message, 'success', 'Амжилттай');
        } else {
            alert(message);
        }
    }

    showErrorMessage(message) {
        // Use message modal for error messages
        if (typeof showMessageModal === 'function') {
            showMessageModal(message, 'error', 'Алдаа');
        } else {
            alert(message);
        }
    }

    showLoading(show) {
        const submitButton = document.querySelector('#delete-form button[type="submit"]');
        if (submitButton) {
            if (show) {
                submitButton.disabled = true;
                submitButton.textContent = 'Deleting...';
            } else {
                submitButton.disabled = false;
                submitButton.textContent = 'Delete';
            }
        }
    }

    closeModal() {
        const modal = document.getElementById('delete-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    getCSRFToken() {
        // Try meta tag first
        const token = document.querySelector('meta[name="csrf-token"]');
        if (token) {
            return token.getAttribute('content');
        }
        
        // Fallback to cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        // Last resort - try to get from form
        const form = document.querySelector('form');
        if (form) {
            const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
            if (csrfInput) {
                return csrfInput.value;
            }
        }
        
        console.warn('CSRF token not found');
        return '';
    }

    // Static method to close modal (for template onclick handlers)
    static closeModal() {
        const modal = document.getElementById('delete-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.Silicon4SoftDelete = new Silicon4SoftDelete();
});
