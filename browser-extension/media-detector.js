/**
 * Media Detector - Manifest V3 Version
 * Uses declarativeNetRequest instead of webRequest
 */

// Import rule manager
importScripts('utils/rule-manager.js');

// Configuration
const CONFIG = {
    MIN_SIZE: 100 * 1024, // 100KB minimum
    VERBOSE: false,
    MAX_MEDIA_PER_TAB: 50
};

// Detected media storage (tabId -> media array)
const detectedMediaByTab = new Map();

// Load verbose setting
chrome.storage.local.get(['verbose'], (result) => {
    CONFIG.VERBOSE = result.verbose || false;
});

/**
 * Parse media URL and extract metadata
 */
function parseMediaUrl(url) {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname;

    let metadata = {
        url,
        title: 'Unknown',
        size: null,
        quality: null,
        type: 'unknown',
        timestamp: Date.now()
    };

    // YouTube detection
    if (hostname.includes('googlevideo.com')) {
        metadata.type = 'youtube';

        // Extract quality from itag parameter
        const itagMatch = url.match(/itag=(\d+)/);
        if (itagMatch) {
            const itag = itagMatch[1];
            const qualityMap = {
                '137': '1080p', '136': '720p', '135': '480p',
                '134': '360p', '133': '240p', '160': '144p',
                '96': 'Audio 128kbps', '95': 'Audio 64kbps'
            };
            metadata.quality = qualityMap[itag] || `itag ${itag}`;
        }

        // Try to extract title from URL params
        const titleMatch = url.match(/title=([^&]+)/);
        if (titleMatch) {
            metadata.title = decodeURIComponent(titleMatch[1]);
        }
    }

    // Twitter detection
    else if (hostname.includes('twimg.com')) {
        metadata.type = 'twitter';
        metadata.title = 'Twitter Video';

        // Detect quality from filename
        if (url.includes('/720x')) metadata.quality = '720p';
        else if (url.includes('/480x')) metadata.quality = '480p';
        else if (url.includes('/360x')) metadata.quality = '360p';
    }

    // Instagram detection
    else if (hostname.includes('cdninstagram.com') || hostname.includes('fbcdn.net')) {
        metadata.type = 'instagram';
        metadata.title = 'Instagram Video';
    }

    // HLS/DASH detection
    else if (url.includes('.m3u8')) {
        metadata.type = 'hls';
        metadata.title = 'HLS Stream';
    }
    else if (url.includes('.mpd')) {
        metadata.type = 'dash';
        metadata.title = 'DASH Stream';
    }

    // Generic MP4
    else if (url.includes('.mp4')) {
        metadata.type = 'video';
        metadata.title = 'Video File';
    }

    return metadata;
}

/**
 * Add detected media to tab storage
 */
function addDetectedMedia(tabId, media) {
    if (!detectedMediaByTab.has(tabId)) {
        detectedMediaByTab.set(tabId, []);
    }

    const mediaList = detectedMediaByTab.get(tabId);

    // Check for duplicates
    const exists = mediaList.some(m => m.url === media.url);
    if (exists) return;

    // Limit per tab
    if (mediaList.length >= CONFIG.MAX_MEDIA_PER_TAB) {
        mediaList.shift(); // Remove oldest
    }

    mediaList.push(media);

    // Update badge
    updateBadge(tabId, mediaList.length);

    // Save to storage
    const storageKey = `media_tab_${tabId}`;
    chrome.storage.local.set({ [storageKey]: mediaList });

    if (CONFIG.VERBOSE) {
        console.log(`📹 Detected media (${media.type}): ${media.title}`);
    }
}

/**
 * Update badge counter for tab
 */
function updateBadge(tabId, count) {
    if (count > 0) {
        chrome.action.setBadgeText({
            text: count.toString(),
            tabId
        });
        chrome.action.setBadgeBackgroundColor({
            color: '#00f2ff',
            tabId
        });
    } else {
        chrome.action.setBadgeText({ text: '', tabId });
    }
}

/**
 * Listen for declarativeNetRequest rule matches
 * This is the MV3 way to detect media requests
 */
chrome.declarativeNetRequest.onRuleMatched.addListener((details) => {
    const { request } = details;
    const { url, tabId, type } = request;

    // Ignore invalid tab IDs
    if (tabId < 0) return;

    // Parse media metadata
    const media = parseMediaUrl(url);

    // Add to detected media
    addDetectedMedia(tabId, media);
});

/**
 * Clear media when tab is closed
 */
chrome.tabs.onRemoved.addListener((tabId) => {
    detectedMediaByTab.delete(tabId);
    const storageKey = `media_tab_${tabId}`;
    chrome.storage.local.remove(storageKey);
});

/**
 * Clear media when tab is updated (navigation)
 */
chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
    if (changeInfo.status === 'loading' && changeInfo.url) {
        // Clear previous media on navigation
        detectedMediaByTab.delete(tabId);
        updateBadge(tabId, 0);
    }
});

/**
 * Handle verbose mode toggle
 */
chrome.storage.onChanged.addListener((changes) => {
    if (changes.verbose) {
        CONFIG.VERBOSE = changes.verbose.newValue;
        console.log(`📢 Verbose mode: ${CONFIG.VERBOSE ? 'ON' : 'OFF'}`);
    }
});

console.log('✅ Media Detector MV3 initialized!');
