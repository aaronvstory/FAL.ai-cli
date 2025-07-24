#!/usr/bin/env python3
"""
Test suite for FAL_LAUNCHER.py fixes
Tests the key functionality improvements and bug fixes
"""

import pytest
import socket
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the launcher module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from FAL_LAUNCHER import FALLauncher, _find_free_port


class TestPortDetection:
    """Test port detection and free port finding"""
    
    def test_find_free_port_default_available(self):
        """Test finding free port when default port is available"""
        # This test assumes port 8000 is available
        port = _find_free_port(8000)
        assert isinstance(port, int)
        assert 1024 <= port <= 65535
    
    def test_find_free_port_default_occupied(self):
        """Test finding alternative port when default is occupied"""
        # Create a socket to occupy a port
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind(("127.0.0.1", 0))
        occupied_port = test_socket.getsockname()[1]
        
        try:
            port = _find_free_port(occupied_port)
            assert port != occupied_port
            assert isinstance(port, int)
            assert 1024 <= port <= 65535
        finally:
            test_socket.close()
    
    def test_find_free_port_random_assignment(self):
        """Test that random port assignment works"""
        # Occupy a known port temporarily
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            occupied_port = s.getsockname()[1]
            
            # Request the occupied port - should get a different one
            free_port = _find_free_port(occupied_port)
            assert free_port != occupied_port


class TestFALLauncher:
    """Test FAL Launcher class functionality"""
    
    @pytest.fixture
    def launcher(self, tmp_path):
        """Create a launcher instance with temporary directories"""
        with patch.object(Path, '__file__', str(tmp_path / "FAL_LAUNCHER.py")):
            launcher = FALLauncher()
            launcher.script_dir = tmp_path
            launcher.data_dir = tmp_path / "data"
            launcher.config_dir = tmp_path / "config"
            launcher.data_dir.mkdir(exist_ok=True)
            launcher.config_dir.mkdir(exist_ok=True)
            return launcher
    
    def test_launcher_initialization(self, launcher):
        """Test launcher initializes correctly"""
        assert isinstance(launcher.settings, dict)
        assert launcher.data_dir.exists()
        assert launcher.config_dir.exists()
        assert "last_mode" in launcher.settings
        assert "preferred_model" in launcher.settings
    
    def test_settings_save_load(self, launcher):
        """Test settings save and load functionality"""
        # Modify settings
        launcher.settings["test_key"] = "test_value"
        launcher._save_settings()
        
        # Create new launcher instance to test loading
        new_launcher = FALLauncher()
        new_launcher.script_dir = launcher.script_dir
        new_launcher.data_dir = launcher.data_dir
        new_launcher.config_dir = launcher.config_dir
        new_launcher.settings = new_launcher._load_settings()
        
        assert new_launcher.settings.get("test_key") == "test_value"


class TestWebModeIntegration:
    """Test web mode launch functionality"""
    
    @pytest.fixture
    def launcher(self, tmp_path):
        """Create launcher with temporary paths"""
        launcher = FALLauncher()
        launcher.script_dir = tmp_path
        launcher.data_dir = tmp_path / "data"
        launcher.data_dir.mkdir(exist_ok=True)
        return launcher
    
    @patch('FAL_LAUNCHER.uvicorn')
    @patch('FAL_LAUNCHER.webbrowser')
    @patch('threading.Timer')
    def test_launch_web_mode_success(self, mock_timer, mock_webbrowser, mock_uvicorn, launcher):
        """Test successful web mode launch"""
        # Mock dependencies
        mock_app = Mock()
        
        with patch('FAL_LAUNCHER.app', mock_app):
            with patch.dict('sys.modules', {'web_app': Mock(app=mock_app)}):
                result = launcher.launch_web_mode()
                
                assert result == True
                mock_uvicorn.run.assert_called_once()
                mock_timer.assert_called_once()
    
    @patch('FAL_LAUNCHER.uvicorn', side_effect=ImportError("uvicorn not found"))
    def test_launch_web_mode_missing_dependencies(self, mock_uvicorn, launcher):
        """Test web mode launch with missing dependencies"""
        result = launcher.launch_web_mode()
        
        assert result == False
    
    def test_web_integration_data_preparation(self, launcher):
        """Test web integration data preparation"""
        launcher._prepare_web_integration()
        
        integration_file = launcher.data_dir / "web_integration.json"
        assert integration_file.exists()
        
        # Load and verify integration data
        import json
        with open(integration_file) as f:
            data = json.load(f)
        
        assert "launcher_version" in data
        assert "user_preferences" in data
        assert "shared_features" in data
        assert "data_locations" in data


