#!/usr/bin/env python3
"""
Test suite for FAL.AI Video Generator
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import Config, VideoGenerator, InteractiveCLI
from security import security_manager, InputValidator

# ========================================================================
#                              Test Configuration                         
# ========================================================================

@pytest.fixture
def temp_config_dir():
    """Create temporary directory for test configuration"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def test_config(temp_config_dir):
    """Create test configuration"""
    config_file = temp_config_dir / "test_settings.json"
    test_settings = {
        "fal_api_key": "test_key",
        "default_model": "test_model",
        "output_directory": str(temp_config_dir / "outputs"),
        "log_level": "DEBUG",
        "max_duration": 5,
        "default_aspect_ratio": "16:9"
    }
    
    config_file.write_text(json.dumps(test_settings, indent=2))
    return Config(str(config_file))

@pytest.fixture
def mock_fal_client():
    """Mock fal_client for testing"""
    with patch('main.fal_client') as mock:
        mock.upload_file.return_value = "https://test.url/file.jpg"
        mock.subscribe.return_value = {"video_url": "https://test.url/video.mp4"}
        mock.submit_async.return_value = AsyncMock()
        mock.stream_async.return_value = AsyncMock()
        yield mock

# ========================================================================
#                            Configuration Tests                          
# ========================================================================

class TestConfig:
    """Test configuration management"""
    
    def test_config_creation(self, temp_config_dir):
        """Test configuration file creation"""
        config_file = temp_config_dir / "new_config.json"
        config = Config(str(config_file))
        
        assert config_file.exists()
        assert config.get("fal_api_key") == ""
        assert config.get("default_model") == "fal-ai/kling-video/v1/pro/image-to-video"
    
    def test_config_loading(self, test_config):
        """Test loading existing configuration"""
        assert test_config.get("fal_api_key") == "test_key"
        assert test_config.get("max_duration") == 5
        assert test_config.get("default_aspect_ratio") == "16:9"
    
    def test_config_get_default(self, test_config):
        """Test getting configuration with default values"""
        assert test_config.get("nonexistent_key", "default") == "default"
        assert test_config.get("fal_api_key", "default") == "test_key"
    
    @patch.dict(os.environ, {"FAL_KEY": "env_key"})
    def test_api_key_from_env(self, test_config):
        """Test API key loading from environment"""
        result = test_config.set_api_key()
        assert result is True
        assert os.environ.get("FAL_KEY") == "env_key"
    
    @patch('security.security_manager.get_secure_api_key', return_value='user_input_key')
    def test_api_key_from_input(self, mock_get_key, temp_config_dir):
        """Test API key input from user"""
        config_file = temp_config_dir / "test_config.json"
        config = Config(str(config_file))
        
        result = config.set_api_key()
        assert result is True
        assert os.environ.get("FAL_KEY") == "user_input_key"

# ========================================================================
#                          Video Generator Tests                          
# ========================================================================

