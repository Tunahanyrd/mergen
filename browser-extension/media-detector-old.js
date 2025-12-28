/**
 * Media Detector - Enhanced for YouTube and streaming platforms
 * IDM-style automatic media capture with YouTube support
 */

// Configuration
const CONFIG = {
    FETCH_TIMEOUT: 5000,
    MIN_SIZE: 100 * 1024,
    VERBOSE: false,
    RATE_LIMIT_MS: 500
};

// Media file patterns - Enhanced for YouTube
const MEDIA_PATTERNS = {
    video: /\.(mp4|mkv|webm|avi|mov|flv|wmv|m4v|3gp)(\?.*)?$/i,
    audio: /\.(mp3|m4a|aac|flac|wav|ogg|opus|wma)(\?.*)?$/i,
    stream: /\.(m3u8|mpd|f4m|m3u)(\?.*)?$/i,
    playlist: /\/(playlist|manifest|index\.m3u8|master\.m3u8)/i,
    // YouTube specific patterns
    youtube: /googlevideo\.com.*videoplayback/i,
    youtubeStream: /manifest\.googlevideo\.com/i
};

// Blacklist
const BLACKLIST_DOMAINS = [
    'doubleclick.net',
    'googlesyndication.com',
    'google-analytics.com',
    'googletagmanager.com',
    'facebook.com/tr',
    'scorecardresearch.com'
];

// YouTube quality detection
const YOUTUBE_QUALITY = {
    '137': '1080p',
    '136': '720p',
    '135': '480p',
    '134': '360p',
    '133': '240p',
    '160': '144p'
};

// Detected media storage
let detectedMedia = new Map();

// Load config from storage
chrome.storage.local.get(['verbose', 'detectedMedia'], (result) => {
    CONFIG.VERBOSE = result.verbose || false;
    if (result.detectedMedia) {
        detectedMedia = new Map(Object.entries(result.detectedMedia));
        updateBadge();
    }
});

/**
 * Validate URL
 */
