#!/bin/bash
# Build AppImage for Linux (universal)

VERSION="0.7.0"
APPDIR="Mergen.AppDir"

# Create AppDir structure
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/128x128/apps"
mkdir -p "${APPDIR}/usr/share/mergen"

# Copy files
cp ../../dist/mergen "${APPDIR}/usr/bin/"
cp ../../data/mergen.desktop "${APPDIR}/usr/share/applications/"
cp ../../data/mergen.png "${APPDIR}/usr/share/icons/hicolor/128x128/apps/"
cp ../../data/mergen.png "${APPDIR}/mergen.png"  # AppImage icon
cp ../../data/mergen.desktop "${APPDIR}/"
cp -r ../../browser-extension "${APPDIR}/usr/share/mergen/"
cp -r ../../native-host "${APPDIR}/usr/share/mergen/"

# Create AppRun
cat > "${APPDIR}/AppRun" << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/mergen" "$@"
EOF

chmod +x "${APPDIR}/AppRun"

# Build AppImage
../../appimagetool-x86_64.AppImage "${APPDIR}" "Mergen-${VERSION}-x86_64.AppImage"

echo "✅ AppImage created: Mergen-${VERSION}-x86_64.AppImage"
