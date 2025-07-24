#!/usr/bin/env python3
"""
Comprehensive test suite for the unified launcher system
Tests all components of the FAL_LAUNCHER.py and core/launcher modules
"""

import os
import sys
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    # Import launcher components
    from FAL_LAUNCHER import FALLauncher
    from core.launcher.file_picker import FilePicker
    from core.launcher.prompt_manager import PromptManager
    from core.launcher.output_organizer import OutputOrganizer
    from core.launcher.cost_calculator import CostCalculator
    from core.launcher.progress_tracker import AdvancedProgressTracker
    from core.launcher.batch_processor import BatchProcessor
    from core.gui.menu_system import MenuSystem
    LAUNCHER_MODULES_AVAILABLE = True
except ImportError as e:
    LAUNCHER_MODULES_AVAILABLE = False
    IMPORT_ERROR = str(e)

class TestFALLauncher:
    """Test the main FAL_LAUNCHER.py functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def launcher(self, temp_dir):
        """Create FALLauncher instance with temporary directory"""
        if not LAUNCHER_MODULES_AVAILABLE:
            pytest.skip(f"Launcher modules not available: {IMPORT_ERROR}")
        
        with patch.object(Path, 'parent', new=Path(temp_dir)):
            launcher = FALLauncher()
            launcher.script_dir = Path(temp_dir)
            launcher.data_dir = Path(temp_dir) / "data"
            launcher.config_dir = Path(temp_dir) / "config"
            launcher.data_dir.mkdir(exist_ok=True)
            launcher.config_dir.mkdir(exist_ok=True)
            return launcher
    
    def test_launcher_initialization(self, launcher):
        """Test launcher initializes correctly"""
        assert launcher.script_dir.exists()
        assert launcher.data_dir.exists()
        assert launcher.config_dir.exists()
        assert isinstance(launcher.settings, dict)
    
    def test_settings_loading_and_saving(self, launcher):
        """Test settings persistence"""
        # Test default settings
        assert "last_mode" in launcher.settings
        assert "preferred_model" in launcher.settings
        
        # Test settings modification and saving
        launcher.settings["test_key"] = "test_value"
        launcher._save_settings()
        
        # Create new launcher instance to test loading
        new_launcher = FALLauncher()
        new_launcher.script_dir = launcher.script_dir
        new_launcher.data_dir = launcher.data_dir
        new_launcher.config_dir = launcher.config_dir
        new_launcher.settings = new_launcher._load_settings()
        
        assert new_launcher.settings.get("test_key") == "test_value"
    
    def test_environment_check(self, launcher):
        """Test environment status checking"""
        env_status = launcher.check_environment()
        
        assert "python_version" in env_status
        assert "gui_available" in env_status
        assert "fal_key_set" in env_status
        assert "web_dependencies" in env_status
        assert "cli_dependencies" in env_status
        
        assert isinstance(env_status["python_version"], tuple)
        assert len(env_status["python_version"]) == 2
    
    @patch('subprocess.run')
    def test_launch_web_mode(self, mock_subprocess, launcher):
        """Test web mode launching"""
        # Mock web_app.py existence
        web_app_path = launcher.script_dir / "web_app.py"
        web_app_path.touch()
        
        result = launcher.launch_web_mode()
        
        assert result is True
        mock_subprocess.assert_called_once()
        assert launcher.settings["last_mode"] == "web"
        
        # Check integration data was created
        integration_file = launcher.data_dir / "web_integration.json"
        assert integration_file.exists()
        
        with open(integration_file) as f:
            integration_data = json.load(f)
            assert "launcher_version" in integration_data
            assert "user_preferences" in integration_data
    
    @patch('subprocess.run')
    def test_launch_cli_mode_fallback(self, mock_subprocess, launcher):
        """Test CLI mode with fallback to main.py"""
        # Mock main.py existence
        main_py_path = launcher.script_dir / "main.py"
        main_py_path.touch()
        
        with patch('core.launcher.unified_launcher.run_unified_launcher', side_effect=ImportError):
            result = launcher.launch_cli_mode()
        
        assert result is True
        mock_subprocess.assert_called_once()
        assert launcher.settings["last_mode"] == "cli"

@pytest.mark.skipif(not LAUNCHER_MODULES_AVAILABLE, reason="Launcher modules not available")
class TestFilePicker:
    """Test the GUI file picker functionality"""
    
    @pytest.fixture
    def file_picker(self):
        return FilePicker()
    
    def test_file_picker_initialization(self, file_picker):
        """Test file picker initializes correctly"""
        assert file_picker.supported_formats is not None
        assert len(file_picker.supported_formats) > 0
        assert ".jpg" in file_picker.supported_formats
        assert ".png" in file_picker.supported_formats
    
    @patch('tkinter.Tk')
    @patch('tkinter.filedialog.askopenfilename')
    def test_pick_single_file(self, mock_filedialog, mock_tk, file_picker):
        """Test single file selection"""
        # Mock tkinter components
        mock_root = Mock()
        mock_tk.return_value = mock_root
        mock_filedialog.return_value = "/path/to/test.jpg"
        
        # Mock the validation method to return True
        with patch.object(file_picker, '_validate_image_file', return_value=True):
            with patch.object(file_picker, '_save_last_directory'):
                result = file_picker.pick_single_file()
        
        assert result == "/path/to/test.jpg"
        mock_filedialog.assert_called_once()
        mock_root.withdraw.assert_called_once()
        mock_root.destroy.assert_called_once()
    
    def test_validate_image_file(self, file_picker):
        """Test image file validation"""
        # Mock Path.exists and Path.is_file to return True for valid extensions
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                with patch('PIL.Image.open') as mock_image_open:
                    # Mock successful image opening
                    mock_img = Mock()
                    mock_image_open.return_value.__enter__.return_value = mock_img
                    
                    # Test valid extensions
                    assert file_picker._validate_image_file("test.jpg") is True
                    assert file_picker._validate_image_file("test.PNG") is True
                    assert file_picker._validate_image_file("test.gif") is True
        
        # Test invalid extensions (these should fail even with mocked file system)
        assert file_picker._validate_image_file("test.txt") is False
        assert file_picker._validate_image_file("test.mp4") is False
        assert file_picker._validate_image_file("test") is False

@pytest.mark.skipif(not LAUNCHER_MODULES_AVAILABLE, reason="Launcher modules not available")
class TestPromptManager:
    """Test prompt history and favorites management"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def prompt_manager(self, temp_dir):
        manager = PromptManager()
        manager.data_dir = Path(temp_dir)
        return manager
    
    def test_prompt_manager_initialization(self, prompt_manager):
        """Test prompt manager initializes correctly"""
        assert prompt_manager.data_dir.exists()
        assert isinstance(prompt_manager.history, list)
        assert isinstance(prompt_manager.favorites, dict)
    
    def test_save_and_retrieve_prompt(self, prompt_manager):
        """Test saving and retrieving prompts"""
        test_prompt = "A beautiful sunset over mountains"
        test_model = "kling_21_pro"
        
        # Save prompt
        prompt_manager.save_prompt(test_prompt, test_model, success=True)
        
        # Retrieve recent prompts
        recent = prompt_manager.get_recent_prompts(limit=5)
        
        assert len(recent) >= 1
        assert recent[0]["prompt"] == test_prompt
        assert recent[0]["model"] == test_model
        assert recent[0]["success"] is True
    
    def test_favorites_management(self, prompt_manager):
        """Test favorites functionality"""
        test_prompt = "Epic dragon flying through clouds"
        favorite_name = "Dragon Flight"
        
        # Add to favorites
        prompt_manager.add_to_favorites(test_prompt, name=favorite_name)
        
        # Check favorites
        favorites = prompt_manager.get_favorites()
        assert favorite_name in favorites
        assert favorites[favorite_name]["prompt"] == test_prompt
        
        # Remove from favorites
        prompt_manager.remove_from_favorites(favorite_name)
        favorites = prompt_manager.get_favorites()
        assert favorite_name not in favorites
    
    def test_search_prompts(self, prompt_manager):
        """Test prompt search functionality"""
        # Add test prompts
        prompt_manager.save_prompt("Beautiful sunset", "kling_21_pro")
        prompt_manager.save_prompt("Amazing sunrise", "kling_21_pro")
        prompt_manager.save_prompt("Dark stormy night", "kling_21_pro")
        
        # Search for sun-related prompts
        sun_prompts = prompt_manager.search_prompts("sun")
        assert len(sun_prompts) >= 2
        
        # Search for specific word
        storm_prompts = prompt_manager.search_prompts("storm")
        assert len(storm_prompts) >= 1

