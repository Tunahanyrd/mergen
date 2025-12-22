// Mergen Download Manager - Browser Extension v0.8.0
// Captures downloads AND streaming media (HLS/DASH) via Manifest V3

const NATIVE_HOST_NAME = "com.tunahanyrd.mergen";

// Track processed downloads to avoid duplicates
const processedDownloads = new Set();

// Store detected streams
let detectedStreams = new Map();

// Media URL patterns for detection
const MEDIA_PATTERNS = {
    hls: /\.m3u8(\?.*)?$/i,
    dash: /\.mpd(\?.*)?$/i,
    mp4: /\.mp4(\?.*)?$/i,
    ts: /\.ts(\?.*)?$/i,
    mp3: /\.mp3(\?.*)?$/i
};

// Initialize extension
chrome.runtime.onInstalled.addListener(() => {
    console.log("✅ Mergen v0.8.0 extension installed!");

    // Create context menus
    chrome.contextMenus.create({
        id: "mergen-download",
        title: "Download with Mergen",
        contexts: ["link"]
    });

    chrome.contextMenus.create({
        id: "mergen-stream",
        title: "Download Stream with Mergen",
        contexts: ["link", "video", "audio"]
    });

    // Setup declarativeNetRequest rules for media detection
    setupMediaDetectionRules();

    // Test connection
    console.log("🔍 Testing native messaging connection...");
    testNativeConnection();
});

// Setup declarativeNetRequest rules for media sniffing
function setupMediaDetectionRules() {
    const rules = [
        {
            id: 1,
            priority: 1,
            action: { type: "allow" },
            condition: {
                regexFilter: ".*\\.m3u8(\\?.*)?$",
                resourceTypes: ["xmlhttprequest", "media"]
            }
        },
        {
            id: 2,
            priority: 1,
            action: { type: "allow" },
            condition: {
                regexFilter: ".*\\.mpd(\\?.*)?$",
                resourceTypes: ["xmlhttprequest", "media"]
            }
        },
        {
            id: 3,
            priority: 1,
            action: { type: "allow" },
            condition: {
                regexFilter: ".*\\.(mp4|ts|mp3)(\\?.*)?$",
                resourceTypes: ["media", "xmlhttprequest"]
            }
        }
    ];

    chrome.declarativeNetRequest.updateDynamicRules({
        removeRuleIds: rules.map(r => r.id),
        addRules: rules
    }).then(() => {
        console.log("📋 Media detection rules registered");
    }).catch(err => {
        console.error("❌ Failed to register rules:", err);
    });
}

// Detect stream type from URL
function detectStreamType(url) {
    for (const [type, pattern] of Object.entries(MEDIA_PATTERNS)) {
        if (pattern.test(url)) {
            return type;
        }
    }
    return 'direct';
}

// Firefox MV3 still supports webRequest API (Chrome Service Workers don't)
// Detect browser and enable webRequest for Firefox
const isFirefox = typeof browser !== 'undefined';

if (isFirefox && browser.webRequest && browser.webRequest.onBeforeRequest) {
    console.log("🦊 Firefox detected - enabling webRequest media sniffing");

    browser.webRequest.onBeforeRequest.addListener(
        (details) => {
            const streamType = detectStreamType(details.url);

            if (streamType !== 'direct') {
                const streamKey = `${details.url}_${Date.now()}`;

                // Store detected stream
                detectedStreams.set(streamKey, {
                    url: details.url,
                    type: streamType,
                    timestamp: Date.now(),
                    tabId: details.tabId
                });

                console.log(`🎬 Detected ${streamType.toUpperCase()} stream:`, details.url.substring(0, 100));

                // Update badge
                updateBadgeCount();

                // Clean old detections (keep last 50)
                if (detectedStreams.size > 50) {
                    const oldestKey = detectedStreams.keys().next().value;
                    detectedStreams.delete(oldestKey);
                }
            }
        },
        {
            urls: ["<all_urls>"],
            types: ["xmlhttprequest", "media"]
        }
    );
} else {
    // Chrome: Use declarativeNetRequest.onRuleMatched for automatic detection
    console.log("🌐 Chrome detected - using declarativeNetRequest events");

    if (chrome.declarativeNetRequest && chrome.declarativeNetRequest.onRuleMatched) {
        chrome.declarativeNetRequest.onRuleMatched.addListener((details) => {
            const url = details.request.url;
            const streamType = detectStreamType(url);

            if (streamType !== 'direct') {
                const streamKey = `${url}_${Date.now()}`;

                // Store detected stream
                detectedStreams.set(streamKey, {
                    url: url,
                    type: streamType,
                    timestamp: Date.now(),
                    tabId: details.request.tabId
                });

                console.log(`🎬 Rule matched - ${streamType.toUpperCase()} stream:`, url.substring(0, 100));

                // Update badge
                updateBadgeCount();

                // Clean old detections (keep last 50)
                if (detectedStreams.size > 50) {
                    const oldestKey = detectedStreams.keys().next().value;
                    detectedStreams.delete(oldestKey);
                }
            }
        });

        console.log("✅ Automatic stream detection enabled via declarativeNetRequest");
    } else {
        console.log("⚠️ declarativeNetRequest events not available - using context menu only");
    }
}

