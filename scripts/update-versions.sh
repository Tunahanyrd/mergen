#!/bin/bash
# update-versions.sh - Update all version references to 0.9.5

NEW_VERSION="0.9.5"

echo "🔧 Updating all version references to ${NEW_VERSION}..."

# Update build.sh
sed -i "s/VERSION=\".*\"/VERSION=\"${NEW_VERSION}\"/" build.sh
sed -i "s/v0\.7\.0/v${NEW_VERSION}/g" build.sh
echo "✅ build.sh updated"

# Update Linux installer scripts
sed -i "s/VERSION=\".*\"/VERSION=\"${NEW_VERSION}\"/" installer/linux/build-deb.sh
echo "✅ build-deb.sh updated"

sed -i "s/VERSION=\".*\"/VERSION=\"${NEW_VERSION}\"/" installer/linux/build-appimage.sh
echo "✅ build-appimage.sh updated"

# Update RPM script (needs inspection first)
if [ -f installer/linux/build-rpm.sh ]; then
    sed -i "s/VERSION=\".*\"/VERSION=\"${NEW_VERSION}\"/" installer/linux/build-rpm.sh
    echo "✅ build-rpm.sh updated"
fi

# Update PKGBUILD
sed -i "s/pkgver=.*/pkgver=${NEW_VERSION}/" installer/linux/PKGBUILD
sed -i "s/pkgrel=.*/pkgrel=1/" installer/linux/PKGBUILD
echo "✅ PKGBUILD updated"

# Update dmg
sed -i "s/pkgver=.*/pkgver=${NEW_VERSION}/" installer/macos/build-dmg.sh
echo "✅ build-dmg.sh updated"

# Update Inno Setup
sed -i "s/#define MyAppVersion \".*\"/#define MyAppVersion \"${NEW_VERSION}\"/" installer/windows/mergen.iss
echo "✅ mergen.iss updated"

echo ""
echo "🎉 All versions updated to ${NEW_VERSION}!"
echo ""
echo "Next steps:"
echo "1. Review changes: git diff"
echo "2. Commit: git commit -am 'Update version to ${NEW_VERSION}'"
echo "3. Tag: git tag -a v${NEW_VERSION} -m 'Release v${NEW_VERSION}'"
echo "4. Push: git push origin main && git push origin v${NEW_VERSION}"
