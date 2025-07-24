#!/usr/bin/env python3
"""
Batch Processor Module - Multiple file processing with advanced scheduling
Handles batch video generation with intelligent queuing, progress tracking, and error recovery
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from colorama import Fore, Style

# Import our enhanced modules
from core.launcher.progress_tracker import AdvancedProgressTracker, ProgressStage
from core.launcher.cost_calculator import CostCalculator
from core.launcher.output_organizer import OutputOrganizer

@dataclass
class BatchJob:
    """Individual job in a batch processing queue"""
    id: str
    image_path: str
    prompt: str
    model: str
    parameters: Dict[str, Any]
    priority: int = 1  # 1-5, 5 being highest
    status: str = "pending"  # pending, processing, completed, failed, cancelled
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2
    estimated_cost: float = 0.0
    output_paths: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def start(self):
        """Mark job as started"""
        self.status = "processing"
        self.started_at = datetime.now().isoformat()
    
    def complete(self, result: Dict[str, Any], output_paths: Dict[str, str] = None):
        """Mark job as completed"""
        self.status = "completed"
        self.completed_at = datetime.now().isoformat()
        self.result = result
        if output_paths:
            self.output_paths = output_paths
    
    def fail(self, error_message: str):
        """Mark job as failed"""
        self.status = "failed"
        self.completed_at = datetime.now().isoformat()
        self.error_message = error_message
    
    def cancel(self):
        """Cancel the job"""
        self.status = "cancelled"
        self.completed_at = datetime.now().isoformat()
    
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.status == "failed" and self.retry_count < self.max_retries
    
    def retry(self):
        """Prepare job for retry"""
        if self.can_retry():
            self.retry_count += 1
            self.status = "pending"
            self.started_at = None
            self.completed_at = None
            self.error_message = None
    
    def get_duration(self) -> Optional[float]:
        """Get job duration in seconds"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.now().isoformat()
        start_dt = datetime.fromisoformat(self.started_at)
        end_dt = datetime.fromisoformat(end_time)
        
        return (end_dt - start_dt).total_seconds()

