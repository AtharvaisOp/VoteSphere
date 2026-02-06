// Theme Toggle Functionality
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    const htmlElement = document.documentElement;
    
    // Function to get system theme preference
    function getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    // Function to set theme
    function setTheme(theme) {
        htmlElement.setAttribute('data-theme', theme);
        // Only update checkbox if it exists (to avoid errors on pages without the toggle)
        if (themeToggle) {
            themeToggle.checked = (theme === 'dark');
        }
    }

    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');

    // Apply theme: functionality of system theme is used if no saved preference
    if (savedTheme) {
        setTheme(savedTheme);
    } else {
        setTheme(getSystemTheme());
    }
    
    // Theme toggle change handler
    if (themeToggle) {
        themeToggle.addEventListener('change', function() {
            const newTheme = this.checked ? 'dark' : 'light';
            setTheme(newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }

    // Listen for system theme changes
    // This allows the app to respond to OS theme changes if the user hasn't successfully overridden it
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            const newSystemTheme = e.matches ? 'dark' : 'light';
            setTheme(newSystemTheme);
        }
    });
});
