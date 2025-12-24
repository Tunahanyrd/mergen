#!/bin/bash
# Build .deb package for Debian/Ubuntu
set -e

VERSION="0.9.3"
ARCH="amd64"
PKG_NAME="mergen_${VERSION}_${ARCH}"

# Create package structure
mkdir -p "${PKG_NAME}/DEBIAN"
mkdir -p "${PKG_NAME}/usr/bin"
mkdir -p "${PKG_NAME}/usr/share/applications"
mkdir -p "${PKG_NAME}/usr/share/icons/hicolor/128x128/apps"
mkdir -p "${PKG_NAME}/usr/share/mergen"

# Copy files (Files are moved here by CI workflow)
cp mergen "${PKG_NAME}/usr/bin/"
cp mergen.desktop "${PKG_NAME}/usr/share/applications/"
cp mergen.png "${PKG_NAME}/usr/share/icons/hicolor/128x128/apps/"
cp -r ../../browser-extension "${PKG_NAME}/usr/share/mergen/"
cp -r ../../native-host "${PKG_NAME}/usr/share/mergen/"

# Install man page
mkdir -p "${PKG_NAME}/usr/share/man/man1"
gzip -c mergen.1 > "${PKG_NAME}/usr/share/man/man1/mergen.1.gz"

# Create control file
cat > "${PKG_NAME}/DEBIAN/control" << EOF
Package: mergen
Version: ${VERSION}
Section: net
Priority: optional
Architecture: ${ARCH}
Maintainer: Tunahanyrd <tunahanyrd@gmail.com>
Depends: python3 (>= 3.8), ffmpeg
Description: Multi-threaded download manager with browser integration and stream support
 Mergen is a modern download manager featuring:
  - Multi-threaded downloads (up to 32 connections)
  - Browser integration (Chrome, Firefox, Brave, Edge)
  - Stream capture and download (HLS/DASH)
  - Resume support
  - Queue management
  - Auto-categorization
Homepage: https://github.com/Tunahanyrd/mergen
EOF

# Create postinst script
cat > "${PKG_NAME}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications
fi

# Update icon cache
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache /usr/share/icons/hicolor
fi

exit 0
EOF

chmod 755 "${PKG_NAME}/DEBIAN/postinst"

# Note: Browser extension is included as source in /usr/share/mergen/browser-extension/
# Users install via "Load Unpacked" or download ZIP from GitHub releases

# Build package
dpkg-deb --build "${PKG_NAME}"

echo "✅ Debian package created: ${PKG_NAME}.deb"