class BatchProcessor:
    """Advanced batch processing system with intelligent scheduling"""
    
    def __init__(self, max_concurrent: int = 3, save_progress: bool = True):
        self.max_concurrent = max_concurrent
        self.save_progress = save_progress
        
        # Data storage
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.batch_file = self.data_dir / "batch_processing.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Job management
        self.jobs: List[BatchJob] = []
        self.active_jobs: Dict[str, asyncio.Task] = {}
        self.completed_jobs: List[BatchJob] = []
        self.failed_jobs: List[BatchJob] = []
        
        # Progress tracking
        self.overall_progress: Optional[AdvancedProgressTracker] = None
        self.job_progress: Dict[str, ProgressStage] = {}
        
        # Utilities
        self.cost_calculator = CostCalculator()
        self.output_organizer = OutputOrganizer()
        
        # Statistics
        self.stats = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "cancelled_jobs": 0,
            "total_cost": 0.0,
            "total_processing_time": 0.0,
            "average_job_time": 0.0
        }
        
        # Callbacks
        self.job_start_callback: Optional[Callable[[BatchJob], None]] = None
        self.job_complete_callback: Optional[Callable[[BatchJob], None]] = None
        self.job_fail_callback: Optional[Callable[[BatchJob, str], None]] = None
        self.batch_complete_callback: Optional[Callable[[], None]] = None
        
        # Load existing batch data
        self._load_batch_data()
    
    def _load_batch_data(self):
        """Load existing batch processing data"""
        try:
            if self.batch_file.exists():
                with open(self.batch_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Load jobs
                    for job_data in data.get("jobs", []):
                        job = BatchJob(**job_data)
                        
                        # Categorize jobs by status
                        if job.status == "completed":
                            self.completed_jobs.append(job)
                        elif job.status in ["failed", "cancelled"]:
                            self.failed_jobs.append(job)
                        else:
                            # Reset processing jobs to pending on restart
                            if job.status == "processing":
                                job.status = "pending"
                                job.started_at = None
                            self.jobs.append(job)
                    
                    # Load statistics
                    self.stats.update(data.get("stats", {}))
                    
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Could not load batch data: {e}{Style.RESET_ALL}")
    
    def _save_batch_data(self):
        """Save batch processing data"""
        if not self.save_progress:
            return
        
        try:
            data = {
                "jobs": [asdict(job) for job in self.jobs + self.completed_jobs + self.failed_jobs],
                "stats": self.stats,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.batch_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Could not save batch data: {e}{Style.RESET_ALL}")
    
    def add_job(self, image_path: str, prompt: str, model: str, 
                parameters: Dict[str, Any] = None, priority: int = 1) -> str:
        """Add a job to the batch queue"""
        # Validate inputs
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        # Generate unique job ID
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.jobs):03d}"
        
        # Calculate estimated cost
        parameters = parameters or {}
        duration = parameters.get("duration", 5)
        cost_info = self.cost_calculator.calculate_cost(model, duration)
        estimated_cost = cost_info.get("total_cost", 0.0)
        
        # Create job
        job = BatchJob(
            id=job_id,
            image_path=image_path,
            prompt=prompt,
            model=model,
            parameters=parameters,
            priority=priority,
            estimated_cost=estimated_cost
        )
        
        # Add to queue (maintain priority order)
        self.jobs.append(job)
        self.jobs.sort(key=lambda x: (x.priority, x.created_at), reverse=True)
        
        # Update statistics
        self.stats["total_jobs"] += 1
        self.stats["total_cost"] += estimated_cost
        
        self._save_batch_data()
        
        print(f"{Fore.GREEN}✅ Added job {job_id} to batch queue{Style.RESET_ALL}")
        print(f"   📁 Image: {Path(image_path).name}")
        print(f"   📝 Prompt: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
        print(f"   💰 Estimated cost: ${estimated_cost:.3f}")
        
        return job_id
    
    def add_multiple_jobs(self, files_and_prompts: List[Tuple[str, str]], 
                         model: str, parameters: Dict[str, Any] = None,
                         shared_prompt: str = None) -> List[str]:
        """Add multiple jobs with the same model and parameters"""
        job_ids = []
        
        print(f"\n{Fore.CYAN}📦 Adding {len(files_and_prompts)} jobs to batch queue...{Style.RESET_ALL}")
        
        for i, (image_path, prompt) in enumerate(files_and_prompts):
            try:
                # Use shared prompt if provided
                final_prompt = shared_prompt or prompt
                
                # Add priority based on order (first files get higher priority)
                priority = max(1, 5 - (i // 10))  # Decrease priority every 10 jobs
                
                job_id = self.add_job(image_path, final_prompt, model, parameters, priority)
                job_ids.append(job_id)
                
            except Exception as e:
                print(f"{Fore.RED}❌ Failed to add job for {Path(image_path).name}: {e}{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}✅ Successfully added {len(job_ids)} jobs to batch queue{Style.RESET_ALL}")
        
        # Show batch summary
        self.show_batch_summary()
        
        return job_ids
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job from the queue"""
        # Find and remove from pending jobs
        for i, job in enumerate(self.jobs):
            if job.id == job_id:
                if job.status == "processing":
                    # Cancel active job
                    if job_id in self.active_jobs:
                        self.active_jobs[job_id].cancel()
                        del self.active_jobs[job_id]
                
                job.cancel()
                self.failed_jobs.append(self.jobs.pop(i))
                self.stats["cancelled_jobs"] += 1
                self._save_batch_data()
                
                print(f"{Fore.YELLOW}🗑️ Cancelled job {job_id}{Style.RESET_ALL}")
                return True
        
        print(f"{Fore.RED}❌ Job {job_id} not found in queue{Style.RESET_ALL}")
        return False
    
    def clear_queue(self, status_filter: str = None):
        """Clear jobs from queue"""
        if status_filter:
            # Clear specific status
            if status_filter == "pending":
                cleared = len([j for j in self.jobs if j.status == "pending"])
                self.jobs = [j for j in self.jobs if j.status != "pending"]
            elif status_filter == "failed":
                cleared = len(self.failed_jobs)
                self.failed_jobs.clear()
            elif status_filter == "completed":
                cleared = len(self.completed_jobs)
                self.completed_jobs.clear()
            else:
                print(f"{Fore.RED}❌ Invalid status filter: {status_filter}{Style.RESET_ALL}")
                return
        else:
            # Clear all
            cleared = len(self.jobs) + len(self.completed_jobs) + len(self.failed_jobs)
            self.jobs.clear()
            self.completed_jobs.clear()
            self.failed_jobs.clear()
            
            # Reset statistics
            self.stats = {
                "total_jobs": 0,
                "completed_jobs": 0,
                "failed_jobs": 0,
                "cancelled_jobs": 0,
                "total_cost": 0.0,
                "total_processing_time": 0.0,
                "average_job_time": 0.0
            }
        
        self._save_batch_data()
        print(f"{Fore.GREEN}✅ Cleared {cleared} jobs{Style.RESET_ALL}")
    
    def show_batch_summary(self):
        """Display batch processing summary"""
        total_jobs = len(self.jobs) + len(self.completed_jobs) + len(self.failed_jobs)
        
        if total_jobs == 0:
            print(f"{Fore.YELLOW}📦 Batch queue is empty{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}📦 Batch Processing Summary:{Style.RESET_ALL}")
        print(f"┌─────────────────────────────────────────────┐")
        print(f"│ Queue Status                                │")
        print(f"├─────────────────────────────────────────────┤")
        print(f"│ 📋 Total Jobs: {total_jobs:<27} │")
        print(f"│ ⏳ Pending: {len([j for j in self.jobs if j.status == 'pending']):<30} │")
        print(f"│ 🔄 Processing: {len([j for j in self.jobs if j.status == 'processing']):<26} │")
        print(f"│ ✅ Completed: {len(self.completed_jobs):<27} │")
        print(f"│ ❌ Failed: {len(self.failed_jobs):<31} │")
        print(f"└─────────────────────────────────────────────┘")
        
        # Cost summary
        total_estimated_cost = sum(job.estimated_cost for job in self.jobs)
        completed_cost = sum(job.estimated_cost for job in self.completed_jobs)
        
        print(f"\n💰 Cost Summary:")
        print(f"   Estimated remaining: ${total_estimated_cost:.2f}")
        print(f"   Completed cost: ${completed_cost:.2f}")
        print(f"   Total estimated: ${total_estimated_cost + completed_cost:.2f}")
        
        # Time estimates
        if self.jobs:
            avg_duration = 45  # seconds per job (estimated)
            estimated_time = len([j for j in self.jobs if j.status == "pending"]) * avg_duration
            concurrent_time = estimated_time / self.max_concurrent
            
            print(f"\n⏱️ Time Estimates:")
            print(f"   Sequential: {self._format_duration(estimated_time)}")
            print(f"   Concurrent ({self.max_concurrent} parallel): {self._format_duration(concurrent_time)}")
    
    def show_job_details(self, job_id: str = None, status: str = None, limit: int = 10):
        """Show detailed job information"""
        jobs_to_show = []
        
        if job_id:
            # Find specific job
            all_jobs = self.jobs + self.completed_jobs + self.failed_jobs
            job = next((j for j in all_jobs if j.id == job_id), None)
            if job:
                jobs_to_show = [job]
            else:
                print(f"{Fore.RED}❌ Job {job_id} not found{Style.RESET_ALL}")
                return
        elif status:
            # Filter by status
            all_jobs = self.jobs + self.completed_jobs + self.failed_jobs
            jobs_to_show = [j for j in all_jobs if j.status == status][:limit]
        else:
            # Show recent jobs
            all_jobs = self.jobs + self.completed_jobs + self.failed_jobs
            jobs_to_show = sorted(all_jobs, key=lambda x: x.created_at, reverse=True)[:limit]
        
        if not jobs_to_show:
            print(f"{Fore.YELLOW}No jobs to display{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}📋 Job Details ({len(jobs_to_show)} jobs):{Style.RESET_ALL}")
        
        for job in jobs_to_show:
            # Status icon and color
            status_info = {
                "pending": ("⏳", Fore.YELLOW),
                "processing": ("🔄", Fore.BLUE),
                "completed": ("✅", Fore.GREEN),
                "failed": ("❌", Fore.RED),
                "cancelled": ("🚫", Fore.MAGENTA)
            }
            
            icon, color = status_info.get(job.status, ("❓", Fore.WHITE))
            
            # Basic info
            print(f"\n{color}{'─' * 60}{Style.RESET_ALL}")
            print(f"{icon} {color}{job.id}{Style.RESET_ALL} | {job.status.upper()}")
            print(f"📁 Image: {Path(job.image_path).name}")
            print(f"📝 Prompt: {job.prompt[:80]}{'...' if len(job.prompt) > 80 else ''}")
            print(f"🎬 Model: {job.model}")
            print(f"💰 Cost: ${job.estimated_cost:.3f}")
            print(f"🔢 Priority: {job.priority}")
            
            # Timing info
            created = datetime.fromisoformat(job.created_at)
            print(f"📅 Created: {created.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if job.started_at:
                started = datetime.fromisoformat(job.started_at)
                print(f"🚀 Started: {started.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if job.completed_at:
                completed = datetime.fromisoformat(job.completed_at)
                print(f"🏁 Completed: {completed.strftime('%Y-%m-%d %H:%M:%S')}")
                
                duration = job.get_duration()
                if duration:
                    print(f"⏱️ Duration: {self._format_duration(duration)}")
            
            # Error info
            if job.error_message:
                print(f"❌ Error: {job.error_message}")
            
            # Retry info
            if job.retry_count > 0:
                print(f"🔄 Retries: {job.retry_count}/{job.max_retries}")
            
            # Result info
            if job.result and job.status == "completed":
                if "video" in job.result:
                    print(f"🎥 Result: Video generated successfully")
                
                if job.output_paths:
                    print(f"📁 Output: {job.output_paths.get('output_dir', 'Unknown')}")
    
    async def process_batch(self, auto_retry: bool = True, 
                           progress_callback: Callable = None) -> Dict[str, Any]:
        """Process all jobs in the batch queue"""
        if not self.jobs:
            return {"message": "No jobs to process", "stats": self.stats}
        
        pending_jobs = [job for job in self.jobs if job.status == "pending"]
        if not pending_jobs:
            return {"message": "No pending jobs to process", "stats": self.stats}
        
        print(f"\n{Fore.CYAN}🚀 Starting batch processing of {len(pending_jobs)} jobs...{Style.RESET_ALL}")
        print(f"📊 Concurrency: {self.max_concurrent} parallel jobs")
        print(f"🔄 Auto-retry: {'Enabled' if auto_retry else 'Disabled'}")
        
        # Setup progress tracking
        self.overall_progress = AdvancedProgressTracker(show_spinner=True)
        self.overall_progress.add_stage("initialize", "Initializing batch processing", 2)
        self.overall_progress.add_stage("process", f"Processing {len(pending_jobs)} jobs", 
                                       len(pending_jobs) * 45)  # Estimated 45s per job
        self.overall_progress.add_stage("finalize", "Finalizing results", 3)
        
        self.overall_progress.start()
        
        start_time = time.time()
        
        try:
            # Initialize
            stage = self.overall_progress.next_stage("Setting up batch processing...")
            await asyncio.sleep(1)  # Brief setup time
            
            # Process jobs
            stage = self.overall_progress.next_stage("Starting job processing...")
            
            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            # Create tasks for all pending jobs
            tasks = []
            for job in pending_jobs:
                task = asyncio.create_task(self._process_single_job(job, semaphore, auto_retry))
                tasks.append(task)
                self.active_jobs[job.id] = task
            
            # Process jobs with progress updates
            completed_count = 0
            for task in asyncio.as_completed(tasks):
                try:
                    job_result = await task
                    completed_count += 1
                    
                    # Update overall progress
                    progress = completed_count / len(tasks)
                    self.overall_progress.update_current_stage(
                        progress, 
                        f"Completed {completed_count}/{len(tasks)} jobs"
                    )
                    
                    if progress_callback:
                        progress_callback(completed_count, len(tasks), job_result)
                        
                except Exception as e:
                    print(f"{Fore.RED}❌ Task error: {e}{Style.RESET_ALL}")
            
            # Finalize
            stage = self.overall_progress.next_stage("Finalizing batch results...")
            
            # Update statistics
            self._update_batch_statistics()
            self._save_batch_data()
            
            # Clear active jobs
            self.active_jobs.clear()
            
            await asyncio.sleep(1)  # Brief finalization time
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Generate final report
            results = self._generate_batch_report(total_time)
            
            self.overall_progress.complete("Batch processing completed successfully!")
            
            if self.batch_complete_callback:
                self.batch_complete_callback()
            
            return results
            
        except Exception as e:
            if self.overall_progress:
                self.overall_progress.fail_current_stage(f"Batch processing failed: {str(e)}")
            
            # Cancel remaining tasks
            for task in self.active_jobs.values():
                task.cancel()
            
            self.active_jobs.clear()
            
            raise
    
    async def _process_single_job(self, job: BatchJob, semaphore: asyncio.Semaphore, 
                                 auto_retry: bool) -> Dict[str, Any]:
        """Process a single job with error handling and retry logic"""
        async with semaphore:
            try:
                job.start()
                
                if self.job_start_callback:
                    self.job_start_callback(job)
                
                print(f"\n{Fore.BLUE}🔄 Processing job {job.id}...{Style.RESET_ALL}")
                print(f"   📁 {Path(job.image_path).name}")
                print(f"   🎬 {job.model}")
                
                # Import generator here to avoid circular imports
                from main import VideoGenerator, Config
                
                config = Config()
                generator = VideoGenerator(config)
                
                # Create output structure
                output_paths = self.output_organizer.create_output_structure(
                    job.image_path, job.prompt, job.model, **job.parameters
                )
                
                # Generate video
                result = await self._generate_video_for_job(generator, job)
                
                # Save results
                video_path = self.output_organizer.save_generation_result(
                    output_paths, result, success=True
                )
                
                # Complete job
                job.complete(result, output_paths)
                
                if self.job_complete_callback:
                    self.job_complete_callback(job)
                
                # Track cost
                self.cost_calculator.track_spending(
                    job.model, job.estimated_cost, 
                    f"Batch job {job.id}"
                )
                
                print(f"{Fore.GREEN}✅ Job {job.id} completed successfully{Style.RESET_ALL}")
                if video_path:
                    print(f"   📹 Video: {video_path}")
                
                return {"job_id": job.id, "status": "completed", "result": result}
                
            except Exception as e:
                error_msg = str(e)
                job.fail(error_msg)
                
                if self.job_fail_callback:
                    self.job_fail_callback(job, error_msg)
                
                print(f"{Fore.RED}❌ Job {job.id} failed: {error_msg}{Style.RESET_ALL}")
                
                # Auto-retry logic
                if auto_retry and job.can_retry():
                    print(f"{Fore.YELLOW}🔄 Retrying job {job.id} ({job.retry_count + 1}/{job.max_retries})...{Style.RESET_ALL}")
                    job.retry()
                    
                    # Exponential backoff
                    retry_delay = 2 ** job.retry_count
                    await asyncio.sleep(retry_delay)
                    
                    return await self._process_single_job(job, semaphore, auto_retry)
                
                return {"job_id": job.id, "status": "failed", "error": error_msg}
    
    async def _generate_video_for_job(self, generator, job: BatchJob) -> Dict[str, Any]:
        """Generate video for a specific job"""
        model_config = generator.config.get("models", {}).get(job.model, {})
        
        if isinstance(model_config, dict):
            endpoint = model_config.get("endpoint")
        else:
            endpoint = model_config
        
        if not endpoint:
            raise ValueError(f"Unknown model: {job.model}")
        
        # Call appropriate generation method
        if job.model == "workflow":
            return await generator.run_workflow(
                arguments={"image_path": job.image_path, "prompt": job.prompt, **job.parameters}
            )
        else:
            return await generator.generate_video(
                endpoint, job.image_path, job.prompt, **job.parameters
            )
    
    def _update_batch_statistics(self):
        """Update batch processing statistics"""
        all_jobs = self.jobs + self.completed_jobs + self.failed_jobs
        
        self.stats["total_jobs"] = len(all_jobs)
        self.stats["completed_jobs"] = len(self.completed_jobs)
        self.stats["failed_jobs"] = len(self.failed_jobs)
        self.stats["cancelled_jobs"] = len([j for j in all_jobs if j.status == "cancelled"])
        
        # Calculate processing times
        completed_with_duration = [j for j in self.completed_jobs if j.get_duration()]
        if completed_with_duration:
            total_time = sum(j.get_duration() for j in completed_with_duration)
            self.stats["total_processing_time"] = total_time
            self.stats["average_job_time"] = total_time / len(completed_with_duration)
    
    def _generate_batch_report(self, total_batch_time: float) -> Dict[str, Any]:
        """Generate comprehensive batch processing report"""
        all_jobs = self.jobs + self.completed_jobs + self.failed_jobs
        
        report = {
            "batch_summary": {
                "total_jobs": len(all_jobs),
                "completed": len(self.completed_jobs),
                "failed": len(self.failed_jobs),
                "cancelled": len([j for j in all_jobs if j.status == "cancelled"]),
                "success_rate": (len(self.completed_jobs) / len(all_jobs)) * 100 if all_jobs else 0
            },
            "timing": {
                "total_batch_time": total_batch_time,
                "average_job_time": self.stats.get("average_job_time", 0),
                "total_processing_time": self.stats.get("total_processing_time", 0)
            },
            "cost_analysis": {
                "total_estimated_cost": sum(j.estimated_cost for j in all_jobs),
                "completed_cost": sum(j.estimated_cost for j in self.completed_jobs),
                "failed_cost_lost": sum(j.estimated_cost for j in self.failed_jobs)
            },
            "model_breakdown": {},
            "stats": self.stats
        }
        
        # Model usage breakdown
        model_usage = {}
        for job in all_jobs:
            model = job.model
            if model not in model_usage:
                model_usage[model] = {"total": 0, "completed": 0, "failed": 0}
            
            model_usage[model]["total"] += 1
            if job.status == "completed":
                model_usage[model]["completed"] += 1
            elif job.status == "failed":
                model_usage[model]["failed"] += 1
        
        report["model_breakdown"] = model_usage
        
        return report
    
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
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        all_jobs = self.jobs + self.completed_jobs + self.failed_jobs
        
        return {
            "total_jobs": len(all_jobs),
            "pending": len([j for j in self.jobs if j.status == "pending"]),
            "processing": len([j for j in self.jobs if j.status == "processing"]),
            "completed": len(self.completed_jobs),
            "failed": len(self.failed_jobs),
            "cancelled": len([j for j in all_jobs if j.status == "cancelled"]),
            "estimated_cost": sum(j.estimated_cost for j in self.jobs if j.status == "pending"),
            "active_jobs": list(self.active_jobs.keys())
        }

# Convenience functions
def create_batch_processor(max_concurrent: int = 3) -> BatchProcessor:
    """Create a batch processor instance"""
    return BatchProcessor(max_concurrent=max_concurrent)

def demo_batch_processor():
    """Demonstrate batch processor capabilities"""
    print("🎬 Batch Processor Demo")
    
    processor = BatchProcessor(max_concurrent=2)
    
    # Add demo jobs
    demo_jobs = [
        ("demo1.jpg", "Beautiful sunset over mountains", "kling_21_standard"),
        ("demo2.jpg", "Flowing river through forest", "kling_21_standard"),
        ("demo3.jpg", "City skyline at night", "kling_21_pro"),
    ]
    
    print("\nAdding demo jobs...")
    for image_path, prompt, model in demo_jobs:
        try:
            processor.add_job(image_path, prompt, model, {"duration": 5})
        except FileNotFoundError:
            print(f"⚠️ Skipping {image_path} (file not found)")
    
    # Show queue status
    processor.show_batch_summary()
    processor.show_job_details(limit=5)

# Test function
if __name__ == "__main__":
    print("Testing Batch Processor...")
    
    # Create processor
    processor = BatchProcessor(max_concurrent=2)
    
    # Test adding jobs
    try:
        job_id = processor.add_job(
            "test_image.jpg", 
            "Test prompt", 
            "kling_21_standard",
            {"duration": 5, "aspect_ratio": "16:9"}
        )
        print(f"Added test job: {job_id}")
    except FileNotFoundError:
        print("⚠️ Test image not found, skipping job creation test")
    
    # Test queue management
    status = processor.get_queue_status()
    print(f"Queue status: {status}")
    
    print("Batch Processor test completed.")
    
    # Uncomment to run full demo
    # demo_batch_processor()