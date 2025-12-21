// Mergen Download Manager - Browser Extension
// Captures downloads and sends to Mergen via Native Messaging

const NATIVE_HOST_NAME = "com.tunahanyrd.mergen";

// Track processed downloads to avoid duplicates
const processedDownloads = new Set();

// Test native messaging connection on install
chrome.runtime.onInstalled.addListener(() => {
    console.log("✅ Mergen extension installed!");

    // Create context menu
    chrome.contextMenus.create({
        id: "mergen-download",
        title: "Download with Mergen",
        contexts: ["link"]
    });

    // Test connection immediately
    console.log("🔍 Testing native messaging connection...");
    testNativeConnection();
});

// Test native messaging connection
function testNativeConnection() {
    chrome.runtime.sendNativeMessage(
        NATIVE_HOST_NAME,
        { action: "ping", test: true },
        (response) => {
            if (chrome.runtime.lastError) {
                console.error("❌ Native messaging connection FAILED:");
                console.error("   Error:", chrome.runtime.lastError.message);
                console.error("   This usually means:");
                console.error("   1. Native host not registered correctly");
                console.error("   2. Extension ID doesn't match manifest");
                console.error("   3. Python script has errors");
            } else {
                console.log("✅ Native messaging connection SUCCESS!");
                console.log("   Response:", response);
            }
        }
    );
}

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "mergen-download" && info.linkUrl) {
        console.log("📥 Context menu download requested:", info.linkUrl);
        sendToMergen(info.linkUrl, info.linkUrl.split('/').pop() || 'download');
    }
});

// PRIMARY: Intercept downloads BEFORE they start (prevents save dialog)
chrome.downloads.onDeterminingFilename.addListener((downloadItem, suggest) => {
    console.log("🚫 Intercepting download:", downloadItem.url);

    // Check for duplicates
    const downloadKey = downloadItem.url + downloadItem.filename;
    if (processedDownloads.has(downloadKey)) {
        console.log("⚠️ Duplicate download, skipping:", downloadKey);
        chrome.downloads.cancel(downloadItem.id);
        return false;
    }

    // Mark as processed
    processedDownloads.add(downloadKey);
    // Clean up after 5 seconds
    setTimeout(() => processedDownloads.delete(downloadKey), 5000);

    // Send to Mergen
    sendToMergen(downloadItem.url, downloadItem.filename);

    // Cancel immediately - NO save dialog will appear
    chrome.downloads.cancel(downloadItem.id, () => {
        chrome.downloads.erase({ id: downloadItem.id });
    });

    // Return false to prevent Chrome from asking for filename
    return false;
});

// Send download to native host
function sendToMergen(url, filename) {
    const message = {
        action: "add_download",
        url: url,
        filename: filename,
        timestamp: new Date().toISOString()
    };

    console.log("📤 Sending to native host:", message);

    chrome.runtime.sendNativeMessage(
        NATIVE_HOST_NAME,
        message,
        (response) => {
            if (chrome.runtime.lastError) {
                console.error("❌ Native messaging error:");
                console.error("   Message:", chrome.runtime.lastError.message);
                console.error("   URL:", url);
            } else {
                console.log("✅ Native host response:", response);
            }
        }
    );
}

// Test connection button (for debugging)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "test_connection") {
        console.log("🧪 Manual test triggered");
        testNativeConnection();
        sendResponse({ status: "test sent" });
    }
});
