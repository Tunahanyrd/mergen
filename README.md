# 🔽 MERGEN - Multi-threaded Download Manager

[![GitHub release](https://img.shields.io/github/v/release/Tunahanyrd/mergen)](https://github.com/Tunahanyrd/mergen/releases)
[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)](https://github.com/Tunahanyrd/mergen)

Modern, fast, and feature-rich download manager with browser integration.

## ✨ Features

- ⚡ **Multi-threaded Downloads** - Up to 32 parallel connections
- 🌐 **Browser Integration** - Capture downloads from Chrome, Firefox, Brave, Edge
- ⏸️ **Resume Support** - Resume interrupted downloads
- 📊 **Queue Management** - Organize downloads in queues
- 🎨 **Modern UI** - Dark theme with glassmorphism design
- 🌍 **i18n Support** - English and Turkish
- 📂 **Auto-categorization** - Smart file type detection
- 🔔 **System Tray** - Minimize to tray
- 📥 **Pre-download Dialog** - Configure before downloading

## 📦 Installation

### Pre-built Packages (Recommended)

Download the latest release for your platform:

**🪟 Windows:**
- [**MergenSetup.exe**](https://github.com/Tunahanyrd/mergen/releases/latest/download/MergenSetup.exe) - Installer with auto-update

**🐧 Linux:**
- [**Debian/Ubuntu (.deb)**](https://github.com/Tunahanyrd/mergen/releases/latest) - `sudo dpkg -i mergen_0.7.0-1_amd64.deb`
- [**Fedora/RHEL (.rpm)**](https://github.com/Tunahanyrd/mergen/releases/latest) - `sudo rpm -i mergen-0.7.0-1.x86_64.rpm`
- [**AppImage**](https://github.com/Tunahanyrd/mergen/releases/latest) - Universal binary for all distros
- [**Arch Linux (.pkg.tar.zst)**](https://github.com/Tunahanyrd/mergen/releases/latest) - `sudo pacman -U mergen-0.7.0-1-x86_64.pkg.tar.zst`

**🍎 macOS:**
- [**Mergen.dmg**](https://github.com/Tunahanyrd/mergen/releases/latest) - Drag & drop to Applications

### Requirements

- Python 3.8+
- PySide6
- requests
- httpx

### From Source

```bash
git clone https://github.com/Tunahanyrd/mergen.git
cd mergen
pip install -r requirements.txt
./main.py
```

## 🌐 Browser Integration (Manual Installation)

### Why Manual Installation?

We distribute the extension directly to avoid store fees ($5) and approval delays. Installation takes ~2 minutes!

### Step 1: Install Native Host

```bash
cd native-host
./install.sh
```

This installs the native messaging host to `~/bin/` and creates manifests for all browsers.

### Step 2: Install Browser Extension

#### Chrome / Chromium / Brave / Edge

**Option A: Load Unpacked (Persistent)**

1. Download or locate: `browser-extension/` folder
2. Open: `chrome://extensions/`
3. Enable **"Developer mode"** (toggle in top-right)
4. Click **"Load unpacked"**
5. Select the `browser-extension/` folder
6. ✅ Extension installed!

**Option B: Drag & Drop**

1. Download: `mergen-browser-extension.zip`
2. Open: `chrome://extensions/`
3. Drag & drop the .zip file onto the page
4. ✅ Extension installed!

#### Firefox

**Temporary Installation (Until AMO Approval):**

1. Open: `about:debugging#/runtime/this-firefox`
2. Click **"Load Temporary Add-on..."**
3. Select: `mergen-firefox-amo.zip` or `browser-extension/manifest.json`
4. ⚠️ **Note:** Removed on browser restart

**Permanent Installation:**

- Extension submitted to Mozilla Add-ons (AMO)
- Approval pending (~1-2 weeks)
- Once approved: Install from addons.mozilla.org
- Will be permanent and auto-update

**Alternative (Developer):**

- Use Firefox Developer Edition
- `about:config` → `xpinstall.signatures.required` → `false`
- Extension becomes permanent

### Step 3: Register Extension in Mergen

1. **Click the extension icon** in your browser toolbar
2. **Copy the Extension ID** shown in the popup
3. Open **Mergen** → **Settings** → **Browser Integration**
4. **Paste the Extension ID** and click **"Register"**
5. **Reload the extension** in your browser
6. ✅ **Done!** Try right-clicking any link → "Download with Mergen"

### How It Works

```
Browser Download → Extension Captures → Native Host → Mergen → Download Starts
```

No more copy-paste! Downloads are captured **before** Chrome's save dialog appears.

### Troubleshooting

**"Native host not found"**

- Run: `cd native-host && ./install.sh`
- Check: `ls ~/bin/mergen-native-host.py`

**"Access forbidden"**

- Extension ID mismatch
- Re-register in Mergen Settings → Browser Integration

**Extension not capturing downloads**

- Reload extension in `chrome://extensions/`
- Check log: `tail -f ~/.mergen-native-host.log`

**Detailed Guide:** [browser-extension/KURULUM.md](browser-extension/KURULUM.md)

## 🚀 Quick Start

**Method 1: With Browser Extension (Recommended)**

- Just click any download link in your browser
- Mergen captures it automatically!

**Method 2: Manual URL**

```bash
./main.py
# Click "Add URL" and paste download link
```

## 🛠️ Configuration

Settings: `~/.config/mergen/config.json`

**Key Settings:**

- Download directory
- Max connections (1-32)
- Auto-categorization
- Browser integration
- Language (en/tr)
- Proxy settings
- Auto-startup on boot

## 🌍 Supported Platforms

### Operating Systems

- ✅ **Linux** - All distributions (Ubuntu, Fedora, Debian, Arch, etc.)
- ✅ **macOS** - 10.14+ (Mojave and later)
- ✅ **Windows** - 10/11 (64-bit)

### Browsers (with extension)

- ✅ Google Chrome / Chromium
- ✅ Brave Browser
- ✅ Microsoft Edge
- ✅ Zen Browser
- ✅ Firefox
- ✅ Any Chromium-based browser

### Desktop Environments

- ✅ GNOME
- ✅ KDE Plasma
- ✅ XFCE
- ✅ Any DE with system tray support

## 🤝 Contributing

Contributions welcome!

1. Fork the repo
2. Create feature branch
3. Make changes
4. Submit pull request

## 📄 License

GPL-3.0 License - see [LICENSE](LICENSE)

## 🙏 Acknowledgments

- PySide6 for GUI framework
- Chrome/Firefox for Native Messaging API
- All contributors and testers

## 📞 Support

- 🐛 [Report Issues](https://github.com/Tunahanyrd/mergen/issues)
- 💬 [Discussions](https://github.com/Tunahanyrd/mergen/discussions)
- ⭐ Star if you find it useful!

---

**Made with ❤️ by [Tunahanyrd](https://github.com/Tunahanyrd)**
