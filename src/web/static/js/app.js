// Common JavaScript utilities for CryptoAI Trading Bot

// Global utilities object
window.CryptoAI = {
    // Configuration
    config: {
        refreshInterval: 30000, // 30 seconds
        chartColors: {
            primary: '#17a2b8',
            success: '#28a745',
            danger: '#dc3545',
            warning: '#ffc107',
            info: '#6f42c1',
            light: '#f8f9fa',
            dark: '#343a40'
        },
        dateFormats: {
            short: { month: 'short', day: 'numeric' },
            medium: { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' },
            long: { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }
        }
    },

    // Utility functions
    utils: {
        // Format currency with proper locale
        formatCurrency: function(value, currency = 'USD', locale = 'pt-BR') {
            if (value === null || value === undefined || isNaN(value)) {
                return '$0.00';
            }
            return new Intl.NumberFormat(locale, {
                style: 'currency',
                currency: currency,
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(value);
        },

        // Format percentage with proper locale
        formatPercentage: function(value, locale = 'pt-BR', decimals = 2) {
            if (value === null || value === undefined || isNaN(value)) {
                return '0.00%';
            }
            return new Intl.NumberFormat(locale, {
                style: 'percent',
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            }).format(value / 100);
        },

        // Format large numbers with suffixes
        formatNumber: function(value, locale = 'pt-BR') {
            if (value === null || value === undefined || isNaN(value)) {
                return '0';
            }
            
            const abs = Math.abs(value);
            if (abs >= 1e9) {
                return (value / 1e9).toFixed(1) + 'B';
            } else if (abs >= 1e6) {
                return (value / 1e6).toFixed(1) + 'M';
            } else if (abs >= 1e3) {
                return (value / 1e3).toFixed(1) + 'K';
            }
            
            return new Intl.NumberFormat(locale).format(value);
        },

        // Format date/time with various options
        formatDateTime: function(isoString, format = 'medium') {
            if (!isoString) return '-';
            
            const date = new Date(isoString);
            const options = this.parent.config.dateFormats[format] || this.parent.config.dateFormats.medium;
            
            return date.toLocaleString('pt-BR', options);
        },

        // Calculate time difference in human readable format
        formatTimeDifference: function(startTime, endTime = null) {
            const start = new Date(startTime);
            const end = endTime ? new Date(endTime) : new Date();
            const diffMs = end - start;
            
            const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diffMs % (1000 * 60)) / 1000);
            
            if (days > 0) {
                return `${days}d ${hours}h ${minutes}m`;
            } else if (hours > 0) {
                return `${hours}h ${minutes}m`;
            } else if (minutes > 0) {
                return `${minutes}m ${seconds}s`;
            } else {
                return `${seconds}s`;
            }
        },

        // Debounce function to limit function calls
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        // Throttle function to limit function calls
        throttle: function(func, limit) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        // Copy text to clipboard
        copyToClipboard: function(text) {
            if (navigator.clipboard && window.isSecureContext) {
                return navigator.clipboard.writeText(text);
            } else {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.opacity = '0';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                
                try {
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    return Promise.resolve();
                } catch (err) {
                    document.body.removeChild(textArea);
                    return Promise.reject(err);
                }
            }
        },

        // Generate random ID
        generateId: function(prefix = 'id') {
            return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        },

        // Validate email format
        isValidEmail: function(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        },

        // Get query parameter value
        getQueryParam: function(name) {
            const urlParams = new URLSearchParams(window.location.search);
            return urlParams.get(name);
        },

        // Set query parameter
        setQueryParam: function(name, value) {
            const url = new URL(window.location);
            url.searchParams.set(name, value);
            window.history.replaceState({}, '', url);
        }
    },

    // Chart utilities
    charts: {
        // Default chart options
        getDefaultOptions: function() {
            return {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffffff'
                        }
                    },
                    tooltip: {
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        borderColor: 'rgba(255, 255, 255, 0.2)',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#ffffff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    y: {
                        ticks: {
                            color: '#ffffff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            };
        },

        // Create gradient for charts
        createGradient: function(ctx, color1, color2) {
            const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
            gradient.addColorStop(0, color1);
            gradient.addColorStop(1, color2);
            return gradient;
        },

        // Update chart data smoothly
        updateChart: function(chart, newData, animate = true) {
            if (!chart || !newData) return;
            
            chart.data = newData;
            chart.update(animate ? 'active' : 'none');
        },

        // Destroy chart safely
        destroyChart: function(chart) {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        }
    },

    // Storage utilities
    storage: {
        // Local storage with JSON support
        set: function(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (e) {
                console.error('Error saving to localStorage:', e);
                return false;
            }
        },

        get: function(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                console.error('Error reading from localStorage:', e);
                return defaultValue;
            }
        },

        remove: function(key) {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (e) {
                console.error('Error removing from localStorage:', e);
                return false;
            }
        },

        clear: function() {
            try {
                localStorage.clear();
                return true;
            } catch (e) {
                console.error('Error clearing localStorage:', e);
                return false;
            }
        }
    },

    // API utilities
    api: {
        // Default fetch options
        defaultOptions: {
            headers: {
                'Content-Type': 'application/json'
            }
        },

        // GET request
        get: function(url, options = {}) {
            return fetch(url, {
                method: 'GET',
                ...this.defaultOptions,
                ...options
            }).then(this.handleResponse);
        },

        // POST request
        post: function(url, data = {}, options = {}) {
            return fetch(url, {
                method: 'POST',
                body: JSON.stringify(data),
                ...this.defaultOptions,
                ...options
            }).then(this.handleResponse);
        },

        // PUT request
        put: function(url, data = {}, options = {}) {
            return fetch(url, {
                method: 'PUT',
                body: JSON.stringify(data),
                ...this.defaultOptions,
                ...options
            }).then(this.handleResponse);
        },

        // DELETE request
        delete: function(url, options = {}) {
            return fetch(url, {
                method: 'DELETE',
                ...this.defaultOptions,
                ...options
            }).then(this.handleResponse);
        },

        // Handle response
        handleResponse: function(response) {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return response.json();
            }
            return response.text();
        }
    },

    // Notification utilities
    notifications: {
        // Show toast notification
        show: function(type, message, duration = 5000) {
            const alertsContainer = document.getElementById('alertsContainer');
            if (!alertsContainer) return;

            const alertId = CryptoAI.utils.generateId('alert');
            const alertColors = {
                'success': 'alert-success',
                'error': 'alert-danger',
                'warning': 'alert-warning',
                'info': 'alert-info'
            };

            const alertHTML = `
                <div id="${alertId}" class="alert ${alertColors[type]} alert-dismissible fade show" role="alert">
                    <strong>${type.charAt(0).toUpperCase() + type.slice(1)}:</strong> ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;

            alertsContainer.insertAdjacentHTML('beforeend', alertHTML);

            // Auto remove after duration
            setTimeout(() => {
                const alert = document.getElementById(alertId);
                if (alert) {
                    alert.remove();
                }
            }, duration);
        },

        success: function(message, duration) {
            this.show('success', message, duration);
        },

        error: function(message, duration) {
            this.show('error', message, duration);
        },

        warning: function(message, duration) {
            this.show('warning', message, duration);
        },

        info: function(message, duration) {
            this.show('info', message, duration);
        }
    },

    // Loading utilities
    loading: {
        // Show loading state
        show: function(element, message = 'Carregando...') {
            if (typeof element === 'string') {
                element = document.getElementById(element);
            }
            
            if (!element) return;

            const loadingHTML = `
                <div class="text-center text-muted py-4">
                    <div class="spinner-glow mb-3"></div>
                    <p>${message}</p>
                </div>
            `;

            element.innerHTML = loadingHTML;
        },

        // Hide loading state
        hide: function(element) {
            if (typeof element === 'string') {
                element = document.getElementById(element);
            }
            
            if (!element) return;
            
            const spinner = element.querySelector('.spinner-glow');
            if (spinner) {
                spinner.parentElement.remove();
            }
        },

        // Show button loading state
        showButton: function(button, text = 'Processando...') {
            if (typeof button === 'string') {
                button = document.getElementById(button);
            }
            
            if (!button) return;

            button.disabled = true;
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = `<span class="spinner-glow me-2"></span>${text}`;
        },

        // Hide button loading state
        hideButton: function(button) {
            if (typeof button === 'string') {
                button = document.getElementById(button);
            }
            
            if (!button) return;

            button.disabled = false;
            if (button.dataset.originalText) {
                button.innerHTML = button.dataset.originalText;
                delete button.dataset.originalText;
            }
        }
    },

    // Validation utilities
    validation: {
        // Validate number input
        isValidNumber: function(value, min = null, max = null) {
            const num = parseFloat(value);
            if (isNaN(num)) return false;
            if (min !== null && num < min) return false;
            if (max !== null && num > max) return false;
            return true;
        },

        // Validate required field
        isRequired: function(value) {
            return value !== null && value !== undefined && value.toString().trim() !== '';
        },

        // Validate form
        validateForm: function(formElement) {
            const errors = [];
            const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
            
            inputs.forEach(input => {
                if (!this.isRequired(input.value)) {
                    errors.push(`${input.name || input.id} é obrigatório`);
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
                
                // Validate number inputs
                if (input.type === 'number' && input.value) {
                    const min = input.min ? parseFloat(input.min) : null;
                    const max = input.max ? parseFloat(input.max) : null;
                    
                    if (!this.isValidNumber(input.value, min, max)) {
                        errors.push(`${input.name || input.id} deve ser um número válido`);
                        input.classList.add('is-invalid');
                    }
                }
                
                // Validate email inputs
                if (input.type === 'email' && input.value) {
                    if (!CryptoAI.utils.isValidEmail(input.value)) {
                        errors.push(`${input.name || input.id} deve ser um email válido`);
                        input.classList.add('is-invalid');
                    }
                }
            });
            
            return {
                isValid: errors.length === 0,
                errors: errors
            };
        }
    },

    // Animation utilities
    animations: {
        // Fade in element
        fadeIn: function(element, duration = 300) {
            if (typeof element === 'string') {
                element = document.getElementById(element);
            }
            
            if (!element) return;

            element.style.opacity = '0';
            element.style.display = 'block';
            
            let opacity = 0;
            const timer = setInterval(() => {
                opacity += 50 / duration;
                element.style.opacity = opacity;
                
                if (opacity >= 1) {
                    clearInterval(timer);
                    element.style.opacity = '1';
                }
            }, 50);
        },

        // Fade out element
        fadeOut: function(element, duration = 300) {
            if (typeof element === 'string') {
                element = document.getElementById(element);
            }
            
            if (!element) return;

            let opacity = 1;
            const timer = setInterval(() => {
                opacity -= 50 / duration;
                element.style.opacity = opacity;
                
                if (opacity <= 0) {
                    clearInterval(timer);
                    element.style.opacity = '0';
                    element.style.display = 'none';
                }
            }, 50);
        },

        // Slide up element
        slideUp: function(element, duration = 300) {
            if (typeof element === 'string') {
                element = document.getElementById(element);
            }
            
            if (!element) return;

            element.style.transitionProperty = 'height, margin, padding';
            element.style.transitionDuration = duration + 'ms';
            element.style.height = element.offsetHeight + 'px';
            element.offsetHeight; // Trigger reflow
            element.style.overflow = 'hidden';
            element.style.height = '0';
            element.style.paddingTop = '0';
            element.style.paddingBottom = '0';
            element.style.marginTop = '0';
            element.style.marginBottom = '0';
            
            setTimeout(() => {
                element.style.display = 'none';
                element.style.removeProperty('height');
                element.style.removeProperty('padding-top');
                element.style.removeProperty('padding-bottom');
                element.style.removeProperty('margin-top');
                element.style.removeProperty('margin-bottom');
                element.style.removeProperty('overflow');
                element.style.removeProperty('transition-duration');
                element.style.removeProperty('transition-property');
            }, duration);
        }
    }
};

// Set up parent references for utils
CryptoAI.utils.parent = CryptoAI;

// Global convenience functions for backward compatibility
window.formatCurrency = CryptoAI.utils.formatCurrency;
window.formatPercentage = CryptoAI.utils.formatPercentage;
window.formatDateTime = CryptoAI.utils.formatDateTime;
window.showAlert = CryptoAI.notifications.show;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth scrolling to all internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading states to forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                CryptoAI.loading.showButton(submitButton);
            }
        });
    });

    // Add tooltips to elements with title attribute
    document.querySelectorAll('[title]').forEach(element => {
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            new bootstrap.Tooltip(element);
        }
    });

    // Console welcome message
    console.log('%c🤖 CryptoAI Trading Bot', 'color: #17a2b8; font-size: 16px; font-weight: bold;');
    console.log('%cInterface carregada com sucesso!', 'color: #28a745; font-size: 12px;');
});
