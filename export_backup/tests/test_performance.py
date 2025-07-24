#!/usr/bin/env python3
"""
Performance and load tests for FAL.AI Video Generator
"""

import pytest
import asyncio
import time
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from concurrent.futures import ThreadPoolExecutor

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import Config, VideoGenerator


class TestPerformance:
    """Performance and load testing"""

    @pytest.fixture
    def test_config(self):
        """Create test configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "test_settings.json"
            test_settings = {
                "fal_api_key": "",
                "default_model": "test_model",
                "output_directory": str(Path(temp_dir) / "outputs"),
                "log_level": "ERROR",  # Reduce log noise during testing
                "max_duration": 5,
                "default_aspect_ratio": "16:9"
            }
            
            import json
            config_file.write_text(json.dumps(test_settings, indent=2))
            yield Config(str(config_file))

    @pytest.fixture
    def mock_fast_fal_client(self):
        """Mock FAL client with fast responses"""
        with patch('main.fal_client') as mock:
            # Simulate fast responses
            mock.upload_file.return_value = "https://test.url/file.jpg"
            mock.subscribe.return_value = {"video_url": "https://test.url/video.mp4"}
            
            # Fast async responses
            async def fast_submit_async(*args, **kwargs):
                handler = AsyncMock()
                handler.iter_events = Mock(return_value=async_iter([{"event": "complete"}]))
                handler.get = AsyncMock(return_value={"video_url": "https://test.url/video.mp4"})
                return handler
            
            mock.submit_async.side_effect = fast_submit_async
            yield mock

    def test_config_loading_performance(self):
        """Test configuration loading performance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "perf_config.json"
            
            # Create large config file to test performance
            large_config = {
                "fal_api_key": "",
                "models": {f"model_{i}": f"test_model_{i}" for i in range(1000)},
                "settings": {f"setting_{i}": f"value_{i}" for i in range(1000)}
            }
            
            import json
            config_file.write_text(json.dumps(large_config, indent=2))
            
            # Measure loading time
            start_time = time.time()
            config = Config(str(config_file))
            load_time = time.time() - start_time
            
            # Should load large config in reasonable time
            assert load_time < 1.0  # Less than 1 second
            assert config.get("models") is not None

    @pytest.mark.asyncio
    async def test_single_video_generation_performance(self, test_config, mock_fast_fal_client):
        """Test single video generation performance"""
        generator = VideoGenerator(test_config)
        
        # Create test image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            f.write(b"test image data")
            test_file = f.name
        
        try:
            start_time = time.time()
            result = await generator.generate_kling_pro(
                test_file,
                "Test performance prompt",
                duration=5,
                aspect_ratio="16:9"
            )
            generation_time = time.time() - start_time
            
            # Should complete quickly with mocked client
            assert generation_time < 2.0  # Less than 2 seconds
            assert "video_url" in result
            
        finally:
            os.unlink(test_file)

    @pytest.mark.asyncio
    async def test_concurrent_generations_performance(self, test_config, mock_fast_fal_client):
        """Test concurrent video generation performance"""
        generator = VideoGenerator(test_config)
        
        # Create multiple test images
        test_files = []
        for i in range(5):
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
                f.write(f"test image data {i}".encode())
                test_files.append(f.name)
        
        try:
            # Create concurrent generation tasks
            async def generate_video(image_path, prompt):
                return await generator.generate_kling_pro(
                    image_path,
                    prompt,
                    duration=5,
                    aspect_ratio="16:9"
                )
            
            tasks = [
                generate_video(test_files[i], f"Test prompt {i}")
                for i in range(5)
            ]
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            # Concurrent execution should be faster than sequential
            assert total_time < 5.0  # Less than 5 seconds for 5 concurrent tasks
            assert len(results) == 5
            assert all("video_url" in result for result in results)
            
        finally:
            for test_file in test_files:
                os.unlink(test_file)

    def test_memory_usage_during_operations(self, test_config):
        """Test memory usage during intensive operations"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        generators = []
        for i in range(10):
            generators.append(VideoGenerator(test_config))
        
        # Force garbage collection
        gc.collect()
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Clean up
        del generators
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_increase = peak_memory - initial_memory
        memory_cleanup = peak_memory - final_memory
        
        # Memory usage should be reasonable
        assert memory_increase < 100  # Less than 100MB increase
        # Note: Garbage collection in tests is unpredictable, so we just check memory increase

    @pytest.mark.asyncio
    async def test_large_file_handling_performance(self, test_config, mock_fast_fal_client):
        """Test performance with large files"""
        generator = VideoGenerator(test_config)
        
        # Create large test file (simulated)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
            # Write larger data to simulate big image
            f.write(b"test image data" * 10000)  # ~150KB
            large_file = f.name
        
        try:
            start_time = time.time()
            result = await generator.generate_kling_pro(
                large_file,
                "Test large file performance",
                duration=5
            )
            processing_time = time.time() - start_time
            
            # Should handle larger files efficiently
            assert processing_time < 3.0
            assert "video_url" in result
            
        finally:
            os.unlink(large_file)

    def test_configuration_access_performance(self, test_config):
        """Test configuration access performance"""
        # Measure repeated configuration access
        start_time = time.time()
        
        for _ in range(1000):
            value = test_config.get("default_model")
            assert value is not None
        
        access_time = time.time() - start_time
        
        # Configuration access should be very fast
        assert access_time < 0.1  # Less than 100ms for 1000 accesses

    @pytest.mark.asyncio
    async def test_error_handling_performance(self, test_config):
        """Test performance during error conditions"""
        generator = VideoGenerator(test_config)
        
        # Test with non-existent file
        start_time = time.time()
        
        try:
            await generator.generate_kling_pro(
                "nonexistent_file.jpg",
                "Test error handling",
                duration=5
            )
        except Exception:
            pass  # Expected to fail
        
        error_handling_time = time.time() - start_time
        
        # Error handling should be fast
        assert error_handling_time < 1.0

    def test_startup_performance(self):
        """Test application startup performance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "startup_config.json"
            
            import json
            config_file.write_text(json.dumps({
                "fal_api_key": "",
                "default_model": "test_model",
                "output_directory": str(Path(temp_dir) / "outputs"),
                "log_level": "ERROR"
            }))
            
            # Measure startup time
            start_time = time.time()
            config = Config(str(config_file))
            generator = VideoGenerator(config)
            startup_time = time.time() - start_time
            
            # Startup should be fast
            assert startup_time < 0.5  # Less than 500ms
            assert generator is not None


