/**
 * Silicon4 Simple Soft Delete
 * Lightweight soft delete functionality using JavaScript and API
 */

class Silicon4SoftDelete {
    constructor() {
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

        // Handle delete form submission
        document.addEventListener('submit', (e) => {
            if (e.target.matches('#delete-form')) {
                e.preventDefault();
                this.handleDeleteSubmit(e.target);
            }
        });
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
        const itemId = form.dataset.itemId;
        const itemName = form.dataset.itemName;
        const deleteUrl = form.action;
        
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
            
            const result = await response.json();
            
            if (result.success) {
                // Show success message
                this.showSuccessMessage(`"${itemName}" Амжилттай устгагдлаа.`);
                
                // Remove item from list or refresh
                this.removeItemFromList(itemId);
                
                // Close modal
                this.closeModal();
                
                // Check if we're on cash document master detail page
                const isCashDocumentPage = window.location.pathname.includes('/cashdocuments/') && 
                                         document.getElementById('cash-document-container') &&
                                         typeof allDocumentsData !== 'undefined';
                
                if (isCashDocumentPage) {
                    // Optimized refresh for cash document page - no full page reload
                    // Remove from allDocumentsData array
                    if (Array.isArray(allDocumentsData)) {
                        allDocumentsData = allDocumentsData.filter(doc => doc.DocumentId != itemId);
                    }
                    
                    // Remove row from DOM
                    const row = document.querySelector(`tr[data-document-id="${itemId}"]`);
                    if (row) {
                        row.remove();
                    }
                    
                    // Clear detail grid if this document was selected
                    const detailContainer = document.getElementById('detail-grid-container');
                    if (detailContainer) {
                        const urlParams = new URLSearchParams(window.location.search);
                        const selectedDocumentId = urlParams.get('selected_document');
                        if (selectedDocumentId == itemId) {
                            detailContainer.innerHTML = '';
                            // Remove from URL
                            const currentUrl = new URL(window.location);
                            currentUrl.searchParams.delete('selected_document');
                            window.history.replaceState({}, '', currentUrl.toString());
                        }
                    }
                    
                    // Re-apply filters and pagination (fast - just client-side filtering)
                    if (typeof applyFrontendFilter === 'function') {
                        // Reset to page 1 if current page becomes empty
                        const startIndex = (currentPage - 1) * pageSize;
                        const remainingAfterDelete = filteredData ? filteredData.filter(doc => doc.DocumentId != itemId).length : 0;
                        if (remainingAfterDelete <= startIndex && currentPage > 1) {
                            currentPage = Math.max(1, Math.ceil(remainingAfterDelete / pageSize));
                        }
                        applyFrontendFilter();
                    }
                } else {
                    // For other pages, use the existing reload behavior
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                }
                
            } else {
                this.showErrorMessage(result.message || 'Error deleting item');
            }
            
        } catch (error) {
            console.error('Delete error:', error);
            this.showErrorMessage('Network error occurred while deleting item');
        } finally {
            this.showLoading(false);
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