function isValidUrl(url) {
    try {
        const urlObj = new URL(url);
        return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch {
        return false;
    }
}

/**
 * Check if URL is YouTube media
 */
function isYouTubeMedia(url) {
    return MEDIA_PATTERNS.youtube.test(url) || MEDIA_PATTERNS.youtubeStream.test(url);
}

/**
 * Extract YouTube quality from URL
 */
function getYouTubeQuality(url) {
    const itag = url.match(/itag=(\d+)/);
    if (itag) {
        return YOUTUBE_QUALITY[itag[1]] || 'unknown';
    }
    return 'auto';
}

/**
 * Check if URL is a media file
 */
function isMediaUrl(url) {
    if (!isValidUrl(url)) return false;

    // YouTube special handling
    if (isYouTubeMedia(url)) {
        return true;
    }

    return MEDIA_PATTERNS.video.test(url) ||
        MEDIA_PATTERNS.audio.test(url) ||
        MEDIA_PATTERNS.stream.test(url) ||
        MEDIA_PATTERNS.playlist.test(url);
}

/**
 * Check if URL should be ignored
 */
function shouldIgnore(url) {
    return BLACKLIST_DOMAINS.some(domain => url.includes(domain));
}

/**
 * Get media type from URL
 */
function getMediaType(url) {
    if (isYouTubeMedia(url)) return 'youtube';
    if (MEDIA_PATTERNS.video.test(url)) return 'video';
    if (MEDIA_PATTERNS.audio.test(url)) return 'audio';
    if (MEDIA_PATTERNS.stream.test(url)) return 'stream';
    if (MEDIA_PATTERNS.playlist.test(url)) return 'playlist';
    return 'unknown';
}

/**
 * Extract filename from URL
 */
function getFilename(url) {
    try {
        // YouTube special naming
        if (isYouTubeMedia(url)) {
            const quality = getYouTubeQuality(url);
            return `youtube_video_${quality}.mp4`;
        }

        const urlObj = new URL(url);
        const pathname = urlObj.pathname;
        const filename = pathname.substring(pathname.lastIndexOf('/') + 1);
        return filename || 'media_file';
    } catch {
        return 'media_file';
    }
}

/**
 * Persist detected media to storage
 */
function persistMedia() {
    const mediaObj = Object.fromEntries(detectedMedia);
    chrome.storage.local.set({ detectedMedia: mediaObj });
}

/**
 * Listen to network requests for media files
 */
chrome.webRequest.onBeforeRequest.addListener(
    (details) => {
        const url = details.url;

        // Ignore blacklisted domains
        if (shouldIgnore(url)) {
            return;
        }

        // Check if media URL (including YouTube)
        if (isMediaUrl(url)) {
            const mediaInfo = {
                url: url,
                filename: getFilename(url),
                type: getMediaType(url),
                tabId: details.tabId,
                timestamp: Date.now(),
                initiator: details.initiator || 'unknown',
                size: details.requestHeaders?.['Content-Length'] || 'unknown'
            };

            // Store detected media
            detectedMedia.set(url, mediaInfo);
            persistMedia();

            if (CONFIG.VERBOSE) {
                console.log('🎬 Media detected:', mediaInfo.filename, mediaInfo.type);
            }

            // Update badge
            updateBadge();

            // Notify popup if open
            chrome.runtime.sendMessage({
                action: 'mediaDetected',
                media: mediaInfo
            }).catch(() => { });
        }
    },
    { urls: ["<all_urls>"] },
    ["requestHeaders"]
);

/**
 * Update extension badge with media count
 */
function updateBadge() {
    const count = detectedMedia.size;
    if (count > 0) {
        chrome.action.setBadgeText({ text: count.toString() });
        chrome.action.setBadgeBackgroundColor({ color: '#00C853' });
    } else {
        chrome.action.setBadgeText({ text: '' });
    }
}

/**
 * Send to Mergen with timeout and validation
 */
async function sendToMergen(url) {
    if (!isValidUrl(url)) {
        throw new Error('Invalid URL');
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), CONFIG.FETCH_TIMEOUT);

    try {
        const response = await fetch('http://localhost:8765/add_download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url }),
            signal: controller.signal
        });

        clearTimeout(timeout);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        if (CONFIG.VERBOSE) {
            console.log('📥 Sent to Mergen:', url);
        }

        return { status: 'ok' };

    } catch (err) {
        clearTimeout(timeout);

        if (err.name === 'AbortError') {
            throw new Error('Mergen not responding (timeout)');
        }

        throw new Error(`Failed to connect to Mergen: ${err.message}`);
    }
}

/**
 * Handle messages from popup
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getDetectedMedia') {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                const tabId = tabs[0].id;
                const tabMedia = Array.from(detectedMedia.values())
                    .filter(m => m.tabId === tabId);
                sendResponse({ media: tabMedia });
            }
        });
        return true;
    }

    if (request.action === 'clearDetectedMedia') {
        detectedMedia.clear();
        persistMedia();
        updateBadge();
        sendResponse({ status: 'ok' });
    }

    if (request.action === 'downloadMedia') {
        sendToMergen(request.url)
            .then(result => sendResponse(result))
            .catch(err => sendResponse({
                status: 'error',
                message: err.message
            }));
        return true;
    }

    if (request.action === 'setVerbose') {
        CONFIG.VERBOSE = request.verbose;
        chrome.storage.local.set({ verbose: request.verbose });
        sendResponse({ status: 'ok' });
    }
});

/**
 * Clear detected media when tab is closed
 */
chrome.tabs.onRemoved.addListener((tabId) => {
    for (const [url, media] of detectedMedia.entries()) {
        if (media.tabId === tabId) {
            detectedMedia.delete(url);
        }
    }
    persistMedia();
    updateBadge();
});

console.log('🎬 Media detector initialized with YouTube support');
