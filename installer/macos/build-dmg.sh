#!/bin/bash
# Build DMG for macOS

VERSION="0.7.0"
APP_NAME="Mergen"

# Ensure app bundle exists
if [ ! -d "../../dist/${APP_NAME}.app" ]; then
    echo "❌ App bundle not found: ../../dist/${APP_NAME}.app"
    exit 1
fi

# Create DMG
create-dmg \
    --volname "${APP_NAME}" \
    --volicon "../../data/mergen.png" \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 100 \
    --icon "${APP_NAME}.app" 200 190 \
    --hide-extension "${APP_NAME}.app" \
    --app-drop-link 600 185 \
    "${APP_NAME}-${VERSION}.dmg" \
    "../../dist/${APP_NAME}.app"

echo "✅ DMG created: ${APP_NAME}-${VERSION}.dmg"
