// Main JavaScript file for Expense Tracker

// Function to format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Function to format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Function to show alert
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);

    // Auto dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => {
            alertDiv.remove();
        }, 150);
    }, 5000);
}

// Function to handle API errors
function handleApiError(error) {
    console.error('API Error:', error);
    showAlert('An error occurred. Please try again later.', 'danger');
}

// Function to check if user is logged in
function checkAuthStatus() {
    fetch('/api/auth/me')
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Not authenticated');
        })
        .then(data => {
            // User is logged in
            document.querySelectorAll('.auth-required').forEach(el => {
                el.classList.remove('d-none');
            });
            document.querySelectorAll('.auth-not-required').forEach(el => {
                el.classList.add('d-none');
            });

            // Update user info in navbar if it exists
            const userInfoEl = document.getElementById('userInfo');
            if (userInfoEl) {
                userInfoEl.textContent = data.name;
            }
        })
        .catch(error => {
            // User is not logged in
            document.querySelectorAll('.auth-required').forEach(el => {
                el.classList.add('d-none');
            });
            document.querySelectorAll('.auth-not-required').forEach(el => {
                el.classList.remove('d-none');
            });
        });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    // Check authentication status
    checkAuthStatus();

    // Add event listeners for forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            // Prevent default form submission
            e.preventDefault();

            // Get form data
            const formData = new FormData(form);
            const data = {};
            formData.forEach((value, key) => {
                data[key] = value;
            });

            // Get form action and method
            const action = form.getAttribute('action') || form.getAttribute('data-action');
            const method = form.getAttribute('method') || 'POST';

            if (!action) {
                console.error('Form has no action attribute');
                return;
            }

            // Send form data to API
            fetch(action, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showAlert(data.error, 'danger');
                    } else {
                        showAlert(data.message || 'Operation successful', 'success');

                        // Redirect if specified
                        if (data.redirect) {
                            window.location.href = data.redirect;
                        }
                    }
                })
                .catch(handleApiError);
        });
    });
}); 