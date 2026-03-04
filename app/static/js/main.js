// Main JavaScript for JobRecommender Portal

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeAnimations();
    initializeFormValidation();
    initializeTooltips();
    initializeAlerts();
});

// Smooth scroll animations
function initializeAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate__animated', 'animate__fadeInUp');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.card, .feature-card, .category-card').forEach(el => {
        observer.observe(el);
    });
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Auto-dismiss alerts
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

// Save job functionality
function saveJob(jobId, button) {
    fetch(`/jobs/${jobId}/save`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.saved) {
            button.innerHTML = '<i class="fas fa-heart"></i> Saved';
            button.classList.remove('btn-outline-danger');
            button.classList.add('btn-danger');
            showToast('Success', data.message, 'success');
        } else {
            button.innerHTML = '<i class="far fa-heart"></i> Save Job';
            button.classList.remove('btn-danger');
            button.classList.add('btn-outline-danger');
            showToast('Info', data.message, 'info');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error', 'Failed to save job', 'danger');
    });
}

// Show toast notification
function showToast(title, message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${title}:</strong> ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// Loading spinner
function showLoading(element) {
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    spinner.id = 'loadingSpinner';
    element.appendChild(spinner);
}

function hideLoading() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.remove();
    }
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Success', 'Copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showToast('Error', 'Failed to copy', 'danger');
    });
}

// Format date
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// Confirm action
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Export functions for global use
window.saveJob = saveJob;
window.showToast = showToast;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.copyToClipboard = copyToClipboard;
window.formatDate = formatDate;
window.confirmAction = confirmAction;
