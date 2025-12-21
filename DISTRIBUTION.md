# Distribution Guide

## Building Binaries

### Linux
```bash
./build.sh
# Output: dist/mergen (binary)
# Output: dist/Mergen.AppDir/ (AppImage structure)
```

**Create AppImage:**
```bash
# Install appimagetool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# Build AppImage
./appimagetool-x86_64.AppImage dist/Mergen.AppDir dist/Mergen-x86_64.AppImage
```

### macOS
```bash
./build.sh
# Output: dist/Mergen.app (app bundle)
# Output: dist/Mergen.dmg (if create-dmg installed)
```

### Windows
```powershell
python -m PyInstaller --onefile --windowed --name mergen --icon data/mergen.png main.py
# Output: dist/mergen.exe
```

## Package Managers

### Arch Linux (AUR)
Create `PKGBUILD`:
```bash
pkgname=mergen
pkgver=0.7.0
pkgrel=1
pkgdesc="Multi-threaded download manager with browser integration"
arch=('x86_64')
url="https://github.com/Tunahanyrd/mergen"
license=('GPL3')
depends=('python' 'python-pyside6' 'python-requests')
source=("$pkgname-$pkgver.tar.gz::$url/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')

package() {
    cd "$srcdir/$pkgname-$pkgver"
    python setup.py install --root="$pkgdir" --optimize=1
    install -Dm644 data/mergen.desktop "$pkgdir/usr/share/applications/mergen.desktop"
    install -Dm644 data/mergen.png "$pkgdir/usr/share/icons/hicolor/128x128/apps/mergen.png"
}
```

### Debian/Ubuntu (.deb)
```bash
# Create debian/ directory structure
# Use dh_make or create control files manually
dpkg-buildpackage -us -uc
```

### Homebrew (macOS)
Create formula:
```ruby
class Mergen < Formula
  desc "Multi-threaded download manager"
  homepage "https://github.com/Tunahanyrd/mergen"
  url "https://github.com/Tunahanyrd/mergen/archive/v0.7.0.tar.gz"
  sha256 "..."
  
  depends_on "python@3.11"
  
  def install
    system "python3", "setup.py", "install", "--prefix=#{prefix}"
  end
end
```

## GitHub Release

1. Tag version:
```bash
git tag -a v0.7.0 -m "Release v0.7.0"
git push origin v0.7.0
```

2. Create release on GitHub
3. Upload artifacts:
   - `Mergen-x86_64.AppImage` (Linux)
   - `Mergen.dmg` (macOS)
   - `mergen-win64.exe` (Windows)
   - `mergen-browser-extension.zip`
   - Source code (auto)

## Extension Stores

### Chrome Web Store
1. Create developer account ($5 fee)
2. Zip extension: `mergen-browser-extension.zip`
3. Upload to Chrome Web Store Dashboard
4. Fill metadata
5. Submit for review (~1-3 days)

### Mozilla Add-ons (AMO)
1. Create account (free)
2. Upload `mergen-firefox-amo.zip`
3. Fill metadata
4. Submit for review (~1-2 weeks)
5. Extension ID: `mergen@tunahanyrd.com`
