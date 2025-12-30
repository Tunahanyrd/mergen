// Import media detector (MV3 version)
importScripts("media-detector.js");

// Mergen Download Manager - Browser Extension v0.9.3
// Captures downloads AND streaming media (HLS/DASH) via Manifest V3

// Browser API polyfill - Firefox uses 'browser', Chrome uses 'chrome'
if (typeof browser === 'undefined') {
    // Chrome/Chromium - use chrome API
    globalThis.browser = chrome;
}
// Now 'browser' works in both Firefox and Chrome!

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
browser.runtime.onInstalled.addListener(() => {
    console.log("✅ Mergen v0.9.3 extension installed!");

    // Create context menus
    browser.contextMenus.create({
        id: "mergen-download",
        title: "Download with Mergen",
        contexts: ["link"]
    });

    browser.contextMenus.create({
        id: "mergen-stream",
        title: "Download Stream with Mergen",
        contexts: ["link", "video", "audio"]
    });

    // AUTO-REGISTER with Mergen app (zero-config!)
    autoRegisterExtension();

    // Setup declarativeNetRequest rules for media detection
    setupMediaDetectionRules();
});

// Auto-register extension with Mergen app
async function autoRegisterExtension() {
    const extensionId = browser.runtime.id;
    const browserType = typeof browser.runtime.getBrowserInfo !== 'undefined' ? 'firefox' : 'chrome';

    console.log(`🚀 Auto-registering ${browserType} extension...`);

    try {
        const response = await fetch('http://localhost:8765/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                extension_id: extensionId,
                browser: browserType,
                version: '0.9.3'
            })
        });

        if (response.ok) {
            const data = await response.json();
            console.log('✅ Auto-registration successful!', data);

            // Store registration status
            browser.storage.local.set({
                registered: true,
                app_version: data.app_version,
                registered_at: Date.now()
            });

            // Show success notification
            browser.notifications.create({
                type: 'basic',
                iconUrl: browser.runtime.getURL('icons/icon128.png'),
                title: '✅ Mergen Connected!',
                message: `Extension auto-registered with Mergen app v${data.app_version}. Ready to use!`,
                priority: 2
            });
        } else {
            throw new Error(`Registration failed: ${response.status}`);
        }
    } catch (err) {
        console.error('❌ Auto-registration failed:', err.message);
        console.log('💡 Make sure Mergen app is running');
        console.log('💡 Start Mergen from your applications menu or terminal');

        // Test if server is reachable
        try {
            const healthCheck = await fetch('http://localhost:8765/health');
            if (healthCheck.ok) {
                console.log('✅ Health check passed, server is running');
                console.log('⚠️ Registration endpoint might have issues');
            }
        } catch (e) {
            console.error('❌ Cannot reach localhost:8765');
            console.error('🔍 Mergen app is not running or port is blocked');
        }

        // Show helpful notification with instructions
        browser.notifications.create({
            type: 'basic',
            iconUrl: browser.runtime.getURL('icons/icon128.png'),
            title: '⚠️ Mergen App Not Running',
            message: `Please start Mergen from your applications menu.\n\nExtension ID: ${extensionId}\n\nThe extension will auto-register when Mergen starts.`,
            priority: 1
        });
    }
}

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

    browser.declarativeNetRequest.updateDynamicRules({
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

    try {
        if (browser.declarativeNetRequest?.onRuleMatched?.addListener) {
            browser.declarativeNetRequest.onRuleMatched.addListener((details) => {
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
            throw new Error("onRuleMatched not available");
        }
    } catch (err) {
        console.log("⚠️ declarativeNetRequest.onRuleMatched not supported:", err.message);
        console.log("📋 Extension will use context menu and download intercept instead");
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
        browser.action.setBadgeText({ text: count.toString() });
        browser.action.setBadgeBackgroundColor({ color: "#007acc" });
    } else {
        browser.action.setBadgeText({ text: "" });
    }
}

// Test native messaging connection
function testNativeConnection() {
    browser.runtime.sendNativeMessage(
        NATIVE_HOST_NAME,
        { action: "ping", test: true },
        (response) => {
            if (browser.runtime.lastError) {
                console.error("❌ Native messaging connection FAILED:");
                console.error("   Error:", browser.runtime.lastError.message);
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
browser.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "mergen-download") {
        let targetUrl = info.linkUrl || info.srcUrl || info.pageUrl;

        if (!targetUrl) return;

        // Reject browser-internal URLs
        if (targetUrl.startsWith('chrome://') ||
            targetUrl.startsWith('about://') ||
            targetUrl.startsWith('chrome-extension://') ||
            targetUrl.startsWith('moz-extension://') ||
            targetUrl.startsWith('file://')) {
            console.log("⚠️ Cannot download browser-internal URL:", targetUrl);
            return;
        }

        console.log("📥 Context menu download requested:", targetUrl);
        const streamType = detectStreamType(targetUrl);
        sendToMergen(targetUrl, targetUrl.split('/').pop() || 'download', streamType);
    } else if (info.menuItemId === "mergen-stream") {
        // Get most recent detected stream for this tab
        const recentStream = Array.from(detectedStreams.values())
            .filter(s => s.tabId === tab.id)
            .sort((a, b) => b.timestamp - a.timestamp)[0];

        if (recentStream) {
            console.log("🎬 Downloading detected stream:", recentStream.url);

            // CRITICAL: For YouTube, send page URL instead of HLS manifest
            // yt-dlp handles YouTube natively and needs the watch URL, not the manifest
            const isYouTube = tab.url && (
                tab.url.includes('youtube.com') ||
                tab.url.includes('youtu.be')
            );

            if (isYouTube) {
                console.log("📺 YouTube detected - sending page URL instead of HLS manifest");
                const filename = 'video'; // yt-dlp will set the real filename
                sendToMergen(tab.url, filename, 'youtube');
            } else {
                const filename = extractFilename(recentStream.url) || 'stream';
                sendToMergen(recentStream.url, filename, recentStream.type);
            }
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
browser.downloads.onDeterminingFilename.addListener((downloadItem, suggest) => {
    console.log("🚫 Intercepting download:", downloadItem.url);

    // Reject browser-internal URLs
    if (downloadItem.url.startsWith('chrome://') ||
        downloadItem.url.startsWith('about://') ||
        downloadItem.url.startsWith('chrome-extension://') ||
        downloadItem.url.startsWith('moz-extension://') ||
        downloadItem.url.startsWith('file://')) {
        console.log("⚠️ Skipping browser-internal URL:", downloadItem.url);
        suggest({ filename: downloadItem.filename }); // Let browser handle it
        return;
    }

    // Check for duplicates
    const downloadKey = downloadItem.url + downloadItem.filename;
    if (processedDownloads.has(downloadKey)) {
        console.log("⚠️ Duplicate download, skipping:", downloadKey);
        browser.downloads.cancel(downloadItem.id);
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
    browser.downloads.cancel(downloadItem.id, () => {
        browser.downloads.erase({ id: downloadItem.id });
    });

    // Return false to prevent Chrome from asking for filename
    return false;
});

// Rate limiting for sending streams to native host
const sentStreams = new Set();

// Send download/stream to native host
function sendToMergen(url, filename, streamType = 'direct') {
    // Prevent duplicate stream notifications within 5 seconds
    if (streamType !== 'direct') {
        const streamKey = `${url}_${streamType}`;
        if (sentStreams.has(streamKey)) {
            console.log("⚠️ Skipper duplicate stream notification:", streamKey);
            return;
        }
        sentStreams.add(streamKey);
        setTimeout(() => sentStreams.delete(streamKey), 5000); // 5 sec cooldown
    }
    const message = {
        action: "add_download",
        url: url,
        filename: filename,
        stream_type: streamType,  // NEW: hls, dash, mp4, ts, mp3, direct
        timestamp: new Date().toISOString()
    };

    console.log("📤 Sending to native host:", message);

    browser.runtime.sendNativeMessage(
        NATIVE_HOST_NAME,
        message,
        (response) => {
            if (browser.runtime.lastError) {
                console.error("❌ Native messaging error:");
                console.error("   Message:", browser.runtime.lastError.message);
                console.error("   URL:", url);
            } else {
                console.log("✅ Native host response:", response);

                // Show notification
                if (streamType !== 'direct') {
                    browser.notifications.create({
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
browser.runtime.onMessage.addListener((request, sender, sendResponse) => {
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
