#!/usr/bin/env python3
"""
Comprehensive security tests for FAL.AI Video Generator
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from security import InputValidator, SecureConfig, SecurityManager


class TestInputValidator:
    """Test input validation and sanitization"""

    def test_validate_file_path_valid(self):
        """Test valid file path validation"""
        assert InputValidator.validate_file_path("test.jpg")
        assert InputValidator.validate_file_path("path/to/file.png")
        assert InputValidator.validate_file_path("C:\\path\\to\\file.mp4")
        assert InputValidator.validate_file_path("./relative/path.txt")

    def test_validate_file_path_invalid(self):
        """Test invalid file path rejection"""
        assert not InputValidator.validate_file_path("")
        assert not InputValidator.validate_file_path("../../../etc/passwd")
        assert not InputValidator.validate_file_path("path/with/../traversal")
        assert not InputValidator.validate_file_path("file<script>alert()</script>")
        assert not InputValidator.validate_file_path("a" * 1001)  # Too long

    def test_sanitize_file_path_valid(self):
        """Test file path sanitization with existing files"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            test_file = f.name
        
        try:
            result = InputValidator.sanitize_file_path(test_file)
            assert result == os.path.normpath(test_file)
        finally:
            os.unlink(test_file)

    def test_sanitize_file_path_nonexistent(self):
        """Test file path sanitization with non-existent files"""
        result = InputValidator.sanitize_file_path("nonexistent_file.jpg")
        assert result is None

    def test_validate_prompt_valid(self):
        """Test valid prompt validation"""
        assert InputValidator.validate_prompt("A beautiful landscape")
        assert InputValidator.validate_prompt("Create a video of a sunset")
        assert InputValidator.validate_prompt("Professional corporate meeting")

    def test_validate_prompt_invalid(self):
        """Test dangerous prompt rejection"""
        assert not InputValidator.validate_prompt("")
        assert not InputValidator.validate_prompt("<script>alert('xss')</script>")
        assert not InputValidator.validate_prompt("javascript:void(0)")
        assert not InputValidator.validate_prompt("eval(malicious_code)")
        assert not InputValidator.validate_prompt("import os; os.system('rm -rf /')")
        assert not InputValidator.validate_prompt("a" * 5001)  # Too long

    def test_sanitize_prompt_valid(self):
        """Test prompt sanitization"""
        prompt = "A beautiful landscape with mountains"
        result = InputValidator.sanitize_prompt(prompt)
        assert result == prompt

    def test_sanitize_prompt_dangerous(self):
        """Test dangerous prompt sanitization"""
        dangerous_prompt = "<script>alert('test')</script>"
        result = InputValidator.sanitize_prompt(dangerous_prompt)
        assert result is None

    def test_validate_duration_valid(self):
        """Test valid duration validation"""
        assert InputValidator.validate_duration(5) == 5
        assert InputValidator.validate_duration("10") == 10
        assert InputValidator.validate_duration(1) == 1
        assert InputValidator.validate_duration(60) == 60

    def test_validate_duration_invalid(self):
        """Test invalid duration rejection"""
        assert InputValidator.validate_duration(0) is None
        assert InputValidator.validate_duration(61) is None
        assert InputValidator.validate_duration(-5) is None
        assert InputValidator.validate_duration("invalid") is None
        assert InputValidator.validate_duration(None) is None

    def test_validate_aspect_ratio_valid(self):
        """Test valid aspect ratio validation"""
        assert InputValidator.validate_aspect_ratio("16:9") == "16:9"
        assert InputValidator.validate_aspect_ratio("9:16") == "9:16"
        assert InputValidator.validate_aspect_ratio("1:1") == "1:1"
        assert InputValidator.validate_aspect_ratio("4:3") == "4:3"

    def test_validate_aspect_ratio_invalid(self):
        """Test invalid aspect ratio rejection"""
        assert InputValidator.validate_aspect_ratio("invalid") is None
        assert InputValidator.validate_aspect_ratio("16:10") is None
        assert InputValidator.validate_aspect_ratio("") is None
        assert InputValidator.validate_aspect_ratio(None) is None

    def test_validate_cfg_scale_valid(self):
        """Test valid CFG scale validation"""
        assert InputValidator.validate_cfg_scale(0.5) == 0.5
        assert InputValidator.validate_cfg_scale("0.3") == 0.3
        assert InputValidator.validate_cfg_scale(0.0) == 0.0
        assert InputValidator.validate_cfg_scale(1.0) == 1.0

    def test_validate_cfg_scale_invalid(self):
        """Test invalid CFG scale rejection"""
        assert InputValidator.validate_cfg_scale(-0.1) is None
        assert InputValidator.validate_cfg_scale(1.1) is None
        assert InputValidator.validate_cfg_scale("invalid") is None
        assert InputValidator.validate_cfg_scale(None) is None

    def test_validate_url_valid(self):
        """Test valid URL validation"""
        assert InputValidator.validate_url("https://example.com/file.jpg")
        assert InputValidator.validate_url("http://test.org/image.png")

    def test_validate_url_invalid(self):
        """Test invalid URL rejection"""
        assert not InputValidator.validate_url("not_a_url")
        assert not InputValidator.validate_url("javascript:alert('xss')")
        assert not InputValidator.validate_url("")


