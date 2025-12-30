/**
 * Mergen Content Script - Media Detector
 * Inspired by IDM's content.js architecture
 * Runs on all pages to detect video, audio, and streaming media
 */

(function () {
    'use strict';

    // Prevent multiple initialization
    if (window.__mergen_init__) return;
    window.__mergen_init__ = true;

    const browser = chrome || browser;

    // Configuration
    const CONFIG = {
        DEBUG: true,
        MIN_VIDEO_SIZE: 100, // Minimum video dimension (width/height) to consider
        DETECTION_DELAY: 200, // ms to debounce detection events
        YOUTUBE_CHECK_INTERVAL: 1000 // ms to check for YouTube player
    };

    // State
    const state = {
        detectedMedia: new Map(), // url -> {element, metadata}
        frameId: null, // Current frame ID
        isTop: window.self === window.top,
        timers: new Map() // element -> timeout
    };

    // Observers
    let mutationObserver = null;
    let resizeObserver = null;
    let intersectionObserver = null;

    /**
     * Utility: Log with prefix
     */
    function log(...args) {
        if (CONFIG.DEBUG) {
            console.log('[Mergen Content]', ...args);
        }
    }

    /**
     * Utility: Get element dimensions and visibility
     */
    function getElementInfo(element) {
        try {
            const rect = element.getBoundingClientRect();
            const style = window.getComputedStyle(element);

            return {
                width: rect.width,
                height: rect.height,
                visible: style.display !== 'none' &&
                    style.visibility !== 'hidden' &&
                    style.opacity !== '0',
                inViewport: rect.top < window.innerHeight &&
                    rect.bottom > 0 &&
                    rect.left < window.innerWidth &&
                    rect.right > 0
            };
        } catch (e) {
            return null;
        }
    }

    /**
     * Utility: Extract video ID from various sources
     */
    function extractVideoId(element, url) {
        // Try data attributes
        const dataId = element.getAttribute('data-video-id') ||
            element.getAttribute('data-id');
        if (dataId) return dataId;

        // Try from URL
        if (url) {
            // YouTube: /watch?v=ID or /embed/ID or youtu.be/ID
            const ytMatch = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
            if (ytMatch) return ytMatch[1];

            // Vimeo: vimeo.com/ID
            const vimeoMatch = url.match(/vimeo\.com\/(\d+)/);
            if (vimeoMatch) return vimeoMatch[1];

            // Instagram: /p/ID or /reel/ID
            const igMatch = url.match(/instagram\.com\/(?:p|reel|tv)\/([a-zA-Z0-9_-]+)/);
            if (igMatch) return igMatch[1];
        }

        return null;
    }

    /**
     * YouTube-specific: Detect player and extract metadata
     */
    function detectYouTubeVideo() {
        // Check if we're on YouTube
        if (!location.hostname.includes('youtube.com')) return null;

        try {
            // Try to get video ID from URL
            const urlParams = new URLSearchParams(location.search);
            const videoId = urlParams.get('v');
            if (!videoId) return null;

            // Try to find ytInitialPlayerResponse in page scripts
            const scripts = document.getElementsByTagName('script');
            for (let script of scripts) {
                if (!script.src && script.textContent.includes('ytInitialPlayerResponse')) {
                    try {
                        // Extract JSON data
                        const match = script.textContent.match(/var ytInitialPlayerResponse = ({.+?});/);
                        if (match) {
                            const data = JSON.parse(match[1]);
                            const videoDetails = data?.videoDetails;

                            if (videoDetails) {
                                return {
                                    id: videoId,
                                    title: videoDetails.title,
                                    author: videoDetails.author,
                                    lengthSeconds: videoDetails.lengthSeconds,
                                    thumbnail: videoDetails.thumbnail?.thumbnails?.[0]?.url,
                                    isLive: videoDetails.isLiveContent
                                };
                            }
                        }
                    } catch (e) {
                        log('Error parsing YouTube data:', e);
                    }
                }
            }

            // Fallback: just return video ID
            return { id: videoId };
        } catch (e) {
            log('Error detecting YouTube:', e);
            return null;
        }
    }

    /**
     * Instagram-specific: Detect media
     */
    function detectInstagramMedia() {
        if (!location.hostname.includes('instagram.com')) return null;

        try {
            // Instagram Reels/Posts use specific video elements
            const videos = document.querySelectorAll('video');
            if (videos.length === 0) return null;

            // Extract post ID from URL
            const match = location.pathname.match(/\/(?:p|reel|tv)\/([a-zA-Z0-9_-]+)/);
            if (!match) return null;

            return {
                id: match[1],
                type: location.pathname.includes('reel') ? 'reel' : 'post',
                videoCount: videos.length
            };
        } catch (e) {
            log('Error detecting Instagram:', e);
            return null;
        }
    }

    /**
     * Core: Detect media element and send to background
     */
    function detectMediaElement(element) {
        // Skip if already detected
        if (element.__mergen_detected__) return;

        // Get element info
        const info = getElementInfo(element);
        if (!info) return;

        // Skip tiny or hidden videos
        if ((element.tagName === 'VIDEO' || element.tagName === 'AUDIO') &&
            (info.width < CONFIG.MIN_VIDEO_SIZE || info.height < CONFIG.MIN_VIDEO_SIZE) &&
            element.tagName === 'VIDEO') {
            return;
        }

        // Get media URL
        const url = element.src || element.currentSrc || element.data;
        if (!url || url.startsWith('blob:') || url.startsWith('data:')) {
            // For blob/data URLs, we still want to track the element
            // but we'll need to get the actual URL later
        }

        // Extract metadata
        const metadata = {
            tagName: element.tagName.toLowerCase(),
            url: url,
            poster: element.poster,
            width: info.width,
            height: info.height,
            duration: element.duration || null,
            videoId: extractVideoId(element, url),
            visible: info.visible,
            inViewport: info.inViewport,
            pageUrl: location.href,
            pageTitle: document.title,
            timestamp: Date.now()
        };

        // Platform-specific detection
        if (location.hostname.includes('youtube.com')) {
            const ytData = detectYouTubeVideo();
            if (ytData) {
                metadata.platform = 'youtube';
                metadata.platformData = ytData;
            }
        } else if (location.hostname.includes('instagram.com')) {
            const igData = detectInstagramMedia();
            if (igData) {
                metadata.platform = 'instagram';
                metadata.platformData = igData;
            }
        } else if (location.hostname.includes('vimeo.com')) {
            metadata.platform = 'vimeo';
        } else if (location.hostname.includes('twitter.com') || location.hostname.includes('x.com')) {
            metadata.platform = 'twitter';
        }

        // Mark as detected
        element.__mergen_detected__ = true;
        element.__mergen_id__ = metadata.timestamp;

        // Store in state
        if (url) {
            state.detectedMedia.set(url, { element, metadata });
        }

        // Send to background
        sendToBackground({
            type: 'media_detected',
            metadata: metadata
        });

        log('✅ Detected:', metadata.tagName, url || '(no URL)', metadata);
    }

    /**
     * Core: Send message to background script
     */
    function sendToBackground(message) {
        try {
            browser.runtime.sendMessage(message).catch(err => {
                log('Error sending to background:', err);
            });
        } catch (e) {
            log('Error sending message:', e);
        }
    }

    /**
     * Setup MutationObserver to detect dynamically added media
     */
    function setupMutationObserver() {
        mutationObserver = new MutationObserver(mutations => {
            for (let mutation of mutations) {
                // Check added nodes
                for (let node of mutation.addedNodes) {
                    if (node.nodeType !== 1) continue; // Element nodes only

                    // Check if it's a media element
                    if (node.tagName === 'VIDEO' || node.tagName === 'AUDIO' ||
                        node.tagName === 'OBJECT' || node.tagName === 'EMBED') {
                        scheduleDetection(node);
                    }

                    // Check children
                    if (node.querySelectorAll) {
                        const mediaElements = node.querySelectorAll('video, audio, object, embed');
                        mediaElements.forEach(scheduleDetection);
                    }
                }
            }
        });

        mutationObserver.observe(document.documentElement, {
            childList: true,
            subtree: true
        });

        log('📡 MutationObserver active');
    }

    /**
     * Setup ResizeObserver to track element size changes
     */
    function setupResizeObserver() {
        resizeObserver = new ResizeObserver(entries => {
            for (let entry of entries) {
                const element = entry.target;
                if (element.__mergen_detected__) {
                    // Re-check if element became visible/large enough
                    const info = getElementInfo(element);
                    if (info && (info.width >= CONFIG.MIN_VIDEO_SIZE || info.height >= CONFIG.MIN_VIDEO_SIZE)) {
                        scheduleDetection(element);
                    }
                }
            }
        });

        log('📏 ResizeObserver active');
    }

    /**
     * Setup IntersectionObserver to track viewport visibility
     */
    function setupIntersectionObserver() {
        intersectionObserver = new IntersectionObserver(entries => {
            for (let entry of entries) {
                const element = entry.target;
                if (element.__mergen_detected__ && entry.isIntersecting) {
                    log('👁️ Media entered viewport:', element);
                    // Could send update to background if needed
                }
            }
        }, {
            threshold: 0.2
        });

        log('👁️ IntersectionObserver active');
    }

    /**
     * Schedule detection with debouncing
     */
    function scheduleDetection(element) {
        // Clear existing timer
        if (state.timers.has(element)) {
            clearTimeout(state.timers.get(element));
        }

        // Schedule new detection
        const timer = setTimeout(() => {
            detectMediaElement(element);
            state.timers.delete(element);

            // Observe for future changes
            if (resizeObserver) resizeObserver.observe(element);
            if (intersectionObserver) intersectionObserver.observe(element);
        }, CONFIG.DETECTION_DELAY);

        state.timers.set(element, timer);
    }

    /**
     * Initial scan: Find all existing media elements
     */
    function scanExistingMedia() {
        const mediaElements = document.querySelectorAll('video, audio, object, embed');
        log(`🔍 Initial scan found ${mediaElements.length} media elements`);

        mediaElements.forEach(element => {
            scheduleDetection(element);
        });
    }

    /**
     * Listen for messages from background script
     */
    function setupMessageListener() {
        browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
            if (message.type === 'get_detected_media') {
                // Return list of detected media
                const mediaList = Array.from(state.detectedMedia.values()).map(item => item.metadata);
                sendResponse({ media: mediaList });
                return true;
            }
        });
    }

    /**
     * Initialize content script
     */
    function initialize() {
        log('🚀 Mergen content script initializing...');
        log('📍 Location:', location.href);
        log('📄 Title:', document.title);
        log('🎯 Frame:', state.isTop ? 'top' : 'iframe');

        // Get frame ID
        if (browser.runtime.getFrameId) {
            state.frameId = browser.runtime.getFrameId(window);
        }

        // Setup observers
        setupMutationObserver();
        setupResizeObserver();
        setupIntersectionObserver();
        setupMessageListener();

        // Initial scan
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', scanExistingMedia);
        } else {
            scanExistingMedia();
        }

        // Platform-specific initialization
        if (location.hostname.includes('youtube.com')) {
            // Re-check periodically for YouTube (SPA navigation)
            setInterval(() => {
                scanExistingMedia();
            }, CONFIG.YOUTUBE_CHECK_INTERVAL);
        }

        log('✅ Content script initialized');
    }

    // Start initialization
    initialize();

})();
