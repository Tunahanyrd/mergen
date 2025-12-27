#!/bin/bash
# Remove all debug print statements from modified files

echo "🧹 Cleaning debug prints..."

# Remove prints with emoji markers
sed -i '/print(f"🔍/d' src/core/downloader.py
sed -i '/print(f"📦/d' src/core/downloader.py  
sed -i '/print(f"✅/d' src/core/downloader.py
sed -i '/print(f"🎬/d' src/core/downloader.py
sed -i '/print(f"▶️/d' src/core/downloader.py
sed -i '/print(f"❌/d' src/core/downloader.py
sed-i '/print(f"🔀/d' src/core/downloader.py

sed -i '/print(f"📦/d' src/gui/quality_dialog_v2.py
sed -i '/print(f"🔍/d' src/gui/quality_dialog_v2.py
sed -i '/print(f"✅/d' src/gui/quality_dialog_v2.py
sed -i '/print(f"🚫/d' src/gui/quality_dialog_v2.py
sed -i '/print(f"📊/d' src/gui/quality_dialog_v2.py
sed -i '/print(f"🎯/d' src/gui/quality_dialog_v2.py
sed -i '/print(f"🎵/d' src/gui/quality_dialog_v2.py
sed -i '/print(f"🎞️/d' src/gui/quality_dialog_v2.py
sed -i '/print(f"➡️/d' src/gui/quality_dialog_v2.py

sed -i '/print(f"🎬/d' src/gui/main_window.py
sed -i '/print(f"💾/d' src/gui/main_window.py
sed -i '/print(f"✅/d' src/gui/main_window.py
sed -i '/print(f"📺/d' src/gui/main_window.py
sed -i '/print(f"📥/d' src/gui/main_window.py
sed -i '/print(f"🚀/d' src/gui/main_window.py

sed -i '/print(f"🚀/d' src/gui/download_dialog.py
sed -i '/print(f"📝/d' src/gui/download_dialog.py
sed -i '/print(f"▶️/d' src/gui/download_dialog.py
sed -i '/print(f"✅/d' src/gui/download_dialog.py

sed -i '/print(f"🔔/d' src/core/downloader.py

echo "✅ Cleanup complete!"
