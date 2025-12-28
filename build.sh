#!/bin/bash
# Modern build script for Mergen v0.9.5
# Supports Linux, macOS, Windows (via WSL/MSYS2)

set -e

VERSION="0.9.5"
APP_NAME="Mergen"

echo "🚀 Building ${APP_NAME} v${VERSION}"
echo "Platform: $(uname -s)"
echo "================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check dependencies
echo "📦 Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓${NC} Python ${PYTHON_VERSION}"

# Install PyInstaller if needed
if ! command -v uv &> /dev/null; then
    echo "⚠️ uv not found. Installing uv..."
    pip install uv
fi

if ! uv pip show --system pyinstaller &> /dev/null; then
    echo "📦 Installing PyInstaller via uv..."
    uv pip install --system pyinstaller
fi

echo -e "${GREEN}✓${NC} PyInstaller installed"

# Clean previous builds
echo ""
echo "🧹 Cleaning previous builds..."
rm -rf build dist *.spec
echo -e "${GREEN}✓${NC} Clean complete"

# Detect platform
PLATFORM=$(uname -s)
ICON_FILE="data/mergen.png"

if [[ "$PLATFORM" == "Darwin" ]]; then
    ICON_FILE="data/mergen.icns"
    BUILD_TYPE="--onedir"
    OUTPUT_NAME="${APP_NAME}"
elif [[ "$PLATFORM" == "MINGW"* ]] || [[ "$PLATFORM" == "MSYS"* ]]; then
    ICON_FILE="data/mergen.ico"
    BUILD_TYPE="--onefile"
    OUTPUT_NAME="${APP_NAME,,}"  # lowercase
else
    # Linux
    BUILD_TYPE="--onefile"
    OUTPUT_NAME="${APP_NAME,,}"
fi

echo ""
echo "🔨 Building ${PLATFORM} binary..."

# Modern PyInstaller command with all optimizations
pyinstaller \
    ${BUILD_TYPE} \
    --name "${OUTPUT_NAME}" \
    --icon "${ICON_FILE}" \
    --windowed \
    --noconfirm \
    --clean \
    \
    `# Data files` \
    --add-data "data${SEP}data" \
    --add-data "browser-extension${SEP}browser-extension" \
    --add-data "native-host${SEP}native-host" \
    \
    `# Hidden imports for Qt6` \
    --hidden-import PySide6.QtCore \
    --hidden-import PySide6.QtGui \
    --hidden-import PySide6.QtWidgets \
    --hidden-import PySide6.QtNetwork \
    --hidden-import PySide6.QtSvg \
    \
    `# Hidden imports for downloaders` \
    --hidden-import httpx \
    --hidden-import httpx._transports.default \
    --hidden-import httpx._transports.asgi \
    --hidden-import requests \
    --hidden-import urllib3 \
    \
    `# Hidden imports for yt-dlp` \
    --hidden-import yt_dlp \
    --hidden-import yt_dlp.extractor \
    --hidden-import yt_dlp.extractor.common \
    --hidden-import yt_dlp.extractor.generic \
    --hidden-import yt_dlp.utils \
    --hidden-import yt_dlp.postprocessor \
    --hidden-import yt_dlp.downloader \
    \
    `# Exclude unnecessary modules for smaller size` \
    --exclude-module matplotlib \
    --exclude-module numpy \
    --exclude-module pandas \
    --exclude-module scipy \
    --exclude-module PIL.ImageTk \
    --exclude-module tkinter \
    \
    `# Optimization` \
    --strip \
    --noupx \
    \
    main.py

echo -e "${GREEN}✓${NC} Binary built successfully"

# Platform-specific packaging
echo ""
echo "📦 Creating platform package..."

if [[ "$PLATFORM" == "Linux" ]]; then
    echo "→ Linux AppImage structure"
    
    APPDIR="dist/${APP_NAME}.AppDir"
    mkdir -p "${APPDIR}/usr/"{bin,share/applications,share/icons/hicolor/512x512/apps,share/mergen}
    
    # Copy binary
    cp "dist/${OUTPUT_NAME}" "${APPDIR}/usr/bin/"
    
    # Copy desktop file and icon
    cp data/mergen.desktop "${APPDIR}/usr/share/applications/"
    cp data/mergen.png "${APPDIR}/usr/share/icons/hicolor/512x512/apps/"
    cp data/mergen.png "${APPDIR}/mergen.png"
    cp data/mergen.desktop "${APPDIR}/"
    
    # Copy browser extension
    cp -r browser-extension "${APPDIR}/usr/share/mergen/"
    cp -r native-host "${APPDIR}/usr/share/mergen/"
    
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
    
    echo -e "${GREEN}✓${NC} AppImage structure created"
    echo -e "${YELLOW}→${NC} Run 'appimagetool ${APPDIR}' to create AppImage"
    
elif [[ "$PLATFORM" == "Darwin" ]]; then
    echo "→ macOS App Bundle"
    
    if [ -d "dist/${OUTPUT_NAME}.app" ]; then
        echo -e "${GREEN}✓${NC} App bundle created: dist/${OUTPUT_NAME}.app"
        
        # Optional: Create DMG
        if command -v create-dmg &> /dev/null; then
            echo "→ Creating DMG..."
            create-dmg \
                --volname "${APP_NAME} ${VERSION}" \
                --window-pos 200 120 \
                --window-size 600 400 \
                --icon-size 100 \
                --icon "${OUTPUT_NAME}.app" 175 120 \
                --hide-extension "${OUTPUT_NAME}.app" \
                --app-drop-link 425 120 \
                "dist/${APP_NAME}-${VERSION}.dmg" \
                "dist/${OUTPUT_NAME}.app"
            echo -e "${GREEN}✓${NC} DMG created: dist/${APP_NAME}-${VERSION}.dmg"
        fi
    fi
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 Build Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Version: ${VERSION}"
echo "Platform: ${PLATFORM}"
echo ""
echo "Output directory: ./dist/"
ls -lh dist/ | tail -n +2
echo ""

# Next steps
if [[ "$PLATFORM" == "Linux" ]]; then
    echo "Next steps:"
    echo "  1. Create AppImage: appimagetool dist/${APP_NAME}.AppDir"
    echo "  2. Or run installers: cd installer/linux && ./build-deb.sh"
fi
