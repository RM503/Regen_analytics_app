/* JS scripts used on landing page */
function hideMessages(selectors, delay=5000) {
    setTimeout(() => {
        selectors.forEach(selector => {
            const element = document.querySelector(selector);
            if (element) {
                element.style.display = 'none';
            }
        })
    }, delay);
}

// Call function
document.addEventListener('DOMContentLoaded', () => {
    hideMessages(['.error-message', '.success-message']);
});