class TestQuickGenerateMode:
    """Test quick generate mode fixes"""
    
    @pytest.fixture
    def launcher(self, tmp_path):
        """Create launcher with temporary paths"""
        launcher = FALLauncher()
        launcher.script_dir = tmp_path
        launcher.data_dir = tmp_path / "data"
        launcher.data_dir.mkdir(exist_ok=True)
        
        # Create fake main.py
        main_py = tmp_path / "main.py"
        main_py.write_text("# Mock main.py")
        
        return launcher
    
    def test_model_name_mapping(self, launcher):
        """Test correct model name mapping for CLI"""
        # Test data for model mapping
        test_cases = [
            ("kling_21_standard", "kling21std"),
            ("kling_21_pro", "kling21pro"), 
            ("kling_21_master", "kling21master"),
            ("kling_16_pro", "kling16pro"),
            ("luma_dream", "luma_dream"),
            ("unknown_model", "unknown_model")  # Should pass through unchanged
        ]
        
        # Mock the components needed for quick generate
        with patch('FAL_LAUNCHER.FilePicker') as mock_picker_class:
            with patch('FAL_LAUNCHER.PromptManager') as mock_prompt_class:
                with patch('subprocess.run') as mock_subprocess:
                    
                    # Setup mocks
                    mock_picker = Mock()
                    mock_picker.pick_single_file.return_value = "/fake/path/image.jpg"
                    mock_picker_class.return_value = mock_picker
                    
                    mock_prompt_manager = Mock()
                    mock_prompt_manager.get_quick_prompt.return_value = "Test prompt"
                    mock_prompt_class.return_value = mock_prompt_manager
                    
                    for internal_model, expected_cli_model in test_cases:
                        launcher.settings["preferred_model"] = internal_model
                        launcher.launch_quick_generate()
                        
                        # Check that subprocess was called with correct model
                        call_args = mock_subprocess.call_args[0][0]  # Get the command list
                        mode_index = call_args.index("--mode")
                        actual_cli_model = call_args[mode_index + 1]
                        
                        assert actual_cli_model == expected_cli_model
    
    @patch('subprocess.run')
    def test_prompt_quoting_fix(self, mock_subprocess, launcher):
        """Test that prompts are not double-quoted"""
        test_prompt = 'A beautiful sunset with "amazing" colors'
        
        with patch('FAL_LAUNCHER.FilePicker') as mock_picker_class:
            with patch('FAL_LAUNCHER.PromptManager') as mock_prompt_class:
                
                # Setup mocks
                mock_picker = Mock()
                mock_picker.pick_single_file.return_value = "/fake/path/image.jpg"
                mock_picker_class.return_value = mock_picker
                
                mock_prompt_manager = Mock()
                mock_prompt_manager.get_quick_prompt.return_value = test_prompt
                mock_prompt_class.return_value = mock_prompt_manager
                
                launcher.launch_quick_generate()
                
                # Check that prompt is passed correctly without extra quotes
                call_args = mock_subprocess.call_args[0][0]
                prompt_index = call_args.index("--prompt")
                actual_prompt = call_args[prompt_index + 1]
                
                assert actual_prompt == test_prompt
                assert not actual_prompt.startswith('"')
                assert not actual_prompt.endswith('"')


class TestEnvironmentChecks:
    """Test environment checking functionality"""
    
    def test_check_environment_all_available(self):
        """Test environment check when all dependencies are available"""
        launcher = FALLauncher()
        
        with patch('builtins.__import__') as mock_import:
            # Mock successful imports
            mock_import.return_value = Mock()
            
            with patch.dict('os.environ', {'FAL_KEY': 'test_key'}):
                env_status = launcher.check_environment()
                
                assert env_status["fal_key_set"] == True
                assert env_status["python_version"] == sys.version_info[:2]
    
    def test_check_environment_missing_dependencies(self):
        """Test environment check with missing dependencies"""
        launcher = FALLauncher()
        
        def mock_import_error(module_name, *args, **kwargs):
            if module_name in ['tkinter', 'fastapi', 'fal_client']:
                raise ImportError(f"No module named '{module_name}'")
            return Mock()
        
        with patch('builtins.__import__', side_effect=mock_import_error):
            env_status = launcher.check_environment()
            
            assert env_status["gui_available"] == False
            assert env_status["web_dependencies"] == False
            assert env_status["cli_dependencies"] == False


class TestErrorHandling:
    """Test error handling improvements"""
    
    @pytest.fixture
    def launcher(self, tmp_path):
        """Create launcher with temporary paths"""
        launcher = FALLauncher()
        launcher.script_dir = tmp_path
        launcher.data_dir = tmp_path / "data"
        launcher.data_dir.mkdir(exist_ok=True)
        return launcher
    
    def test_web_mode_graceful_failure(self, launcher):
        """Test web mode handles failures gracefully"""
        with patch('FAL_LAUNCHER.uvicorn.run', side_effect=Exception("Server failed")):
            result = launcher.launch_web_mode()
            assert result == False
    
    def test_cli_mode_missing_main_py(self, launcher):
        """Test CLI mode handles missing main.py gracefully"""
        # Don't create main.py - should fail gracefully
        with patch('FAL_LAUNCHER.run_unified_launcher', side_effect=ImportError()):
            result = launcher.launch_cli_mode()
            assert result == False
    
    def test_quick_generate_missing_main_py(self, launcher):
        """Test quick generate handles missing main.py gracefully"""
        # Don't create main.py
        with patch('FAL_LAUNCHER.FilePicker') as mock_picker_class:
            with patch('FAL_LAUNCHER.PromptManager') as mock_prompt_class:
                
                mock_picker = Mock()
                mock_picker.pick_single_file.return_value = "/fake/path/image.jpg"
                mock_picker_class.return_value = mock_picker
                
                mock_prompt_manager = Mock()
                mock_prompt_manager.get_quick_prompt.return_value = "Test prompt"
                mock_prompt_class.return_value = mock_prompt_manager
                
                result = launcher.launch_quick_generate()
                assert result == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])