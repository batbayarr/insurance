/**
 * Generic Message Modal
 * Shows error, success, warning, or info messages in a modal
 * Reuses existing delete modal styling
 */

console.log('Message modal script loaded');

// Make sure function is in global scope
window.showMessageModal = function(message, type = 'error', title = null) {
    console.log('showMessageModal called with:', {message, type, title});
    
    const modal = document.getElementById('message-modal');
    
    // Fallback to alert if modal not found
    if (!modal) {
        console.warn('Message modal not found, falling back to alert');
        alert(message);
        return;
    }
    
    // Get elements
    const iconContainer = document.getElementById('message-modal-icon-container');
    const titleElement = document.getElementById('message-modal-title');
    const textElement = document.getElementById('message-modal-text');
    const okButton = document.getElementById('message-modal-ok-btn');
    
    // Hide all icons
    const icons = {
        error: document.getElementById('message-modal-icon-error'),
        success: document.getElementById('message-modal-icon-success'),
        warning: document.getElementById('message-modal-icon-warning'),
        info: document.getElementById('message-modal-icon-info')
    };
    
    Object.values(icons).forEach(icon => {
        if (icon) icon.classList.add('hidden');
    });
    
    // Set styles based on type
    const typeConfig = {
        error: {
            bgClass: 'bg-red-100',
            btnClass: 'bg-red-500 hover:bg-red-600 focus:ring-red-300',
            defaultTitle: 'Алдаа'  // Error in Mongolian
        },
        success: {
            bgClass: 'bg-green-100',
            btnClass: 'bg-green-500 hover:bg-green-600 focus:ring-green-300',
            defaultTitle: 'Амжилттай'  // Success in Mongolian
        },
        warning: {
            bgClass: 'bg-yellow-100',
            btnClass: 'bg-yellow-500 hover:bg-yellow-600 focus:ring-yellow-300',
            defaultTitle: 'Анхааруулга'  // Warning in Mongolian
        },
        info: {
            bgClass: 'bg-blue-100',
            btnClass: 'bg-blue-500 hover:bg-blue-600 focus:ring-blue-300',
            defaultTitle: 'Мэдээлэл'  // Info in Mongolian
        }
    };
    
    const config = typeConfig[type] || typeConfig.error;
    
    // Update icon container background
    if (iconContainer) {
        iconContainer.className = `mx-auto flex items-center justify-center h-12 w-12 rounded-full ${config.bgClass}`;
    }
    
    // Show appropriate icon
    if (icons[type]) {
        icons[type].classList.remove('hidden');
    }
    
    // Update title
    if (titleElement) {
        titleElement.textContent = title || config.defaultTitle;
    }
    
    // Update message
    if (textElement) {
        textElement.textContent = message;
    }
    
    // Update button style
    if (okButton) {
        okButton.className = `px-4 py-2 ${config.btnClass} text-white text-base font-medium rounded-md w-24 focus:outline-none focus:ring-2`;
    }
    
    // Show modal
    modal.classList.remove('hidden');
    
    // Focus on OK button for accessibility
    if (okButton) {
        setTimeout(() => okButton.focus(), 100);
    }
}

/**
 * Hide the message modal
 */
function hideMessageModal() {
    const modal = document.getElementById('message-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

/**
 * Convenience functions for specific message types
 */
window.showError = function(message, title) {
    window.showMessageModal(message, 'error', title);
}

window.showSuccess = function(message, title) {
    window.showMessageModal(message, 'success', title);
}

window.showWarning = function(message, title) {
    window.showMessageModal(message, 'warning', title);
}

window.showInfo = function(message, title) {
    window.showMessageModal(message, 'info', title);
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    const modal = document.getElementById('message-modal');
    if (modal && e.target === modal) {
        modal.classList.add('hidden');
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        hideMessageModal();
    }
});

