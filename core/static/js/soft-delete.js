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
            modalText.textContent = `Are you sure you want to delete "${itemName}"? The item will be marked as deleted and hidden from the list.`;
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
                this.showSuccessMessage(`"${itemName}" has been deleted successfully.`);
                
                // Remove item from list or refresh
                this.removeItemFromList(itemId);
                
                // Close modal
                this.closeModal();
                
                // Refresh the list after a short delay
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
                
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
        // Use Silicon4Message for success messages
        if (typeof Silicon4Message !== 'undefined') {
            Silicon4Message.success(message);
        } else {
            alert(message);
        }
    }

    showErrorMessage(message) {
        // Use Silicon4Message for error messages
        if (typeof Silicon4Message !== 'undefined') {
            Silicon4Message.error(message);
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
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
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
