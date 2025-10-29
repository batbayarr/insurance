/**
 * Generic Period Lock Validation
 * Validates document date before form submission
 */

function validatePeriodLock(dateValue, callback) {
    if (!dateValue) {
        callback(false, ''); // No date, proceed
        return;
    }
    
    fetch(`/core/api/check-period-lock/?date=${dateValue}`)
        .then(response => response.json())
        .then(data => {
            callback(data.is_locked, data.message);
        })
        .catch(() => {
            callback(false, ''); // On error, allow submission
        });
}

function attachPeriodLockValidation(formSelector, dateInputSelector) {
    const form = document.querySelector(formSelector);
    const dateInput = document.querySelector(dateInputSelector);
    
    if (!form || !dateInput) return;
    
    let isValidating = false; // Flag to prevent multiple validations
    
    form.addEventListener('submit', function(e) {
        // If already validated, let it through
        if (isValidating) {
            return true;
        }
        
        e.preventDefault(); // Stop submission
        e.stopPropagation();
        
        const dateValue = dateInput.value;
        
        validatePeriodLock(dateValue, function(isLocked, message) {
            if (isLocked) {
                alert(message);
                dateInput.focus();
                isValidating = false; // Reset flag
            } else {
                // Not locked, allow submission
                isValidating = true; // Set flag to allow submission
                form.submit(); // Submit
            }
        });
    });
}

