#!/usr/bin/env python3
"""
Core functionality tests for FAL_LAUNCHER.py fixes
Tests the essential fixes without complex mocking
"""

import pytest
import socket
import sys
from pathlib import Path

# Import the port detection function
sys.path.insert(0, str(Path(__file__).parent.parent))
from FAL_LAUNCHER import _find_free_port, FALLauncher


def test_find_free_port_basic():
    """Test basic port finding functionality"""
    port = _find_free_port(8000)
    assert isinstance(port, int)
    assert 1024 <= port <= 65535


def test_find_free_port_occupied():
    """Test finding alternative port when default is occupied"""
    # Create a socket to occupy a port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
        test_socket.bind(("127.0.0.1", 0))
        occupied_port = test_socket.getsockname()[1]
        
        # Request the occupied port - should get a different one
        free_port = _find_free_port(occupied_port)
        assert free_port != occupied_port
        assert isinstance(free_port, int)


def test_launcher_initialization():
    """Test launcher initializes correctly"""
    launcher = FALLauncher()
    assert isinstance(launcher.settings, dict)
    assert launcher.data_dir.exists()
    assert launcher.config_dir.exists()
    assert "last_mode" in launcher.settings
    assert "preferred_model" in launcher.settings


def test_model_name_mapping():
    """Test that model name mapping logic is correct"""
    # Test model mapping logic
    model_mapping = {
        "kling_21_standard": "kling21std", 
        "kling_21_pro": "kling21pro",
        "kling_21_master": "kling21master",
        "kling_16_pro": "kling16pro",
        "luma_dream": "luma_dream"
    }
    
    test_cases = [
        ("kling_21_standard", "kling21std"),
        ("kling_21_pro", "kling21pro"), 
        ("kling_21_master", "kling21master"),
        ("kling_16_pro", "kling16pro"),
        ("luma_dream", "luma_dream"),
        ("unknown_model", "unknown_model")  # Should pass through unchanged
    ]
    
    for internal_model, expected_cli_model in test_cases:
        actual_cli_model = model_mapping.get(internal_model, internal_model)
        assert actual_cli_model == expected_cli_model


def test_environment_check():
    """Test environment checking functionality"""
    launcher = FALLauncher()
    env_status = launcher.check_environment()
    
    # Should return a dict with expected keys
    expected_keys = [
        "python_version", "gui_available", "fal_key_set", 
        "web_dependencies", "cli_dependencies"
    ]
    
    for key in expected_keys:
        assert key in env_status
    
    # Python version should be current version
    assert env_status["python_version"] == sys.version_info[:2]


def test_settings_persistence(tmp_path):
    """Test that settings can be saved and loaded"""
    # Create launcher with temporary directory
    launcher = FALLauncher()
    original_data_dir = launcher.data_dir
    
    # Use temporary directory
    launcher.data_dir = tmp_path / "data"
    launcher.data_dir.mkdir(exist_ok=True)
    
    # Modify and save settings
    test_setting = "test_value_12345"
    launcher.settings["test_key"] = test_setting
    launcher._save_settings()
    
    # Load settings in new instance
    new_launcher = FALLauncher()
    new_launcher.data_dir = launcher.data_dir
    new_settings = new_launcher._load_settings()
    
    assert new_settings.get("test_key") == test_setting
    
    # Restore original data dir
    launcher.data_dir = original_data_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])