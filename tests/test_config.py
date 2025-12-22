import os
import json
import pytest
from pathlib import Path
from src.core.config import ConfigManager

@pytest.fixture
def config_manager(tmp_path):
    # Mocking QStandardPaths or injecting path would be ideal.
    # Since ConfigManager uses a singleton and hardcoded paths via QStandardPaths,
    # it's hard to isolate file I/O without mocking QStandardPaths.
    # For now, we test the logic that doesn't depend on global state or accepts dependency in future.
    # Or, we can mock QStandardPaths.writableLocation using pytest-mock.
    pass

def test_singleton():
    c1 = ConfigManager()
    c2 = ConfigManager()
    assert c1 is c2

def test_defaults(mocker):
    # Mock file I/O to prevent reading real config
    mocker.patch('builtins.open', mocker.mock_open(read_data='{}'))
    mocker.patch('os.path.exists', return_value=False)
    
    cm = ConfigManager()
    # Force reload to apply mocks if singleton was already active
    cm._initialized = False 
    cm.__init__()
    
    assert cm.get("max_connections") == 8
    assert cm.get("theme") == "dark"

def test_get_proxy_config_structure(mocker):
    cm = ConfigManager()
    cm.config["proxy_enabled"] = True
    cm.config["proxy_host"] = "127.0.0.1"
    cm.config["proxy_port"] = "8080"
    
    proxy = cm.get_proxy_config()
    assert proxy["enabled"] is True
    assert proxy["host"] == "127.0.0.1"
    assert proxy["port"] == 8080