@pytest.mark.skipif(not LAUNCHER_MODULES_AVAILABLE, reason="Launcher modules not available")
class TestCostCalculator:
    """Test cost calculation and budget tracking"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def cost_calculator(self, temp_dir):
        calculator = CostCalculator()
        calculator.data_dir = Path(temp_dir)
        return calculator
    
    def test_cost_calculation(self, cost_calculator):
        """Test cost calculation for different models"""
        # Test Kling 2.1 Pro
        cost_info = cost_calculator.calculate_cost("kling_21_pro", duration=5)
        assert cost_info["cost"] == 0.45
        assert cost_info["model"] == "kling_21_pro"
        assert cost_info["duration"] == 5
        
        # Test different duration
        cost_info = cost_calculator.calculate_cost("kling_21_standard", duration=10)
        assert cost_info["cost"] == 0.50  # $0.25 * 2 (10s = 2 * 5s)
    
    def test_spending_tracking(self, cost_calculator):
        """Test spending tracking functionality"""
        # Track some spending
        cost_calculator.track_spending("kling_21_pro", 0.45, "Test generation")
        cost_calculator.track_spending("kling_21_standard", 0.25, "Another test")
        
        # Get spending summary
        summary = cost_calculator.get_spending_summary()
        
        assert summary["total_spent"] == 0.70
        assert summary["generation_count"] == 2
        assert len(summary["by_model"]) == 2
    
    def test_budget_management(self, cost_calculator):
        """Test budget setting and alerts"""
        # Set budget
        cost_calculator.set_monthly_budget(10.00)
        
        # Check budget status
        budget_info = cost_calculator.get_budget_status()
        assert budget_info["budget"] == 10.00
        assert budget_info["remaining"] == 10.00
        
        # Track spending
        cost_calculator.track_spending("kling_21_pro", 8.00, "Large generation")
        
        # Check updated budget
        budget_info = cost_calculator.get_budget_status()
        assert budget_info["remaining"] == 2.00
        assert budget_info["percentage_used"] == 80.0

@pytest.mark.skipif(not LAUNCHER_MODULES_AVAILABLE, reason="Launcher modules not available")
class TestOutputOrganizer:
    """Test smart output organization"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def output_organizer(self, temp_dir):
        organizer = OutputOrganizer()
        organizer.base_output_dir = Path(temp_dir)
        return organizer
    
    def test_output_structure_creation(self, output_organizer):
        """Test creation of organized output structure"""
        source_image = "/path/to/test_image.jpg"
        prompt = "Beautiful landscape with mountains"
        model = "kling_21_pro"
        
        output_paths = output_organizer.create_output_structure(source_image, prompt, model)
        
        assert "output_dir" in output_paths
        assert "metadata_file" in output_paths
        assert output_paths["output_dir"].exists()
        
        # Check directory structure
        output_dir = output_paths["output_dir"]
        assert output_dir.name.startswith("test_image_")
    
    def test_metadata_generation(self, output_organizer):
        """Test metadata file generation"""
        source_image = "/path/to/test.jpg"
        prompt = "Test prompt"
        model = "kling_21_pro"
        
        output_paths = output_organizer.create_output_structure(source_image, prompt, model)
        
        # Simulate generation result
        result = {
            "video_url": "https://example.com/video.mp4",
            "request_id": "test-123",
            "status": "completed"
        }
        
        output_organizer.save_generation_result(output_paths, result)
        
        # Check metadata file
        metadata_file = output_paths["metadata_file"]
        assert metadata_file.exists()
        
        with open(metadata_file) as f:
            metadata = json.load(f)
            assert metadata["source_image"] == source_image
            assert metadata["prompt"] == prompt
            assert metadata["model"] == model
            assert metadata["generation_result"] == result

