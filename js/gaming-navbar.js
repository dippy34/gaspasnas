// Gaming Navbar Component
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const currentPage = currentPath.split('/').pop() || 'index.html';
    
    const navbarHTML = `
        <nav class="gaming-navbar">
            <a href="/index.html" class="logo">NOVA HUB</a>
            <ul class="nav-links">
                <li><a href="/index.html" class="${currentPage === 'index.html' ? 'active' : ''}">Home</a></li>
                <li><a href="/projects.html" class="${currentPage === 'projects.html' ? 'active' : ''}">Games</a></li>
                <li><a href="/apps.html" class="${currentPage === 'apps.html' ? 'active' : ''}">Apps</a></li>
                <li><a href="/bookmarklets.html" class="${currentPage === 'bookmarklets.html' ? 'active' : ''}">Bookmarklets</a></li>
                <li><a href="/settings.html" class="${currentPage === 'settings.html' ? 'active' : ''}">Settings</a></li>
                <li><a href="/about.html" class="${currentPage === 'about.html' ? 'active' : ''}">Hacks</a></li>
            </ul>
        </nav>
    `;
    
    // Insert navbar at the beginning of body
    document.body.insertAdjacentHTML('afterbegin', navbarHTML);
    
    // Note: Theme class is managed by main.js based on selected theme
    // Don't force add gaming-theme here, let main.js handle it
    
    // Add panic button if enabled
    if (typeof window.updatePanicButton === 'function') {
        window.updatePanicButton();
    }
});

// Panic Button Functions (for all pages)
window.updatePanicButton = function() {
    const enabled = localStorage.getItem('selenite.panicEnabled') === 'true';
    
    if (enabled) {
        // Check if button already exists
        let panicButton = document.getElementById('panicButton');
        
        if (!panicButton) {
            // Create panic button
            panicButton = document.createElement('button');
            panicButton.id = 'panicButton';
            panicButton.className = 'panic-button';
            panicButton.innerHTML = '🚨';
            panicButton.onclick = window.activatePanic;
            document.body.appendChild(panicButton);
        } else {
            panicButton.style.display = 'block';
        }
    } else {
        const panicButton = document.getElementById('panicButton');
        if (panicButton) {
            panicButton.style.display = 'none';
        }
    }
};

window.activatePanic = function() {
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    
    const panicUrl = localStorage.getItem('selenite.panicUrl') || getCookie('panicurl') || 'https://google.com';
    window.location.href = panicUrl;
};


