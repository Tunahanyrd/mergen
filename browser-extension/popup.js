/**
 * Popup Script - Media Detection UI
 */

// Load detected media on popup open
document.addEventListener('DOMContentLoaded', () => {
    loadDetectedMedia();

    // Add current page button
    document.getElementById('add-current').addEventListener('click', addCurrentPage);

    // Download all media button
    document.getElementById('download-all').addEventListener('click', downloadAllMedia);

    // Clear media list button
    document.getElementById('clear-media').addEventListener('click', clearMediaList);
});

/**
 * Load and display detected media
 */
function loadDetectedMedia() {
    chrome.runtime.sendMessage({ action: 'getDetectedMedia' }, (response) => {
        if (response && response.media) {
            displayMediaList(response.media);
        }
    });
}

/**
 * Display media list in popup
 */
function displayMediaList(mediaArray) {
    const mediaList = document.getElementById('media-list');
    const mediaCount = document.getElementById('media-count');
    const downloadAll = document.getElementById('download-all');
    const clearBtn = document.getElementById('clear-media');

    mediaCount.textContent = mediaArray.length;

    if (mediaArray.length === 0) {
        mediaList.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 48px; margin-bottom: 12px;">🔍</div>
                <div>No media detected yet</div>
                <div style="font-size: 12px; margin-top: 8px; opacity: 0.7;">
                    Browse any site with videos
                </div>
            </div>
        `;
        downloadAll.style.display = 'none';
        clearBtn.style.display = 'none';
        return;
    }

    // Show buttons
    downloadAll.style.display = 'block';
    clearBtn.style.display = 'block';

    // Build media list
    mediaList.innerHTML = mediaArray.map(media => {
        const icon = getMediaIcon(media.type);
        return `
            <div class="media-item">
                <div class="media-icon">${icon}</div>
                <div class="media-info">
                    <div class="media-name" title="${media.filename}">${media.filename}</div>
                    <div class="media-type">${media.type}</div>
                </div>
                <button class="download-btn" data-url="${escapeHtml(media.url)}">
                    📥 Download
                </button>
            </div>
        `;
    }).join('');

    // Add click listeners to download buttons
    mediaList.querySelectorAll('.download-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const url = btn.getAttribute('data-url');
            downloadMedia(url);
        });
    });
}

/**
 * Get icon for media type
 */
function getMediaIcon(type) {
    const icons = {
        'video': '🎥',
        'audio': '🎵',
        'stream': '📡',
        'playlist': '📋',
        'unknown': '📄'
    };
    return icons[type] || icons['unknown'];
}

/**
 * Download single media file
 */
function downloadMedia(url) {
    showStatus('Sending to Mergen...', false);

    chrome.runtime.sendMessage({
        action: 'downloadMedia',
        url: url
    }, (response) => {
        if (response && response.status === 'ok') {
            showStatus('✅ Added to Mergen!', false);
        } else {
            showStatus('❌ Failed to send to Mergen', true);
        }
    });
}

/**
 * Download all detected media
 */
function downloadAllMedia() {
    chrome.runtime.sendMessage({ action: 'getDetectedMedia' }, (response) => {
        if (response && response.media) {
            const count = response.media.length;
            showStatus(`📥 Sending ${count} files to Mergen...`, false);

            response.media.forEach((media, index) => {
                setTimeout(() => {
                    downloadMedia(media.url);
                }, index * 100); // Stagger requests
            });
        }
    });
}

/**
 * Clear media list
 */
function clearMediaList() {
    chrome.runtime.sendMessage({ action: 'clearDetectedMedia' }, () => {
        loadDetectedMedia();
        showStatus('🗑️ Media list cleared', false);
    });
}

/**
 * Add current page URL
 */
function addCurrentPage() {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
            const url = tabs[0].url;
            showStatus('Sending current page...', false);

            fetch('http://localhost:8765/add_download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            })
                .then(response => response.json())
                .then(data => {
                    showStatus('✅ Added to Mergen!', false);
                })
                .catch(error => {
                    showStatus('❌ Mergen not running?', true);
                });
        }
    });
}

/**
 * Show status message
 */
function showStatus(message, isError) {
    const statusDiv = document.getElementById('status-message');
    statusDiv.textContent = message;
    statusDiv.className = 'status' + (isError ? ' error' : '');
    statusDiv.style.display = 'block';

    setTimeout(() => {
        statusDiv.style.display = 'none';
    }, 3000);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Listen for media detection updates
chrome.runtime.onMessage.addListener((request) => {
    if (request.action === 'mediaDetected') {
        loadDetectedMedia();
    }
});
