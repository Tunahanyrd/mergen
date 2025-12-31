# aria2 Installation Script

## Dependencies

### 1. aria2c (Download Engine)
```bash
# Ubuntu/Debian
sudo apt install -y aria2

# Fedora/RHEL
sudo dnf install -y aria2

# macOS
brew install aria2

# Windows
# Download from: https://github.com/aria2/aria2/releases
# Or use: choco install aria2
```

### 2. Python Dependencies (via uv)
```bash
# Add to pyproject.toml
uv add aiohttp
```

## Verification
```bash
# Check aria2c
aria2c --version

# Check aiohttp
python -c "import aiohttp; print(aiohttp.__version__)"
```

## Auto-installation in Mergen

Add to `install_dependencies()` in setup script:
```python
def install_aria2():
    """Ensure aria2c is installed"""
    import shutil
    import subprocess
    import platform
    
    # Check if already installed
    if shutil.which('aria2c'):
        print("✅ aria2c already installed")
        return True
    
    print("📦 Installing aria2c...")
    
    system = platform.system()
    try:
        if system == 'Linux':
            # Try apt first
            subprocess.run(['sudo', 'apt', 'install', '-y', 'aria2'], check=True)
        elif system == 'Darwin':  # macOS
            subprocess.run(['brew', 'install', 'aria2'], check=True)
        else:
            print("⚠️ Please install aria2c manually")
            return False
        
        print("✅ aria2c installed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to install aria2c: {e}")
        print("Please install manually:")
        print("  Ubuntu/Debian: sudo apt install aria2")
        print("  macOS: brew install aria2")
        return False
```
