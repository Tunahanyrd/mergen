/**
 * Mergen Extension Popup
 * Shows detected media with download buttons
 */

const browser = chrome || browser;

// Get platform emoji
function getPlatformEmoji(platform) {
    const emojis = {
        'youtube': '▶️',
        'instagram': '📸',
        'twitter': '🐦',
        'vimeo': '🎬',
        'default': '🎥'
    };
    return emojis[platform] || emojis.default;
}

// Format size
function formatSize(width, height) {
    if (!width || !height) return '';
    return `${width}×${height}`;
}

// Format duration
function formatDuration(seconds) {
    if (!seconds) return '';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Create media item element
function createMediaItem(stream) {
    const metadata = stream.metadata || {};
    const type = stream.type || 'video';
    const platform = stream.platform || metadata.platform;

    const item = document.createElement('div');
    item.className = 'media-item';

    // Icon
    const icon = document.createElement('div');
    icon.className = 'media-icon';
    icon.textContent = getPlatformEmoji(platform);

    // Info
    const info = document.createElement('div');
    info.className = 'media-info';

    const title = document.createElement('div');
    title.className = 'media-title';

    // Get title from various sources (with safe navigation)
    const titleText = (metadata.platformData && metadata.platformData.title) ||
        metadata.pageTitle ||
        (metadata.pageUrl ? new URL(metadata.pageUrl).hostname : 'Video');
    title.textContent = titleText;

    const meta = document.createElement('div');
    meta.className = 'media-meta';

    if (platform) {
        const platformBadge = document.createElement('span');
        platformBadge.className = 'platform-badge';
        platformBadge.textContent = platform;
        meta.appendChild(platformBadge);
    }

    const size = formatSize(metadata.width, metadata.height);
    if (size) {
        const sizeText = document.createElement('span');
        sizeText.textContent = size;
        meta.appendChild(sizeText);
    }

    const typeText = document.createElement('span');
    typeText.textContent = type === 'blob' ? 'video' : type;
    meta.appendChild(typeText);

    info.appendChild(title);
    info.appendChild(meta);

    // Download button
    const downloadBtn = document.createElement('button');
    downloadBtn.className = 'download-btn';
    downloadBtn.textContent = '⬇ Download';
    downloadBtn.onclick = (e) => {
        e.stopPropagation();
        downloadMedia(stream);
    };

    item.appendChild(icon);
    item.appendChild(info);
    item.appendChild(downloadBtn);

    return item;
}

// Download media
async function downloadMedia(stream) {
    console.log('📥 Downloading:', stream);

    const { metadata, url } = stream;

    // For blob URLs (YouTube/Instagram), use pageUrl for yt-dlp
    const downloadUrl = metadata.isBlob ? metadata.pageUrl : metadata.url;

    // Send to background to forward to Mergen
    try {
        const response = await browser.runtime.sendMessage({
            type: 'download_media',
            url: downloadUrl,
            metadata: metadata
        });

        console.log('✅ Download request sent:', response);

        // Show feedback
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✓ Sent to Mergen';
        btn.style.background = '#2196F3';

        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
        }, 2000);

    } catch (error) {
        console.error('❌ Download failed:', error);
        alert('Failed to send to Mergen. Make sure the app is running!');
    }
}

// Load detected media
async function loadDetectedMedia() {
    console.log('🔍 Loading detected media...');

    const loadingState = document.getElementById('loadingState');
    const emptyState = document.getElementById('emptyState');
    const mediaList = document.getElementById('mediaList');
    const mediaCount = document.getElementById('mediaCount');

    try {
        // Get detected streams from background
        console.log('📤 Sending get_detected_media request...');
        const response = await browser.runtime.sendMessage({
            type: 'get_detected_media'
        });

        console.log('📥 Response from background:', response);

        const streams = response.streams || [];

        console.log(`✅ Received ${streams.length} streams`);

        mediaCount.textContent = streams.length;

        if (streams.length === 0) {
            console.log('📭 No media detected - showing empty state');
            loadingState.style.display = 'none';
            emptyState.style.display = 'block';
            mediaList.style.display = 'none';
        } else {
            console.log(`📺 Displaying ${streams.length} media items`);
            loadingState.style.display = 'none';
            emptyState.style.display = 'none';
            mediaList.style.display = 'block';

            // Clear existing items
            mediaList.innerHTML = '';

            // Add media items
            streams.forEach((stream, index) => {
                console.log(`  ${index + 1}. ${stream.metadata?.pageTitle || stream.url?.substring(0, 50)}`);
                const item = createMediaItem(stream);
                mediaList.appendChild(item);
            });

            console.log('✅ Media list rendered');
        }

    } catch (error) {
        console.error('❌ Error loading media:', error);
        loadingState.textContent = 'Error loading media: ' + error.message;
    }
}

// Initialize popup
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Popup initialized');
    loadDetectedMedia();
});
