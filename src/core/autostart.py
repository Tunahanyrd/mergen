import os
import platform
import sys
from pathlib import Path


class AutoStartManager:
    APP_NAME = "Mergen"
    APP_KEY = "com.tunahanyrd.mergen"

    @staticmethod
    def set_autostart(enable: bool = True):
        system = platform.system()
        if system == "Windows":
            AutoStartManager._set_windows(enable)
        elif system == "Linux":
            AutoStartManager._set_linux(enable)
        elif system == "Darwin":
            AutoStartManager._set_macos(enable)

    @staticmethod
    def is_autostart_enabled() -> bool:
        system = platform.system()
        if system == "Windows":
            return AutoStartManager._check_windows()
        elif system == "Linux":
            return AutoStartManager._check_linux()
        elif system == "Darwin":
            return AutoStartManager._check_macos()
        return False

    @staticmethod
    def _get_executable_path():
        if getattr(sys, "frozen", False):
            return sys.executable
        return sys.executable + ' "' + os.path.abspath(sys.argv[0]) + '"'

    # Windows Implementation
    @staticmethod
    def _set_windows(enable):
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS
            )
            if enable:
                exe_path = AutoStartManager._get_executable_path()
                # Quote path if it contains spaces and not already quoted
                if " " in exe_path and not exe_path.startswith('"'):
                    exe_path = f'"{exe_path}"'
                winreg.SetValueEx(key, AutoStartManager.APP_NAME, 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, AutoStartManager.APP_NAME)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"AutoStart Error (Windows): {e}")

    @staticmethod
    def _check_windows():
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, AutoStartManager.APP_NAME)
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False

    # Linux Implementation
    @staticmethod
    def _set_linux(enable):
        autostart_dir = Path.home() / ".config" / "autostart"
        desktop_file = autostart_dir / "mergen.desktop"

        if enable:
            if not autostart_dir.exists():
                autostart_dir.mkdir(parents=True, exist_ok=True)

            exe_path = AutoStartManager._get_executable_path()

            content = f"""[Desktop Entry]
Type=Application
Name={AutoStartManager.APP_NAME}
Exec={exe_path}
Icon=mergen
Comment=Mergen Download Manager Auto-Start
X-GNOME-Autostart-enabled=true
"""
            with open(desktop_file, "w") as f:
                f.write(content)
        else:
            if desktop_file.exists():
                os.remove(desktop_file)

    @staticmethod
    def _check_linux():
        return (Path.home() / ".config" / "autostart" / "mergen.desktop").exists()

    # macOS Implementation
    @staticmethod
    def _set_macos(enable):
        launch_agents = Path.home() / "Library" / "LaunchAgents"
        plist_file = launch_agents / f"{AutoStartManager.APP_KEY}.plist"

        if enable:
            if not launch_agents.exists():
                launch_agents.mkdir(parents=True, exist_ok=True)

            exe_path = AutoStartManager._get_executable_path()
            # On macOS, sys.executable in a bundle points to the binary inside MacOS/
            # e.g. Mergen.app/Contents/MacOS/Mergen

            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{AutoStartManager.APP_KEY}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
            with open(plist_file, "w") as f:
                f.write(plist_content)
        else:
            if plist_file.exists():
                os.remove(plist_file)

    @staticmethod
    def _check_macos():
        return (Path.home() / "Library" / "LaunchAgents" / f"{AutoStartManager.APP_KEY}.plist").exists()
