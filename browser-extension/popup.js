// Popup script for Mergen extension

// Browser API polyfill - Firefox uses 'browser', Chrome uses 'chrome'
if (typeof browser === 'undefined') {
    globalThis.browser = chrome;
}

// Get and display extension ID
const extensionId = browser.runtime.id;
document.getElementById('extension-id').value = extensionId;

// Copy Extension ID to clipboard
document.getElementById('copy-btn').addEventListener('click', async () => {
    const copyBtn = document.getElementById('copy-btn');

    try {
        await navigator.clipboard.writeText(extensionId);
        copyBtn.textContent = '✅ Copied!';
        copyBtn.classList.add('copied');

        setTimeout(() => {
            copyBtn.textContent = '📋 Copy';
            copyBtn.classList.remove('copied');
        }, 2000);
    } catch (err) {
        console.error('Failed to copy:', err);
        // Fallback for older browsers
        document.getElementById('extension-id').select();
        document.execCommand('copy');
        copyBtn.textContent = '✅ Copied!';
    }
});

// Test connection to native host
async function checkConnection() {
    const statusIcon = document.getElementById('status-icon');
    const statusText = document.getElementById('status-text');

    // Set checking state
    statusIcon.textContent = '🔄';
    statusText.textContent = 'Checking connection...';
    statusText.className = 'status-text checking';

    // Send test message to background
    browser.runtime.sendMessage({ action: 'test_connection' }, (response) => {
        if (browser.runtime.lastError || !response) {
            // Connection failed
            statusIcon.textContent = '🔴';
            statusText.textContent = 'Disconnected - Please register in Mergen';
            statusText.className = 'status-text disconnected';
        } else if (response.error) {
            // Native host error
            statusIcon.textContent = '🔴';
            statusText.textContent = 'Mergen app not running';
            statusText.className = 'status-text disconnected';
        } else {
            // Connection successful
            statusIcon.textContent = '🟢';
            statusText.textContent = 'Connected to Mergen!';
            statusText.className = 'status-text connected';
        }
    });
}

// Test button
document.getElementById('test-btn').addEventListener('click', () => {
    checkConnection();
});

// Auto-check on popup open
checkConnection();

// Re-check every 3 seconds while popup is open
setInterval(checkConnection, 3000);
