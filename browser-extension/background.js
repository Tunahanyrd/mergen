/**
 * Mergen Browser Extension - Auto-register with native host
 * No manual ID configuration needed!
 */

const MERGEN_HOST = 'com.tunahanyrd.mergen';

// Auto-register extension ID with native host on first install
chrome.runtime.onInstalled.addListener(async (details) => {
    console.log('[MERGEN] Extension installed/updated');

    // Auto-register this extension ID with native host
    await registerWithNativeHost();

    // Create context menu
    chrome.contextMenus.create({
        id: 'download-with-mergen',
        title: '📥 Download with Mergen',
        contexts: ['page', 'link', 'video', 'audio']
    });
});

/**
 * Auto-register extension ID with native host (IDM-style)
 */
async function registerWithNativeHost() {
    try {
        const extensionId = chrome.runtime.id;
        console.log('[MERGEN] Auto-registering extension ID:', extensionId);

        const response = await chrome.runtime.sendNativeMessage(MERGEN_HOST, {
            action: 'register_extension',
            extensionId: extensionId
        });

        if (response?.success) {
            console.log('[MERGEN] ✅ Extension registered with native host');
        } else {
            console.warn('[MERGEN] ⚠️ Registration response:', response);
        }
    } catch (err) {
        console.warn('[MERGEN] Auto-registration failed (this is OK on first install):', err.message);
    }
}

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    if (info.menuItemId === 'download-with-mergen') {
        const url = info.linkUrl || info.srcUrl || tab.url;
        console.log('[MERGEN] Context menu clicked, URL:', url);
        await sendToMergen(url, tab);
    }
});

// Handle browser action (icon click)
chrome.action.onClicked.addListener(async (tab) => {
    console.log('[MERGEN] Extension icon clicked, URL:', tab.url);
    await sendToMergen(tab.url, tab);
});

/**
 * Send download request to Mergen via native messaging
 */
async function sendToMergen(url, tab) {
    try {
        console.log('[MERGEN] Sending to native host:', {
            url,
            title: tab.title
        });

        const response = await chrome.runtime.sendNativeMessage(MERGEN_HOST, {
            action: 'download_url',
            url: url,
            pageTitle: tab.title || '',
            pageUrl: tab.url || '',
            favicon: tab.favIconUrl || ''
        });

        if (response && response.success) {
            console.log('[MERGEN] ✅ Successfully sent to Mergen');
            showNotification('Download Started', `Added: ${tab.title || url}`);
        } else {
            console.error('[MERGEN] Error:', response?.error);
            showNotification('Mergen Error', response?.error || 'Failed to send to Mergen');
        }
    } catch (err) {
        console.error('[MERGEN] Native messaging error:', err);
        showNotification(
            'Mergen Not Running',
            'Make sure Mergen app is running. First time? Run install script in native-host/'
        );
    }
}

/**
 * Show notification to user
 */
function showNotification(title, message) {
    try {
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon-128.png',
            title: title,
            message: message
        });
    } catch (e) {
        console.log('[MERGEN] Notification:', title, '-', message);
    }
}

console.log('[MERGEN] Background script loaded');
