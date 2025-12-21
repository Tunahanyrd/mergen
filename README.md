# Mergen - Modern Download Manager

<div align="center">

![Mergen Logo](data/mergen.png)

A powerful, multi-threaded download manager with a sleek dark UI, built with PySide6.

</div>

## ✨ Features

- 🚀 **Multi-threaded Downloads**: Utilizes multiple connections for faster downloads
- ⏸️ **Resume Support**: Pause and resume downloads seamlessly
- 📊 **Real-time Progress**: Live speed, ETA, and progress tracking
- 🎨 **Modern UI**: Dark glassmorphism theme with customizable light mode
- 📁 **Smart Categories**: Automatic file organization by type
- 🔄 **Queue Management**: Organize downloads into custom queues
- 🌍 **Internationalization**: Multi-language support (TR/EN)
- 🔌 **Proxy Support**: HTTP/HTTPS proxy configuration
- 💾 **Persistent State**: Downloads resume even after restart

## 📥 Installation

### Pre-built Binaries (Recommended)

Download the latest release for your platform:

**Linux:**
```bash
wget https://github.com/Tunahanyrd/mergen/releases/latest/download/mergen
chmod +x mergen
./mergen
```

**macOS (Apple Silicon):**
```bash
wget https://github.com/Tunahanyrd/mergen/releases/latest/download/mergen.bin
chmod +x mergen.bin
./mergen.bin
```

**Windows:**
Download `mergen.exe` from the [releases page](https://github.com/Tunahanyrd/mergen/releases/latest) and run it.

### From Source

**Requirements:**
- Python 3.11+
- PySide6
- httpx

**Installation:**
```bash
git clone https://github.com/Tunahanyrd/mergen.git
cd mergen
pip install -r requirements.txt
python main.py
```

## 🏗️ Building from Source

### Using Nuitka (Recommended)

**Linux/macOS:**
```bash
python -m nuitka --standalone --onefile --enable-plugin=pyside6 \
  --assume-yes-for-downloads --include-data-dir=data=data \
  --output-dir=build --output-filename=mergen main.py
```

**Windows:**
```bash
python -m nuitka --standalone --onefile --enable-plugin=pyside6 ^
  --assume-yes-for-downloads --include-data-dir=data=data ^
  --output-dir=build --output-filename=mergen.exe main.py
```

Or simply use the build script:
```bash
python build_nuitka.py
```

## 🎯 Usage

1. **Add Downloads**: Click "Add URL" or press `Ctrl+N`, paste the download link
2. **Manage Downloads**: Use toolbar buttons to pause, resume, or delete
3. **Categories**: Files are automatically sorted by extension
4. **Queues**: Create custom download queues for batch operations
5. **Settings**: Configure download directory, proxy, theme, and more

### Keyboard Shortcuts

- `Ctrl+N` - Add new download
- `Ctrl+R` - Resume selected download
- `Ctrl+P` - Pause selected download
- `Delete` - Delete selected download
- `Ctrl+Q` - Quit application

## 🛠️ Configuration

Configuration files are stored in:
- **Linux**: `~/.config/mergen/`
- **macOS**: `~/Library/Application Support/mergen/`
- **Windows**: `%APPDATA%\mergen\`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [PySide6](https://doc.qt.io/qtforpython/)
- HTTP library: [httpx](https://www.python-httpx.org/)
- Compiled with [Nuitka](https://nuitka.net/)