class TestVideoGenerator:
    """Test video generation functionality"""
    
    def test_generator_initialization(self, test_config):
        """Test video generator initialization"""
        generator = VideoGenerator(test_config)
        
        output_dir = Path(test_config.get("output_directory"))
        assert output_dir.exists()
    
    def test_upload_file(self, test_config, mock_fal_client):
        """Test file upload functionality"""
        generator = VideoGenerator(test_config)
        
        # Create test file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            f.write(b"test image data")
            test_file = f.name
        
        try:
            url = generator.upload_file(test_file)
            assert url == "https://test.url/file.jpg"
            mock_fal_client.upload_file.assert_called_once_with(test_file)
        finally:
            os.unlink(test_file)
    
    def test_upload_file_error(self, test_config, mock_fal_client):
        """Test file upload error handling"""
        mock_fal_client.upload_file.side_effect = Exception("Upload failed")
        generator = VideoGenerator(test_config)
        
        with pytest.raises(Exception, match="Upload failed"):
            generator.upload_file("nonexistent.jpg")
    
    @pytest.mark.asyncio
    async def test_generate_kling_pro(self, test_config, mock_fal_client):
        """Test Kling Pro video generation"""
        generator = VideoGenerator(test_config)
        
        # Create test image file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            f.write(b"test image data")
            test_file = f.name
        
        try:
            result = await generator.generate_kling_pro(
                test_file, 
                "test prompt",
                duration=10,
                aspect_ratio="9:16"
            )
            
            assert result == {"video_url": "https://test.url/video.mp4"}
            mock_fal_client.upload_file.assert_called_with(test_file)
            mock_fal_client.subscribe.assert_called_once()
        finally:
            os.unlink(test_file)
    
    @pytest.mark.asyncio
    async def test_generate_kling_v16(self, test_config, mock_fal_client):
        """Test Kling v1.6 async video generation"""
        # Setup async mock
        async def mock_submit_async(*args, **kwargs):
            mock_handler = AsyncMock()
            mock_handler.iter_events = Mock(return_value=async_iter([{"event": "progress"}]))
            mock_handler.get = AsyncMock(return_value={"video_url": "https://test.url/video.mp4"})
            return mock_handler
        
        mock_fal_client.submit_async.side_effect = mock_submit_async
        
        generator = VideoGenerator(test_config)
        
        # Create test image file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            f.write(b"test image data")
            test_file = f.name
        
        try:
            result = await generator.generate_kling_v16(
                test_file,
                "test prompt",
                duration=5
            )
            
            assert result == {"video_url": "https://test.url/video.mp4"}
            mock_fal_client.upload_file.assert_called_with(test_file)
            mock_fal_client.submit_async.assert_called_once()
        finally:
            os.unlink(test_file)
    
    @pytest.mark.asyncio
    async def test_run_workflow(self, test_config, mock_fal_client):
        """Test custom workflow execution"""
        mock_fal_client.stream_async.return_value = async_iter([
            {"event": "start"},
            {"event": "progress", "data": "50%"},
            {"event": "complete"}
        ])
        
        generator = VideoGenerator(test_config)
        
        result = await generator.run_workflow(arguments={"test": "data"})
        
        assert "events" in result
        assert len(result["events"]) == 3
        mock_fal_client.stream_async.assert_called_once()

# ========================================================================
#                          Interactive CLI Tests                          
# ========================================================================

class TestInteractiveCLI:
    """Test interactive command line interface"""
    
    def test_cli_initialization(self, test_config):
        """Test CLI initialization"""
        generator = VideoGenerator(test_config)
        cli = InteractiveCLI(generator)
        
        assert cli.generator == generator
    
    @patch('builtins.input', return_value='test.jpg')
    def test_get_file_path_existing(self, mock_input, test_config):
        """Test getting existing file path"""
        generator = VideoGenerator(test_config)
        cli = InteractiveCLI(generator)
        
        # Create test file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            test_file = f.name
        
        try:
            with patch('builtins.input', return_value=test_file):
                result = cli.get_file_path("Enter file")
                assert result == test_file
        finally:
            os.unlink(test_file)
    
    @patch('builtins.input', side_effect=['nonexistent.jpg', ''])
    def test_get_file_path_nonexistent(self, mock_input, test_config, capsys):
        """Test handling of nonexistent file path"""
        generator = VideoGenerator(test_config)
        cli = InteractiveCLI(generator)
        
        result = cli.get_file_path("Enter file")
        assert result is None
        
        captured = capsys.readouterr()
        assert "Invalid or unsafe file path" in captured.out

# ========================================================================
#                              Utilities                                  
# ========================================================================

async def async_iter(items):
    """Helper to create async iterator from list"""
    for item in items:
        yield item

# ========================================================================
#                           Integration Tests                             
# ========================================================================

class TestIntegration:
    """Integration tests for the complete system"""
    
    def test_full_initialization(self, temp_config_dir):
        """Test complete system initialization"""
        config_file = temp_config_dir / "integration_config.json"
        
        # Test config creation
        config = Config(str(config_file))
        assert config_file.exists()
        
        # Test generator initialization
        generator = VideoGenerator(config)
        output_dir = Path(config.get("output_directory"))
        assert output_dir.exists()
        
        # Test CLI initialization
        cli = InteractiveCLI(generator)
        assert cli.generator == generator
    
    @pytest.mark.asyncio
    async def test_end_to_end_mock(self, test_config, mock_fal_client):
        """Test end-to-end workflow with mocked FAL client"""
        generator = VideoGenerator(test_config)
        
        # Create test image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            f.write(b"test image data")
            test_file = f.name
        
        try:
            # Test the complete workflow
            result = await generator.generate_kling_pro(
                test_file,
                "A beautiful landscape video",
                duration=5,
                aspect_ratio="16:9"
            )
            
            assert "video_url" in result
            assert mock_fal_client.upload_file.called
            assert mock_fal_client.subscribe.called
            
        finally:
            os.unlink(test_file)

# ========================================================================
#                              Main Test Runner                           
# ========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])