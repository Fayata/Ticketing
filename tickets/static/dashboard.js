// Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');

    if (sidebarToggle && sidebar) {
        // Load saved sidebar state
        const sidebarState = localStorage.getItem('sidebarCollapsed');
        if (sidebarState === 'true') {
            sidebar.classList.add('collapsed');
        }

        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });
    }

    // Mobile Menu Toggle
    if (mobileMenuToggle && sidebar) {
        mobileMenuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('mobile-open');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                if (!sidebar.contains(e.target) && !mobileMenuToggle.contains(e.target)) {
                    sidebar.classList.remove('mobile-open');
                }
            }
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
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

    // Auto-dismiss alerts/notifications
    const alerts = document.querySelectorAll('.alert, .notification');
    alerts.forEach(alert => {
        if (alert.dataset.autoDismiss !== 'false') {
            setTimeout(() => {
                alert.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-10px)';
                setTimeout(() => alert.remove(), 300);
            }, 5000);
        }
    });

    // Ticket item click handler
    const ticketItems = document.querySelectorAll('.ticket-item');
    ticketItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Don't navigate if clicking on a link or button inside
            if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON') {
                return;
            }
            const ticketId = this.dataset.ticketId;
            if (ticketId) {
                window.location.href = `/tiket/${ticketId}/`;
            }
        });
    });

    // Notification button
    const notificationBtn = document.getElementById('notificationBtn');
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function() {
            // TODO: Implement notification panel
            alert('Fitur notifikasi akan segera hadir!');
        });
    }

    // Add animation to stats on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s ease-out forwards';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe all cards and stats
    document.querySelectorAll('.stat-card, .card, .quick-action-btn').forEach(el => {
        observer.observe(el);
    });

    // Add CSS animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    document.head.appendChild(style);

    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            if (window.innerWidth > 768) {
                sidebar.classList.remove('mobile-open');
            }
        }, 250);
    });

    // Prevent default on empty href links
    document.querySelectorAll('a[href="#"]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
        });
    });

    // Format dates to relative time
    const timeElements = document.querySelectorAll('[data-timestamp]');
    timeElements.forEach(el => {
        const timestamp = el.dataset.timestamp;
        if (timestamp) {
            el.textContent = getRelativeTime(new Date(timestamp));
        }
    });

    // Add loading state to buttons
    const actionButtons = document.querySelectorAll('.btn-primary, .btn-white, .btn-purple');
    actionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (this.type === 'submit' || this.dataset.loading === 'true') {
                this.disabled = true;
                const originalText = this.innerHTML;
                this.innerHTML = '<span class="spinner"></span> Loading...';
                
                // Re-enable after 3 seconds (adjust based on actual action)
                setTimeout(() => {
                    this.disabled = false;
                    this.innerHTML = originalText;
                }, 3000);
            }
        });
    });
});

// Helper function to get relative time
function getRelativeTime(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
        return 'Baru saja';
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `${minutes} menit lalu`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours} jam lalu`;
    } else if (diffInSeconds < 604800) {
        const days = Math.floor(diffInSeconds / 86400);
        return `${days} hari lalu`;
    } else {
        return date.toLocaleDateString('id-ID', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    }
}

// Helper function to show toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        padding: 1rem 1.5rem;
        background: white;
        border-radius: 0.5rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        z-index: 1000;
        animation: slideInRight 0.3s ease-out;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Export functions for use in other scripts
window.dashboardHelpers = {
    showToast,
    getRelativeTime
};