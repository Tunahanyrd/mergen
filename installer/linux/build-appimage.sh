#!/bin/bash
# Modern AppImage builder for Mergen v0.9.5
set -e

VERSION="0.9.5"
APPDIR="Mergen.AppDir"

echo "📦 Building AppImage: Mergen-${VERSION}-x86_64.AppImage"

# Clean previous
rm -rf "${APPDIR}"

# Create structure
mkdir -p "${APPDIR}/usr/"{bin,share/applications,share/icons/hicolor/512x512/apps,share/mergen,lib}

echo "→ Copying files..."

# Copy binary
cp mergen "${APPDIR}/usr/bin/"
chmod +x "${APPDIR}/usr/bin/mergen"

# Copy desktop file and icon
cp ../../data/mergen.desktop "${APPDIR}/usr/share/applications/"
cp ../../data/mergen.png "${APPDIR}/usr/share/icons/hicolor/512x512/apps/"
cp ../../data/mergen.png "${APPDIR}/mergen.png"  # AppImage icon
cp ../../data/mergen.desktop "${APPDIR}/"

# Copy browser extension
cp -r ../../browser-extension "${APPDIR}/usr/share/mergen/"
cp -r ../../native-host "${APPDIR}/usr/share/mergen/"

# Create AppRun with browser setup
cat > "${APPDIR}/AppRun" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}

export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"

# Setup native messaging on first run
NATIVE_JSON="${HERE}/usr/share/mergen/native-host/com.mergen.native.json"

# Chrome
CHROME_DIR="$HOME/.config/google-chrome/NativeMessagingHosts"
[ -d "$CHROME_DIR" ] && ln -sf "$NATIVE_JSON" "$CHROME_DIR/com.mergen.native.json" 2>/dev/null || true

# Chromium
CHROMIUM_DIR="$HOME/.config/chromium/NativeMessagingHosts"
[ -d "$CHROMIUM_DIR" ] && ln -sf "$NATIVE_JSON" "$CHROMIUM_DIR/com.mergen.native.json" 2>/dev/null || true

# Firefox
FIREFOX_DIR="$HOME/.mozilla/native-messaging-hosts"
[ -d "$FIREFOX_DIR" ] && ln -sf "$NATIVE_JSON" "$FIREFOX_DIR/com.mergen.native.json" 2>/dev/null || true

# Brave
BRAVE_DIR="$HOME/.config/BraveSoftware/Brave-Browser/NativeMessagingHosts"
[ -d "$BRAVE_DIR" ] && ln -sf "$NATIVE_JSON" "$BRAVE_DIR/com.mergen.native.json" 2>/dev/null || true

# Launch app
exec "${HERE}/usr/bin/mergen" "$@"
EOF

chmod +x "${APPDIR}/AppRun"

# Use appimagetool
APPIMAGETOOL_BIN="${APPIMAGETOOL:-appimagetool}"

echo "→ Running appimagetool..."

# Build AppImage
ARCH=x86_64 "$APPIMAGETOOL_BIN" --appimage-extract-and-run "${APPDIR}" "Mergen-${VERSION}-x86_64.AppImage"

if [ -f "Mergen-${VERSION}-x86_64.AppImage" ]; then
    chmod +x "Mergen-${VERSION}-x86_64.AppImage"
    SIZE=$(du -h "Mergen-${VERSION}-x86_64.AppImage" | cut -f1)
    echo ""
    echo "✅ AppImage created successfully!"
    echo "   File: Mergen-${VERSION}-x86_64.AppImage"
    echo "   Size: ${SIZE}"
    echo ""
    echo "Run with: ./Mergen-${VERSION}-x86_64.AppImage"
else
    echo "❌ Failed to create AppImage"
    exit 1
fi