@pytest.mark.skipif(not LAUNCHER_MODULES_AVAILABLE, reason="Launcher modules not available")
class TestProgressTracker:
    """Test multi-stage progress tracking"""
    
    @pytest.fixture
    def progress_tracker(self):
        return AdvancedProgressTracker()
    
    def test_progress_tracker_initialization(self, progress_tracker):
        """Test progress tracker initializes correctly"""
        assert len(progress_tracker.stages) == 0
        assert progress_tracker.current_stage_index == 0
    
    def test_stage_management(self, progress_tracker):
        """Test adding and managing stages"""
        # Add stages
        progress_tracker.add_stage("Upload", "Uploading image file", 2.0)
        progress_tracker.add_stage("Processing", "Processing video generation", 30.0)
        progress_tracker.add_stage("Download", "Downloading result", 5.0)
        
        assert len(progress_tracker.stages) == 3
        assert progress_tracker.stages[0]["name"] == "Upload"
        assert progress_tracker.get_total_estimated_time() == 37.0
    
    def test_progress_updates(self, progress_tracker):
        """Test progress updates and calculations"""
        # Add stages
        progress_tracker.add_stage("Stage 1", "First stage", 10.0)
        progress_tracker.add_stage("Stage 2", "Second stage", 20.0)
        
        # Start tracking
        progress_tracker.start()
        
        # Update first stage
        progress_tracker.update_current_stage(0.5, "Halfway through stage 1")
        
        overall_progress = progress_tracker.get_overall_progress()
        assert 0 < overall_progress < 1
        
        # Complete first stage and move to second
        progress_tracker.complete_current_stage()
        progress_tracker.update_current_stage(0.25, "Quarter through stage 2")
        
        overall_progress = progress_tracker.get_overall_progress()
        assert overall_progress > 0.33  # Should be more than first stage completion