class TestLoadTesting:
    """Load and stress testing"""

    @pytest.fixture
    def stress_test_config(self):
        """Configuration for stress testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "stress_config.json"
            
            import json
            config_file.write_text(json.dumps({
                "fal_api_key": "",
                "default_model": "test_model",
                "output_directory": str(Path(temp_dir) / "outputs"),
                "log_level": "CRITICAL",  # Minimal logging for performance
                "max_duration": 3  # Shorter duration for faster tests
            }))
            
            yield Config(str(config_file))

    @pytest.mark.asyncio
    async def test_high_concurrency_load(self, stress_test_config):
        """Test high concurrency load"""
        with patch('main.fal_client') as mock:
            # Very fast mock responses
            mock.upload_file.return_value = "https://test.url/file.jpg"
            mock.subscribe.return_value = {"video_url": "https://test.url/video.mp4"}
            
            generator = VideoGenerator(stress_test_config)
            
            # Create many test files
            test_files = []
            for i in range(20):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
                    f.write(f"test data {i}".encode())
                    test_files.append(f.name)
            
            try:
                # Create high-concurrency tasks
                async def generate_video(image_path, index):
                    return await generator.generate_kling_pro(
                        image_path,
                        f"Load test prompt {index}",
                        duration=3
                    )
                
                tasks = [
                    generate_video(test_files[i], i)
                    for i in range(20)
                ]
                
                start_time = time.time()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                total_time = time.time() - start_time
                
                # Should handle high concurrency
                successful_results = [r for r in results if not isinstance(r, Exception)]
                assert len(successful_results) >= 18  # At least 90% success rate
                assert total_time < 10.0  # Complete within reasonable time
                
            finally:
                for test_file in test_files:
                    try:
                        os.unlink(test_file)
                    except:
                        pass

    def test_resource_limits_handling(self, stress_test_config):
        """Test handling of resource limits"""
        # Test with many generator instances
        generators = []
        
        try:
            for i in range(50):
                generators.append(VideoGenerator(stress_test_config))
            
            # All generators should be created successfully
            assert len(generators) == 50
            
            # Basic functionality should still work
            test_generator = generators[0]
            assert test_generator.config is not None
            
        finally:
            # Clean up
            del generators


# Utility functions
async def async_iter(items):
    """Helper to create async iterator from list"""
    for item in items:
        yield item


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])