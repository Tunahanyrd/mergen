/**
 * Mergen Browser Extension - Simplified Version
 * Just sends page URLs to Mergen, let yt-dlp handle detection
 */

const MERGEN_HOST = 'com.tunahanyrd.mergen';

// Initialize context menu on installation
chrome.runtime.onInstalled.addListener(() => {
    console.log('[MERGEN] Extension installed, creating context menu');

    chrome.contextMenus.create({
        id: 'download-with-mergen',
        title: '📥 Download with Mergen',
        contexts: ['page', 'link', 'video', 'audio']
    });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    if (info.menuItemId === 'download-with-mergen') {
        // Prefer link URL if right-clicked on link, otherwise use page URL
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
            title: tab.title,
            favicon: tab.favIconUrl
        });

        const response = await chrome.runtime.sendNativeMessage(MERGEN_HOST, {
            action: 'download_url',
            url: url,
            pageTitle: tab.title || '',
            pageUrl: tab.url || '',
            favicon: tab.favIconUrl || ''
        });

        if (response && response.success) {
            console.log('[MERGEN] Successfully sent to Mergen');
        } else {
            console.error('[MERGEN] Mergen returned error:', response?.error);
            showNotification('Mergen Error', response?.error || 'Failed to send to Mergen');
        }
    } catch (err) {
        console.error('[MERGEN] Native messaging error:', err);
        showNotification(
            'Mergen Connection Failed',
            'Make sure Mergen is running and the extension is registered.'
        );
    }
}

/**
 * Show notification to user
 */
function showNotification(title, message) {
    chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icons/icon-128.png',
        title: title,
        message: message
    });
}

console.log('[MERGEN] Background script loaded');
