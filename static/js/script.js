document.addEventListener('DOMContentLoaded', function() {
    // Toggle sidebar on mobile
    const sidebar = document.querySelector('.sidebar');
    const menuToggle = document.querySelector('.menu-toggle');
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    
    menuToggle?.addEventListener('click', function() {
        sidebar.classList.add('active');
    });
    
    sidebarToggle?.addEventListener('click', function() {
        sidebar.classList.remove('active');
    });

    // Quotation submenu toggle
    const quotationMenu = document.getElementById('quotation-menu');
    if (quotationMenu) {
        quotationMenu.addEventListener('click', function(e) {
            e.preventDefault();
            const submenu = document.getElementById('quotation-submenu');
            const chevron = this.querySelector('.chevron');
            
            this.classList.toggle('active');
            submenu.classList.toggle('show');
            chevron.style.transform = submenu.classList.contains('show') ? 'rotate(180deg)' : 'rotate(0)';
        });
    }

    // Active menu item highlighting
    const navLinks = document.querySelectorAll('.nav-link:not(#quotation-menu)');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Remove active class from all links except submenu items
            document.querySelectorAll('.nav-menu > .nav-item > .nav-link').forEach(l => {
                if (!l.closest('.submenu')) {
                    l.classList.remove('active');
                }
            });
            this.classList.add('active');
        });
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 992) {
            if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        }
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const toggles = document.querySelectorAll('.toggle-submenu');

    toggles.forEach(toggle => {
        toggle.addEventListener('click', function () {
            const submenu = this.nextElementSibling;
            const chevron = this.querySelector('.chevron');
            submenu.classList.toggle('show');
            chevron.classList.toggle('rotate');
        });
    });
});