// Both Firefox and Chrome now have automatic sniffing! ✅
// 1. downloads.onDeterminingFilename (direct downloads)
// 2. Context menu on video/audio elements
// 3. User manually selecting "Download Stream" on links

// Update extension badge with stream count
function updateBadgeCount() {
    const count = detectedStreams.size;
    if (count > 0) {
        chrome.action.setBadgeText({ text: count.toString() });
        chrome.action.setBadgeBackgroundColor({ color: "#007acc" });
    } else {
        chrome.action.setBadgeText({ text: "" });
    }
}

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
        const streamType = detectStreamType(info.linkUrl);
        sendToMergen(info.linkUrl, info.linkUrl.split('/').pop() || 'download', streamType);
    } else if (info.menuItemId === "mergen-stream") {
        // Get most recent detected stream for this tab
        const recentStream = Array.from(detectedStreams.values())
            .filter(s => s.tabId === tab.id)
            .sort((a, b) => b.timestamp - a.timestamp)[0];

        if (recentStream) {
            console.log("🎬 Downloading detected stream:", recentStream.url);
            const filename = extractFilename(recentStream.url) || 'stream';
            sendToMergen(recentStream.url, filename, recentStream.type);
        } else if (info.linkUrl) {
            const streamType = detectStreamType(info.linkUrl);
            sendToMergen(info.linkUrl, info.linkUrl.split('/').pop() || 'stream', streamType);
        }
    }
});

// Extract filename from URL
function extractFilename(url) {
    try {
        const urlObj = new URL(url);
        const pathname = urlObj.pathname;
        const parts = pathname.split('/');
        return parts[parts.length - 1] || null;
    } catch {
        return null;
    }
}

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

    // Detect if it's a stream
    const streamType = detectStreamType(downloadItem.url);

    // Send to Mergen
    sendToMergen(downloadItem.url, downloadItem.filename, streamType);

    // Cancel immediately - NO save dialog will appear
    chrome.downloads.cancel(downloadItem.id, () => {
        chrome.downloads.erase({ id: downloadItem.id });
    });

    // Return false to prevent Chrome from asking for filename
    return false;
});

// Send download/stream to native host
function sendToMergen(url, filename, streamType = 'direct') {
    const message = {
        action: "add_download",
        url: url,
        filename: filename,
        stream_type: streamType,  // NEW: hls, dash, mp4, ts, mp3, direct
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

                // Show notification
                if (streamType !== 'direct') {
                    chrome.notifications.create({
                        type: 'basic',
                        iconUrl: 'icons/icon128.png',
                        title: 'Mergen - Stream Detected',
                        message: `${streamType.toUpperCase()} stream sent to Mergen`
                    });
                }
            }
        }
    );
}

// Handle messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "test_connection") {
        console.log("🧪 Manual test triggered");
        testNativeConnection();
        sendResponse({ status: "test sent" });
    } else if (request.action === "get_streams") {
        // Send detected streams to popup
        sendResponse({
            streams: Array.from(detectedStreams.values())
        });
    } else if (request.action === "download_stream") {
        const stream = detectedStreams.get(request.streamKey);
        if (stream) {
            const filename = extractFilename(stream.url) || 'stream';
            sendToMergen(stream.url, filename, stream.type);
            sendResponse({ status: "sent" });
        } else {
            sendResponse({ status: "not_found" });
        }
    }
    return true;  // Keep channel open for async response
});

// Clean old detections periodically (every 5 minutes)
setInterval(() => {
    const now = Date.now();
    const maxAge = 5 * 60 * 1000;  // 5 minutes

    for (const [key, stream] of detectedStreams.entries()) {
        if (now - stream.timestamp > maxAge) {
            detectedStreams.delete(key);
        }
    }

    updateBadgeCount();
}, 60000);  // Check every minute