@pytest.mark.skipif(not LAUNCHER_MODULES_AVAILABLE, reason="Launcher modules not available")
class TestBatchProcessor:
    """Test batch processing functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def batch_processor(self, temp_dir):
        processor = BatchProcessor()
        processor.data_dir = Path(temp_dir)
        return processor
    
    def test_batch_processor_initialization(self, batch_processor):
        """Test batch processor initializes correctly"""
        assert len(batch_processor.job_queue) == 0
        assert batch_processor.max_concurrent_jobs > 0
    
    def test_job_queue_management(self, batch_processor):
        """Test adding and managing batch jobs"""
        # Add jobs
        job1 = {
            "image_path": "/path/to/image1.jpg",
            "prompt": "Beautiful sunset",
            "model": "kling_21_pro",
            "duration": 5
        }
        
        job2 = {
            "image_path": "/path/to/image2.jpg", 
            "prompt": "Mountain landscape",
            "model": "kling_21_standard",
            "duration": 5
        }
        
        batch_processor.add_job(job1)
        batch_processor.add_job(job2)
        
        assert len(batch_processor.job_queue) == 2
        assert batch_processor.job_queue[0]["status"] == "queued"
    
    def test_job_validation(self, batch_processor):
        """Test job validation"""
        # Valid job
        valid_job = {
            "image_path": "/path/to/image.jpg",
            "prompt": "Test prompt",
            "model": "kling_21_pro",
            "duration": 5
        }
        
        assert batch_processor.validate_job(valid_job) is True
        
        # Invalid job (missing required field)
        invalid_job = {
            "image_path": "/path/to/image.jpg",
            "model": "kling_21_pro"
            # Missing prompt and duration
        }
        
        assert batch_processor.validate_job(invalid_job) is False

@pytest.mark.skipif(not LAUNCHER_MODULES_AVAILABLE, reason="Launcher modules not available")
class TestMenuSystem:
    """Test questionnaire-style menu system"""
    
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def menu_system(self, temp_dir):
        menu = MenuSystem()
        menu.data_dir = Path(temp_dir)
        return menu
    
    def test_menu_system_initialization(self, menu_system):
        """Test menu system initializes correctly"""
        assert menu_system.data_dir.exists()
        assert len(menu_system.user_types) > 0
        assert "beginner" in menu_system.user_types
        assert "professional" in menu_system.user_types
    
    def test_user_type_detection(self, menu_system):
        """Test user type detection"""
        # Mock user responses for beginner
        with patch('builtins.input', side_effect=['1', '1', '1']):  # Beginner responses
            user_type = menu_system.detect_user_type()
            assert user_type in menu_system.user_types
    
    def test_workflow_availability(self, menu_system):
        """Test workflow availability for different user types"""
        workflows = menu_system.get_available_workflows("beginner")
        assert "quick_start" in workflows
        
        workflows = menu_system.get_available_workflows("professional")
        assert "batch_processing" in workflows

class TestLauncherIntegration:
    """Integration tests for the complete launcher system"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory with necessary files"""
        temp_dir = tempfile.mkdtemp()
        
        # Create necessary files for testing
        (Path(temp_dir) / "main.py").touch()
        (Path(temp_dir) / "web_app.py").touch()
        (Path(temp_dir) / "FAL_LAUNCHER.py").write_text("")
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_migration_backup_integrity(self, temp_project_dir):
        """Test that migration backup contains all necessary files"""
        backup_dir = Path(temp_project_dir) / "launcher_backup"
        
        if backup_dir.exists():
            # Find latest migration backup
            migration_dirs = [d for d in backup_dir.iterdir() if d.name.startswith("migration_")]
            if migration_dirs:
                latest_backup = max(migration_dirs, key=lambda x: x.name)
                
                # Check if info file exists
                info_file = latest_backup / "migration_info.txt"
                if info_file.exists():
                    assert info_file.read_text().find("Migration Date:") != -1
    
    def test_legacy_launcher_redirects(self, temp_project_dir):
        """Test that legacy launchers exist and redirect properly"""
        project_path = Path(temp_project_dir)
        
        # Check if legacy launchers exist
        legacy_launchers = [
            "DOUBLE_CLICK_ME.bat",
            "start.bat", 
            "LAUNCH.bat"
        ]
        
        for launcher in legacy_launchers:
            launcher_path = project_path / launcher
            if launcher_path.exists():
                content = launcher_path.read_text()
                assert "FAL_LAUNCHER.py" in content, f"{launcher} should redirect to FAL_LAUNCHER.py"

def run_comprehensive_test():
    """Run all launcher tests and generate report"""
    print("🧪 Running Comprehensive Launcher System Tests")
    print("=" * 60)
    
    # Test availability of modules
    if not LAUNCHER_MODULES_AVAILABLE:
        print(f"❌ Launcher modules not available: {IMPORT_ERROR}")
        print("   Install requirements or check module paths")
        return False
    
    # Run tests with pytest
    test_args = [
        __file__,
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ]
    
    try:
        exit_code = pytest.main(test_args)
        
        if exit_code == 0:
            print("\n✅ All launcher system tests passed!")
            print("🎉 Unified launcher system is fully functional!")
            return True
        else:
            print(f"\n❌ Some tests failed (exit code: {exit_code})")
            return False
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)