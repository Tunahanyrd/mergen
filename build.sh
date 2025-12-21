#!/bin/bash
# Build Mergen for all platforms

echo "🔨 Building Mergen v0.7.0"
echo "========================="

# Check PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist

# Build for current platform
echo "Building binary..."
pyinstaller --onefile \
    --windowed \
    --name mergen \
    --icon data/mergen.png \
    --add-data "data:data" \
    --add-data "browser-extension:browser-extension" \
    --add-data "native-host:native-host" \
    --hidden-import PySide6.QtCore \
    --hidden-import PySide6.QtGui \
    --hidden-import PySide6.QtWidgets \
    main.py

echo "✅ Binary built: dist/mergen"

# Platform-specific packaging
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Creating Linux package..."
    
    # Create AppImage structure
    mkdir -p dist/Mergen.AppDir/usr/{bin,share/applications,share/icons/hicolor/128x128/apps}
    
    cp dist/mergen dist/Mergen.AppDir/usr/bin/
    cp data/mergen.desktop dist/Mergen.AppDir/usr/share/applications/
    cp data/mergen.png dist/Mergen.AppDir/usr/share/icons/hicolor/128x128/apps/
    
    # Create AppRun
    cat > dist/Mergen.AppDir/AppRun << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
exec "${HERE}/usr/bin/mergen" "$@"
EOF
    chmod +x dist/Mergen.AppDir/AppRun
    
    echo "✅ AppImage structure ready (needs appimagetool to package)"
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Creating macOS App Bundle..."
    
    # PyInstaller creates .app automatically with --windowed
    if [ -d "dist/mergen.app" ]; then
        mv dist/mergen.app dist/Mergen.app
        echo "✅ macOS app bundle: dist/Mergen.app"
        
        # Optional: Create DMG
        if command -v create-dmg &> /dev/null; then
            create-dmg \
                --volname "Mergen" \
                --window-size 600 400 \
                --icon-size 100 \
                --app-drop-link 450 185 \
                dist/Mergen.dmg \
                dist/Mergen.app
            echo "✅ DMG created: dist/Mergen.dmg"
        fi
    fi
fi

echo ""
echo "🎉 Build complete!"
echo "Output: dist/"
ls -lh dist/
