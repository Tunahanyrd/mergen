import pytest
from src.core.autostart import AutoStartManager

def test_autostart_check(mocker):
    # Mock platform-specific check methods
    mocker.patch('src.core.autostart.AutoStartManager._check_windows', return_value=True)
    mocker.patch('src.core.autostart.AutoStartManager._check_linux', return_value=False)
    mocker.patch('platform.system', return_value='Windows')
    
    assert AutoStartManager.is_autostart_enabled() is True
    
    mocker.patch('platform.system', return_value='Linux')
    assert AutoStartManager.is_autostart_enabled() is False

def test_set_autostart_linux(mocker, tmp_path):
    mocker.patch('platform.system', return_value='Linux')
    
    # Mock home dir to point to tmp_path
    mocker.patch('pathlib.Path.home', return_value=tmp_path)
    mocker.patch('sys.executable', '/usr/bin/python3')
    mocker.patch('sys.argv', ['/app/main.py'])
    
    AutoStartManager.set_autostart(True)
    
    desktop_file = tmp_path / ".config" / "autostart" / "mergen.desktop"
    assert desktop_file.exists()
    content = desktop_file.read_text()
    assert "X-GNOME-Autostart-enabled=true" in content
    
    AutoStartManager.set_autostart(False)
    assert not desktop_file.exists()
