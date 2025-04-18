// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}

// Alert functions
function showAlert(message, type) {
    const alertBox = document.createElement('div');
    alertBox.className = `alert alert-${type} alert-dismissible fade show`;
    alertBox.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertBox);
    setTimeout(() => {
        if (alertBox) {
            alertBox.remove();
        }
    }, 3000);
}

function handleApiError(error) {
    console.error('API Error:', error);
    showAlert('An error occurred. Please try again.', 'danger');
} 