class TestSecureConfig:
    """Test secure configuration management"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            yield temp_dir
            os.chdir(original_cwd)

    def test_encryption_key_generation(self, temp_dir):
        """Test encryption key generation and storage"""
        config = SecureConfig()
        assert config.encryption_key is not None
        assert len(config.encryption_key) == 44  # Fernet key length

        # Test key persistence
        key_path = Path("./.encryption_key")
        assert key_path.exists()

    def test_data_encryption_decryption(self, temp_dir):
        """Test data encryption and decryption"""
        config = SecureConfig()
        test_data = "sensitive_api_key_12345"
        
        encrypted = config.encrypt_sensitive_data(test_data)
        decrypted = config.decrypt_sensitive_data(encrypted)
        
        assert encrypted != test_data
        assert decrypted == test_data

    @patch.dict(os.environ, {"FAL_KEY": "test_api_key_from_env"})
    def test_get_api_key_from_env(self, temp_dir):
        """Test API key retrieval from environment"""
        config = SecureConfig()
        api_key = config.get_api_key_secure()
        assert api_key == "test_api_key_from_env"

    @patch('builtins.input', return_value='user_input_api_key')
    def test_get_api_key_from_input(self, mock_input, temp_dir):
        """Test API key retrieval from user input"""
        # Clear environment variable
        with patch.dict(os.environ, {}, clear=True):
            config = SecureConfig()
            api_key = config.get_api_key_secure()
            assert api_key == "user_input_api_key"
            
            # Verify encrypted storage
            encrypted_key_path = Path("./config/encrypted_api_key")
            assert encrypted_key_path.exists()

    @patch('builtins.input', side_effect=['', 'invalid!@#$%^&*()', 'valid_api_key'])
    def test_api_key_input_validation(self, mock_input, temp_dir):
        """Test API key input validation"""
        with patch.dict(os.environ, {}, clear=True):
            config = SecureConfig()
            api_key = config.get_api_key_secure()
            assert api_key == "valid_api_key"


class TestSecurityManager:
    """Test security manager integration"""

    @pytest.fixture
    def temp_image_file(self):
        """Create temporary image file for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            f.write(b"fake image data")
            yield f.name
        os.unlink(f.name)

    def test_validate_and_sanitize_valid_inputs(self, temp_image_file):
        """Test validation of valid inputs"""
        manager = SecurityManager()
        
        inputs = {
            'image_path': temp_image_file,
            'prompt': 'A beautiful landscape',
            'duration': 10,
            'aspect_ratio': '16:9',
            'cfg_scale': 0.5
        }
        
        result = manager.validate_and_sanitize_inputs(**inputs)
        
        assert result['image_path'] == temp_image_file
        assert result['prompt'] == 'A beautiful landscape'
        assert result['duration'] == 10
        assert result['aspect_ratio'] == '16:9'
        assert result['cfg_scale'] == 0.5

    def test_validate_and_sanitize_invalid_inputs(self):
        """Test validation rejection of invalid inputs"""
        manager = SecurityManager()
        
        # Test invalid image path
        with pytest.raises(ValueError, match="Invalid or missing image file"):
            manager.validate_and_sanitize_inputs(
                image_path="nonexistent.jpg",
                prompt="test"
            )
        
        # Test dangerous prompt
        with pytest.raises(ValueError, match="Invalid or dangerous prompt"):
            manager.validate_and_sanitize_inputs(
                prompt="<script>alert('xss')</script>"
            )
        
        # Test invalid duration
        with pytest.raises(ValueError, match="Invalid duration"):
            manager.validate_and_sanitize_inputs(
                duration=100
            )

    @patch('security.SecureConfig.get_api_key_secure')
    def test_get_secure_api_key_success(self, mock_get_key):
        """Test successful API key retrieval"""
        mock_get_key.return_value = "test_api_key"
        manager = SecurityManager()
        
        api_key = manager.get_secure_api_key()
        assert api_key == "test_api_key"

    @patch('security.SecureConfig.get_api_key_secure')
    def test_get_secure_api_key_failure(self, mock_get_key):
        """Test API key retrieval failure"""
        mock_get_key.return_value = None
        manager = SecurityManager()
        
        with pytest.raises(ValueError, match="API key is required"):
            manager.get_secure_api_key()


class TestSecurityIntegration:
    """Integration tests for security features"""

    @pytest.fixture
    def temp_environment(self):
        """Create isolated test environment"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            yield temp_dir
            os.chdir(original_cwd)

    def test_end_to_end_security_workflow(self, temp_environment):
        """Test complete security workflow"""
        from security import security_manager
        
        # Create test image file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            f.write(b"test image data")
            test_image = f.name
        
        try:
            # Test input validation
            validated = security_manager.validate_and_sanitize_inputs(
                image_path=test_image,
                prompt="A beautiful test video",
                duration=5,
                aspect_ratio="16:9"
            )
            
            assert validated['image_path'] == test_image
            assert validated['prompt'] == "A beautiful test video"
            assert validated['duration'] == 5
            assert validated['aspect_ratio'] == "16:9"
            
        finally:
            os.unlink(test_image)

    def test_security_with_optional_parameters(self, temp_environment):
        """Test security validation with optional parameters"""
        from security import security_manager
        
        # Create test files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f1:
            f1.write(b"main image")
            main_image = f1.name
            
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f2:
            f2.write(b"tail image")
            tail_image = f2.name
        
        try:
            validated = security_manager.validate_and_sanitize_inputs(
                image_path=main_image,
                tail_image_path=tail_image,
                prompt="Main prompt",
                negative_prompt="Negative prompt",
                duration=10,
                aspect_ratio="9:16",
                cfg_scale=0.7
            )
            
            assert all(key in validated for key in [
                'image_path', 'tail_image_path', 'prompt', 
                'negative_prompt', 'duration', 'aspect_ratio', 'cfg_scale'
            ])
            
        finally:
            os.unlink(main_image)
            os.unlink(tail_image)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])