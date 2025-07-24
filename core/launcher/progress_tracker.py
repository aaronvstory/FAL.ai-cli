#!/usr/bin/env python3
"""
Progress Tracker Module - Advanced multi-stage progress visualization
Provides detailed progress tracking with ETA, stage management, and visual indicators
"""

import time
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from colorama import Fore, Style
import sys

class ProgressStage:
    """Individual progress stage with status and timing"""
    
    def __init__(self, name: str, description: str, estimated_duration: float = 0):
        self.name = name
        self.description = description
        self.estimated_duration = estimated_duration  # seconds
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.status = "pending"  # pending, active, completed, failed
        self.progress = 0.0  # 0.0 to 1.0
        self.message = ""
        self.substages: List[Dict[str, Any]] = []
    
    def start(self):
        """Mark stage as started"""
        self.start_time = datetime.now()
        self.status = "active"
    
    def complete(self, message: str = ""):
        """Mark stage as completed"""
        self.end_time = datetime.now()
        self.status = "completed"
        self.progress = 1.0
        if message:
            self.message = message
    
    def fail(self, error_message: str = ""):
        """Mark stage as failed"""
        self.end_time = datetime.now()
        self.status = "failed"
        if error_message:
            self.message = error_message
    
    def update_progress(self, progress: float, message: str = ""):
        """Update stage progress"""
        self.progress = max(0.0, min(1.0, progress))
        if message:
            self.message = message
    
    def get_elapsed_time(self) -> Optional[float]:
        """Get elapsed time in seconds"""
        if not self.start_time:
            return None
        
        end_time = self.end_time or datetime.now()
        return (end_time - self.start_time).total_seconds()
    
    def get_eta(self) -> Optional[float]:
        """Get estimated time to completion"""
        if self.status != "active" or self.progress <= 0:
            return None
        
        elapsed = self.get_elapsed_time()
        if not elapsed:
            return None
        
        # Calculate ETA based on current progress
        if self.progress > 0:
            total_estimated = elapsed / self.progress
            return total_estimated - elapsed
        
        return self.estimated_duration

