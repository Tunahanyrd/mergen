#!/bin/bash
# Modern .deb package builder for Mergen v0.9.5
set -e

VERSION="0.9.5"
ARCH="amd64"
PKG_NAME="mergen_${VERSION}_${ARCH}"

echo "📦 Building Debian package: ${PKG_NAME}.deb"

# Create package structure
mkdir -p "${PKG_NAME}/DEBIAN"
mkdir -p "${PKG_NAME}/usr/bin"
mkdir -p "${PKG_NAME}/usr/share/applications"
mkdir -p "${PKG_NAME}/usr/share/icons/hicolor/512x512/apps"
mkdir -p "${PKG_NAME}/usr/share/mergen"
mkdir -p "${PKG_NAME}/usr/share/man/man1"

# Copy files
echo "→ Copying files..."
cp mergen "${PKG_NAME}/usr/bin/"
chmod +x "${PKG_NAME}/usr/bin/mergen"

cp mergen.desktop "${PKG_NAME}/usr/share/applications/"
cp mergen.png "${PKG_NAME}/usr/share/icons/hicolor/512x512/apps/"

# Copy browser extension and native host
cp -r ../../browser-extension "${PKG_NAME}/usr/share/mergen/"
cp -r ../../native-host "${PKG_NAME}/usr/share/mergen/"

# Install man page
gzip -c mergen.1 > "${PKG_NAME}/usr/share/man/man1/mergen.1.gz"

# Create control file
cat > "${PKG_NAME}/DEBIAN/control" << EOF
Package: mergen
Version: ${VERSION}
Section: net
Priority: optional
Architecture: ${ARCH}
Maintainer: Tunahanyrd <tunahanyrd@gmail.com>
Depends: python3 (>= 3.9), ffmpeg, libxcb-xinerama0, libxcb-cursor0
Recommends: yt-dlp
Suggests: google-chrome-stable | chromium-browser | firefox | brave-browser
Description: Multi-threaded download manager with browser integration
 Mergen is a modern, feature-rich download manager featuring:
  * Multi-threaded downloads (up to 64 connections)
  * Browser integration (Chrome, Firefox, Brave, Edge)
  * Stream capture and download (HLS/DASH/M3U8)
  * YouTube and social media support (via yt-dlp)
  * Resume support and queue management
  * Auto-categorization by file type
  * Native messaging for seamless browser integration
  * Dark/Light theme support
Homepage: https://github.com/Tunahanyrd/mergen
EOF

# Create postinst script
cat > "${PKG_NAME}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

echo "Configuring Mergen..."

# Update desktop database
if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database /usr/share/applications
fi

# Update icon cache
if command -v gtk-update-icon-cache > /dev/null 2>&1; then
    gtk-update-icon-cache /usr/share/icons/hicolor 2> /dev/null || true
fi

# Setup native messaging for browsers
NATIVE_HOST_JSON="/usr/share/mergen/native-host/com.mergen.native.json"

# Chrome
CHROME_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
mkdir -p "$CHROME_DIR"
ln -sf "$NATIVE_HOST_JSON" "$CHROME_DIR/com.mergen.native.json" 2>/dev/null || true

# Chromium
CHROMIUM_DIR="$HOME/.config/chromium/NativeMessagingHosts"
mkdir -p "$CHROMIUM_DIR"
ln -sf "$NATIVE_HOST_JSON" "$CHROMIUM_DIR/com.mergen.native.json" 2>/dev/null || true

# Firefox
FIREFOX_DIR="$HOME/.mozilla/native-messaging-hosts"
mkdir -p "$FIREFOX_DIR"
ln -sf "$NATIVE_HOST_JSON" "$FIREFOX_DIR/com.mergen.native.json" 2>/dev/null || true

# Brave
BRAVE_DIR="$HOME/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts"
mkdir -p "$BRAVE_DIR"
ln -sf "$NATIVE_HOST_JSON" "$BRAVE_DIR/com.mergen.native.json" 2>/dev/null || true

echo "✅ Mergen installed successfully!"
echo ""
echo "To install the browser extension:"
echo "  1. Open browser extensions page"
echo "  2. Enable 'Developer mode'"
echo "  3. Click 'Load unpacked'"
echo "  4. Select: /usr/share/mergenrowser-extension/"

exit 0
EOF

chmod 755 "${PKG_NAME}/DEBIAN/postinst"

# Create prerm script (cleanup)
cat > "${PKG_NAME}/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

# Remove native messaging symlinks
rm -f "$HOME/.config/google-chrome/NativeMessagingHosts/com.mergen.native.json"
rm -f "$HOME/.config/chromium/NativeMessagingHosts/com.mergen.native.json"
rm -f "$HOME/.mozilla/native-messaging-hosts/com.mergen.native.json"
rm -f "$HOME/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts/com.mergen.native.json"

exit 0
EOF

chmod 755 "${PKG_NAME}/DEBIAN/prerm"

# Build package
echo "→ Building .deb..."
dpkg-deb --build "${PKG_NAME}"

# Verify
if [ -f "${PKG_NAME}.deb" ]; then
    SIZE=$(du -h "${PKG_NAME}.deb" | cut -f1)
    echo ""
    echo "✅ Debian package created successfully!"
    echo "   File: ${PKG_NAME}.deb"
    echo "   Size: ${SIZE}"
    echo ""
    echo "Install with:"
    echo "  sudo dpkg -i ${PKG_NAME}.deb"
    echo "  sudo apt-get install -f  # Fix dependencies"
else
    echo "❌ Failed to create package"
    exit 1
fi
