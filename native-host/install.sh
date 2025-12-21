#!/bin/bash
# Cross-platform installer for Mergen Browser Integration
# Supports: Debian/Ubuntu, Arch, Fedora, macOS

set -e

echo "🌐 Mergen Browser Integration Installer"
echo "========================================"
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

echo "✅ Detected OS: $OS"
echo ""

# Install native host script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NATIVE_HOST_SCRIPT="$SCRIPT_DIR/mergen-native-host.py"

if [ "$OS" = "linux" ]; then
    # Linux: Install to ~/bin
    mkdir -p "$HOME/bin"
    cp "$NATIVE_HOST_SCRIPT" "$HOME/bin/"
    chmod +x "$HOME/bin/mergen-native-host.py"
    INSTALL_PATH="$HOME/bin/mergen-native-host.py"
    
    # Detect browser locations
    CHROME_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
    CHROMIUM_DIR="$HOME/.config/chromium/NativeMessagingHosts"
    BRAVE_DIR="$HOME/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts"
    FIREFOX_DIR="$HOME/.mozilla/native-messaging-hosts"
    
elif [ "$OS" = "macos" ]; then
    # macOS: Install to ~/Library
    mkdir -p "$HOME/Library/Application Support/Mergen"
    cp "$NATIVE_HOST_SCRIPT" "$HOME/Library/Application Support/Mergen/"
    chmod +x "$HOME/Library/Application Support/Mergen/mergen-native-host.py"
    INSTALL_PATH="$HOME/Library/Application Support/Mergen/mergen-native-host.py"
    
    # macOS browser locations
    CHROME_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
    CHROMIUM_DIR="$HOME/Library/Application Support/Chromium/NativeMessagingHosts"
    BRAVE_DIR="$HOME/Library/Application Support/BraveSoftware/Brave-Browser/NativeMessagingHosts"
    FIREFOX_DIR="$HOME/Library/Application Support/Mozilla/NativeMessagingHosts"
fi

echo "✅ Native host installed: $INSTALL_PATH"
echo ""

# Create placeholder manifests for all browsers
create_manifest() {
    local dir=$1
    local origin_type=$2
    
    mkdir -p "$dir"
    
    cat > "$dir/com.tunahanyrd.mergen.json" << EOF
{
  "name": "com.tunahanyrd.mergen",
  "description": "Mergen Download Manager Native Messaging Host",
  "path": "$INSTALL_PATH",
  "type": "stdio",
  "allowed_origins": [
    "${origin_type}://EXTENSION_ID_PLACEHOLDER/"
  ]
}
EOF
}

# Install for Chrome-based browsers
if [ -d "$(dirname "$CHROME_DIR")" ]; then
    create_manifest "$CHROME_DIR" "chrome-extension"
    echo "✅ Chrome manifest installed"
fi

if [ -d "$(dirname "$CHROMIUM_DIR")" ]; then
    create_manifest "$CHROMIUM_DIR" "chrome-extension"
    echo "✅ Chromium manifest installed"
fi

if [ -d "$(dirname "$BRAVE_DIR")" ]; then
    create_manifest "$BRAVE_DIR" "chrome-extension"
    echo "✅ Brave manifest installed"
fi

# Install for Firefox
if [ -d "$(dirname "$FIREFOX_DIR")" ]; then
    create_manifest "$FIREFOX_DIR" "moz-extension"
    echo "✅ Firefox manifest installed"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Install browser extension"
echo "2. Copy Extension ID from extension popup"
echo "3. Open Mergen → Settings → Browser Integration"
echo "4. Paste Extension ID and click 'Register'"
echo ""
echo "Extension location: $SCRIPT_DIR/../browser-extension/"
