#!/bin/bash
# Mergen Browser Extension Helper
# Opens necessary folders and pages to make installation easier

echo "🚀 Mergen Browser Extension Helper"
echo "=================================="

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     xdg_open="xdg-open";;
    Darwin*)    xdg_open="open";;
    *)          xdg_open="echo";;
esac

# 1. Open Extension Folder
EXT_DIR="/usr/share/mergen/browser-extension"
if [ ! -d "$EXT_DIR" ]; then
    # Fallback for dev environment or local run
    EXT_DIR="$(dirname $(readlink -f $0))/browser-extension"
fi

echo "📂 Opening extension folder: $EXT_DIR"
$xdg_open "$EXT_DIR" &

# 2. Open Browser Extension Pages
echo "🌐 Opening browser extension pages..."

# Chrome / Chromium
echo "  • Chrome: chrome://extensions (Please enable Developer Mode)"
google-chrome "chrome://extensions" 2>/dev/null || chromium "chrome://extensions" 2>/dev/null &

# Firefox
echo "  • Firefox: about:debugging#/runtime/this-firefox"
firefox "about:debugging#/runtime/this-firefox" 2>/dev/null &

echo ""
echo "📋 TO INSTALL:"
echo "1. Enable 'Developer Mode' in your browser."
echo "2. Drag and drop the 'browser-extension' folder (opened) into the browser window."
echo "   OR use 'Load Unpacked' button."
echo "3. Copy the Extension ID and paste it into Mergen Settings > Browser Integration."
echo ""
read -p "Press Enter to exit..."