class AdvancedProgressTracker:
    """Advanced progress tracker with multi-stage visualization"""
    
    def __init__(self, show_eta: bool = True, show_spinner: bool = True):
        self.stages: List[ProgressStage] = []
        self.current_stage_index = -1
        self.show_eta = show_eta
        self.show_spinner = show_spinner
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.overall_status = "not_started"  # not_started, running, completed, failed
        
        # Visual elements
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.spinner_thread: Optional[threading.Thread] = None
        self.spinner_running = False
        
        # Callbacks
        self.stage_start_callback: Optional[Callable] = None
        self.stage_complete_callback: Optional[Callable] = None
        self.progress_update_callback: Optional[Callable] = None
    
    def add_stage(self, name: str, description: str, estimated_duration: float = 0) -> ProgressStage:
        """Add a new stage to the tracker"""
        stage = ProgressStage(name, description, estimated_duration)
        self.stages.append(stage)
        return stage
    
    def start(self):
        """Start the overall progress tracking"""
        self.start_time = datetime.now()
        self.overall_status = "running"
        
        if self.show_spinner:
            self._start_spinner()
        
        self._display_header()
    
    def next_stage(self, message: str = "") -> Optional[ProgressStage]:
        """Move to the next stage"""
        # Complete current stage if exists
        if 0 <= self.current_stage_index < len(self.stages):
            current_stage = self.stages[self.current_stage_index]
            if current_stage.status == "active":
                current_stage.complete(message)
                
                if self.stage_complete_callback:
                    self.stage_complete_callback(current_stage)
        
        # Move to next stage
        self.current_stage_index += 1
        
        if self.current_stage_index >= len(self.stages):
            return None  # No more stages
        
        next_stage = self.stages[self.current_stage_index]
        next_stage.start()
        
        if self.stage_start_callback:
            self.stage_start_callback(next_stage)
        
        self._update_display()
        return next_stage
    
    def update_current_stage(self, progress: float, message: str = ""):
        """Update current stage progress"""
        if 0 <= self.current_stage_index < len(self.stages):
            stage = self.stages[self.current_stage_index]
            stage.update_progress(progress, message)
            
            if self.progress_update_callback:
                self.progress_update_callback(stage)
            
            self._update_display()
    
    def fail_current_stage(self, error_message: str = ""):
        """Mark current stage as failed"""
        if 0 <= self.current_stage_index < len(self.stages):
            stage = self.stages[self.current_stage_index]
            stage.fail(error_message)
            self.overall_status = "failed"
            
            self._stop_spinner()
            self._update_display()
    
    def complete(self, message: str = "All stages completed successfully"):
        """Complete all progress tracking"""
        # Complete current stage if active
        if 0 <= self.current_stage_index < len(self.stages):
            current_stage = self.stages[self.current_stage_index]
            if current_stage.status == "active":
                current_stage.complete()
        
        self.end_time = datetime.now()
        self.overall_status = "completed"
        
        self._stop_spinner()
        self._display_completion(message)
    
    def _start_spinner(self):
        """Start the spinner animation"""
        self.spinner_running = True
        self.spinner_thread = threading.Thread(target=self._spinner_animation, daemon=True)
        self.spinner_thread.start()
    
    def _stop_spinner(self):
        """Stop the spinner animation"""
        self.spinner_running = False
        if self.spinner_thread:
            self.spinner_thread.join(timeout=0.5)
    
    def _spinner_animation(self):
        """Spinner animation loop"""
        while self.spinner_running:
            if self.current_stage_index >= 0 and self.current_stage_index < len(self.stages):
                current_stage = self.stages[self.current_stage_index]
                if current_stage.status == "active":
                    # Update spinner character
                    self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
                    self._update_display()
            
            time.sleep(0.1)
    
    def _display_header(self):
        """Display progress tracker header"""
        print(f"\n{Fore.CYAN}{'=' * 70}")
        print(f"🎬 FAL.AI Video Generation Progress")
        print(f"{'=' * 70}{Style.RESET_ALL}")
        print(f"📊 Total Stages: {len(self.stages)}")
        if self.show_eta and self.start_time:
            total_estimated = sum(stage.estimated_duration for stage in self.stages)
            if total_estimated > 0:
                print(f"⏱️ Estimated Total Time: {self._format_duration(total_estimated)}")
        print()
    
    def _update_display(self):
        """Update the progress display"""
        if not self.stages:
            return
        
        # Clear previous lines (simple approach)
        print("\r" + " " * 80, end="")
        print(f"\r", end="")
        
        # Display current stage info
        if 0 <= self.current_stage_index < len(self.stages):
            current_stage = self.stages[self.current_stage_index]
            
            # Stage status icon
            status_icons = {
                "pending": "⏳",
                "active": self.spinner_chars[self.spinner_index] if self.show_spinner else "🔄",
                "completed": "✅",
                "failed": "❌"
            }
            
            icon = status_icons.get(current_stage.status, "❓")
            
            # Progress bar
            progress_bar = self._create_progress_bar(current_stage.progress)
            
            # ETA calculation
            eta_text = ""
            if self.show_eta and current_stage.status == "active":
                eta = current_stage.get_eta()
                if eta and eta > 0:
                    eta_text = f" | ETA: {self._format_duration(eta)}"
            
            # Stage info
            stage_text = f"{icon} {current_stage.name}"
            progress_text = f"{progress_bar} {current_stage.progress*100:.1f}%{eta_text}"
            
            print(f"\r{stage_text:<30} {progress_text}", end="", flush=True)
            
            # Message on new line if exists
            if current_stage.message:
                print(f"\n   💬 {current_stage.message}", end="", flush=True)
        
        # Overall progress
        completed_stages = sum(1 for stage in self.stages if stage.status == "completed")
        overall_progress = completed_stages / len(self.stages) if self.stages else 0
        
        print(f"\n📈 Overall Progress: {overall_progress*100:.1f}% ({completed_stages}/{len(self.stages)} stages)", end="", flush=True)
    
    def _display_completion(self, message: str):
        """Display completion message"""
        print(f"\n\n{Fore.GREEN}{'=' * 70}")
        print(f"✅ {message}")
        print(f"{'=' * 70}{Style.RESET_ALL}")
        
        if self.start_time and self.end_time:
            total_time = (self.end_time - self.start_time).total_seconds()
            print(f"⏱️ Total Time: {self._format_duration(total_time)}")
        
        # Summary of stages
        print(f"\n📋 Stage Summary:")
        for i, stage in enumerate(self.stages, 1):
            status_icons = {"completed": "✅", "failed": "❌", "pending": "⏳", "active": "🔄"}
            icon = status_icons.get(stage.status, "❓")
            elapsed = stage.get_elapsed_time()
            time_text = f" ({self._format_duration(elapsed)})" if elapsed else ""
            
            print(f"  {i}. {icon} {stage.name}{time_text}")
            if stage.message:
                print(f"     💬 {stage.message}")
        
        print()
    
    def _create_progress_bar(self, progress: float, width: int = 20) -> str:
        """Create a visual progress bar"""
        filled = int(progress * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

class FALProgressTracker(AdvancedProgressTracker):
    """Specialized progress tracker for FAL.AI video generation"""
    
    def __init__(self, model: str = "unknown", **kwargs):
        super().__init__(**kwargs)
        self.model = model
        
        # Define standard FAL.AI generation stages
        self._setup_fal_stages()
    
    def _setup_fal_stages(self):
        """Setup standard FAL.AI generation stages"""
        stages_config = [
            ("validation", "Validating inputs and parameters", 2),
            ("upload", "Uploading image to FAL.AI servers", 5),
            ("queue", "Waiting in generation queue", 10),
            ("processing", "AI model generating video", 30),
            ("postprocess", "Post-processing and optimization", 8),
            ("download", "Downloading generated video", 5)
        ]
        
        for name, description, duration in stages_config:
            self.add_stage(name, description, duration)
    
    def handle_fal_queue_update(self, update):
        """Handle FAL.AI queue updates"""
        try:
            # Parse different types of FAL updates
            if hasattr(update, 'logs') and update.logs:
                for log_entry in update.logs:
                    message = log_entry.get('message', '')
                    
                    # Map log messages to stages and progress
                    if 'upload' in message.lower():
                        self._move_to_stage("upload")
                        self.update_current_stage(0.5, message)
                    elif 'queue' in message.lower() or 'waiting' in message.lower():
                        self._move_to_stage("queue")
                        self.update_current_stage(0.3, message)
                    elif 'processing' in message.lower() or 'generating' in message.lower():
                        self._move_to_stage("processing")
                        self.update_current_stage(0.1, message)
                    elif 'complete' in message.lower() or 'finished' in message.lower():
                        self._move_to_stage("postprocess")
                        self.update_current_stage(0.8, message)
            
            # Handle different update types
            elif hasattr(update, 'status'):
                status = update.status.lower()
                if status == 'in_progress':
                    if self.current_stage_index < 0:
                        self.next_stage("Starting generation...")
                elif status == 'completed':
                    self._move_to_stage("download")
                    self.update_current_stage(1.0, "Generation completed!")
        
        except Exception as e:
            # Don't let progress tracking errors break the generation
            current_stage = self.get_current_stage()
            if current_stage:
                current_stage.message = f"Progress update error: {str(e)}"
    
    def _move_to_stage(self, stage_name: str):
        """Move to a specific stage by name"""
        target_index = -1
        for i, stage in enumerate(self.stages):
            if stage.name == stage_name:
                target_index = i
                break
        
        if target_index >= 0 and target_index > self.current_stage_index:
            # Complete intermediate stages
            while self.current_stage_index < target_index:
                if self.current_stage_index >= 0:
                    self.stages[self.current_stage_index].complete()
                self.current_stage_index += 1
            
            # Start target stage
            if self.current_stage_index < len(self.stages):
                self.stages[self.current_stage_index].start()
                self._update_display()
    
    def get_current_stage(self) -> Optional[ProgressStage]:
        """Get the current active stage"""
        if 0 <= self.current_stage_index < len(self.stages):
            return self.stages[self.current_stage_index]
        return None

class SimpleProgressBar:
    """Simple progress bar for basic use cases"""
    
    def __init__(self, total: int = 100, width: int = 50, prefix: str = "Progress"):
        self.total = total
        self.width = width
        self.prefix = prefix
        self.current = 0
        self.start_time = time.time()
    
    def update(self, progress: int, message: str = ""):
        """Update progress bar"""
        self.current = min(progress, self.total)
        
        # Calculate percentage and create bar
        percent = (self.current / self.total) * 100
        filled = int(self.width * self.current // self.total)
        bar = "█" * filled + "░" * (self.width - filled)
        
        # Calculate ETA
        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta = (elapsed / self.current) * (self.total - self.current)
            eta_text = f" | ETA: {eta:.1f}s" if eta > 0 else " | Complete"
        else:
            eta_text = ""
        
        # Display
        progress_text = f"\r{self.prefix}: [{bar}] {percent:.1f}%{eta_text}"
        if message:
            progress_text += f" | {message}"
        
        print(progress_text, end="", flush=True)
        
        if self.current >= self.total:
            print()  # New line when complete

# Convenience functions
def create_fal_progress_tracker(model: str = "unknown") -> FALProgressTracker:
    """Create a FAL.AI-specific progress tracker"""
    return FALProgressTracker(model=model)

def create_simple_progress_bar(total: int = 100, prefix: str = "Progress") -> SimpleProgressBar:
    """Create a simple progress bar"""
    return SimpleProgressBar(total=total, prefix=prefix)

def demo_progress_tracker():
    """Demo of the progress tracker functionality"""
    print("🎬 FAL.AI Progress Tracker Demo")
    
    # Create tracker
    tracker = FALProgressTracker(model="kling_21_pro")
    tracker.start()
    
    # Simulate generation process
    stages = [
        ("validation", 1.0, "Input validation complete"),
        ("upload", 3.0, "Image uploaded successfully"),
        ("queue", 5.0, "Position in queue: 1"),
        ("processing", 15.0, "AI model generating video..."),
        ("postprocess", 2.0, "Optimizing video quality"),
        ("download", 2.0, "Video ready for download")
    ]
    
    for stage_name, duration, final_message in stages:
        stage = tracker.next_stage()
        if not stage:
            break
        
        # Simulate progress within stage
        steps = int(duration * 10)  # 10 updates per second
        for i in range(steps):
            progress = (i + 1) / steps
            message = f"Processing... {progress*100:.0f}%" if i < steps - 1 else final_message
            tracker.update_current_stage(progress, message)
            time.sleep(0.1)
    
    tracker.complete("Video generation completed successfully!")

# Test function
if __name__ == "__main__":
    print("Testing Progress Tracker...")
    
    # Test simple progress bar
    print("\n1. Testing Simple Progress Bar:")
    simple_bar = SimpleProgressBar(total=100, prefix="Download")
    for i in range(101):
        simple_bar.update(i, f"Downloading file... {i}%")
        time.sleep(0.02)
    
    print("\n2. Testing Advanced Progress Tracker:")
    tracker = AdvancedProgressTracker()
    tracker.add_stage("prepare", "Preparing data", 2)
    tracker.add_stage("process", "Processing data", 5)
    tracker.add_stage("finalize", "Finalizing results", 1)
    
    tracker.start()
    
    # Simulate stages
    for _ in range(3):
        stage = tracker.next_stage()
        if not stage:
            break
        
        for i in range(10):
            progress = (i + 1) / 10
            tracker.update_current_stage(progress, f"Step {i+1}/10")
            time.sleep(0.1)
    
    tracker.complete("All stages completed!")
    
    print("\nProgress Tracker test completed.")
    
    # Uncomment to run full demo
    # demo_progress_tracker()