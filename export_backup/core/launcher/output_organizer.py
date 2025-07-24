#!/usr/bin/env python3
"""
Output Organizer Module - Smart file organization and metadata management
Handles output organization, metadata storage, and cleanup utilities
"""

import os
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from urllib.parse import urlparse
import hashlib

class OutputOrganizer:
    """Smart output organization with metadata and cleanup"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.script_dir / "data"
        self.outputs_dir = self.data_dir / "outputs"
        self.metadata_file = self.data_dir / "output_metadata.json"
        
        # Create directories
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing metadata
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load output metadata from file"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Warning: Could not load metadata: {e}")
        
        return {"outputs": [], "statistics": {}}
    
    def _save_metadata(self):
        """Save metadata to file"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Warning: Could not save metadata: {e}")
    
    def create_output_structure(self, source_image_path: str, prompt: str, 
                              model: str, **parameters) -> Dict[str, str]:
        """Create organized output structure next to source image"""
        try:
            source_path = Path(source_image_path)
            source_dir = source_path.parent
            source_name = source_path.stem
            
            # Create timestamp for uniqueness
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create output folder next to source image
            output_folder_name = f"{source_name}_fal_output_{timestamp}"
            output_dir = source_dir / output_folder_name
            output_dir.mkdir(exist_ok=True)
            
            # Alternative: Create in central outputs directory if source dir not writable
            if not os.access(source_dir, os.W_OK):
                output_dir = self.outputs_dir / output_folder_name
                output_dir.mkdir(exist_ok=True)
            
            # Create subdirectories
            video_dir = output_dir / "videos"
            metadata_dir = output_dir / "metadata"
            thumbnails_dir = output_dir / "thumbnails"
            
            video_dir.mkdir(exist_ok=True)
            metadata_dir.mkdir(exist_ok=True)
            thumbnails_dir.mkdir(exist_ok=True)
            
            # Generate output filenames
            base_filename = f"{source_name}_{model}_{timestamp}"
            
            paths = {
                "output_dir": str(output_dir),
                "video_dir": str(video_dir),
                "metadata_dir": str(metadata_dir),
                "thumbnails_dir": str(thumbnails_dir),
                "video_filename": f"{base_filename}.mp4",
                "metadata_filename": f"{base_filename}_metadata.json",
                "prompt_filename": f"{base_filename}_prompt.txt",
                "thumbnail_filename": f"{base_filename}_thumb.jpg"
            }
            
            # Create metadata file immediately
            self._create_generation_metadata(
                paths["metadata_dir"], 
                paths["metadata_filename"],
                source_image_path, prompt, model, parameters
            )
            
            # Save prompt to text file
            prompt_file = Path(paths["metadata_dir"]) / paths["prompt_filename"]
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            return paths
            
        except Exception as e:
            print(f"❌ Error creating output structure: {e}")
            # Fallback to simple filename in current directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fallback_name = f"fal_output_{timestamp}"
            
            return {
                "output_dir": str(Path.cwd()),
                "video_dir": str(Path.cwd()),
                "metadata_dir": str(Path.cwd()),
                "thumbnails_dir": str(Path.cwd()),
                "video_filename": f"{fallback_name}.mp4",
                "metadata_filename": f"{fallback_name}_metadata.json",
                "prompt_filename": f"{fallback_name}_prompt.txt",
                "thumbnail_filename": f"{fallback_name}_thumb.jpg"
            }
    
    def _create_generation_metadata(self, metadata_dir: str, filename: str,
                                  source_image: str, prompt: str, model: str,
                                  parameters: Dict[str, Any]):
        """Create detailed metadata file for the generation"""
        metadata = {
            "generation_info": {
                "timestamp": datetime.now().isoformat(),
                "source_image": source_image,
                "prompt": prompt,
                "model": model,
                "parameters": parameters
            },
            "file_info": {
                "created_by": "FAL.AI Video Generator - Unified Launcher",
                "version": "3.0",
                "generator_config": {
                    "cli_version": "enhanced",
                    "features": ["file_picker", "prompt_manager", "smart_output"]
                }
            },
            "cost_info": {
                "estimated_cost": self._estimate_cost(model, parameters.get("duration", 5)),
                "model_pricing": self._get_model_pricing(model)
            }
        }
        
        metadata_path = Path(metadata_dir) / filename
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Warning: Could not save generation metadata: {e}")
    
    def _estimate_cost(self, model: str, duration: int) -> float:
        """Estimate generation cost"""
        # Default pricing (should be loaded from config)
        pricing = {
            "kling_21_standard": 0.05,
            "kling_21_pro": 0.09,
            "kling_21_master": 0.28,
            "kling_16_pro": 0.095,
            "luma_dream": 0.10,
            "haiper_20": 0.04
        }
        
        cost_per_second = pricing.get(model, 0.05)
        return cost_per_second * duration
    
    def _get_model_pricing(self, model: str) -> Dict[str, float]:
        """Get model pricing information"""
        return {
            "cost_per_second": self._estimate_cost(model, 1),
            "cost_5s": self._estimate_cost(model, 5),
            "cost_10s": self._estimate_cost(model, 10)
        }
    
    def save_generation_result(self, output_paths: Dict[str, str], 
                             result: Dict[str, Any], 
                             success: bool = True) -> Optional[str]:
        """Save generation result and update metadata"""
        try:
            generation_id = self._generate_id(output_paths["video_filename"])
            
            # Extract video URL and download if possible
            video_url = None
            local_video_path = None
            
            if success and isinstance(result, dict):
                # Handle different result formats
                if "video" in result:
                    video_info = result["video"]
                    if isinstance(video_info, dict) and "url" in video_info:
                        video_url = video_info["url"]
                    elif isinstance(video_info, str):
                        video_url = video_info
                elif "url" in result:
                    video_url = result["url"]
                
                # Try to download video
                if video_url:
                    local_video_path = self._download_video(
                        video_url, 
                        output_paths["video_dir"], 
                        output_paths["video_filename"]
                    )
            
            # Update generation metadata with result
            result_metadata = {
                "generation_id": generation_id,
                "success": success,
                "result": result,
                "video_url": video_url,
                "local_video_path": local_video_path,
                "completion_time": datetime.now().isoformat(),
                "output_paths": output_paths
            }
            
            # Save result metadata
            result_file = Path(output_paths["metadata_dir"]) / "generation_result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_metadata, f, indent=2, ensure_ascii=False)
            
            # Add to global metadata
            self.metadata["outputs"].append(result_metadata)
            self._update_statistics(success, result_metadata)
            self._save_metadata()
            
            print(f"✅ Output saved to: {output_paths['output_dir']}")
            if local_video_path:
                print(f"📹 Video downloaded: {local_video_path}")
            
            return local_video_path or video_url
            
        except Exception as e:
            print(f"⚠️ Warning: Could not save generation result: {e}")
            return None
    
    def _generate_id(self, filename: str) -> str:
        """Generate unique ID for generation"""
        timestamp = datetime.now().isoformat()
        content = f"{filename}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _download_video(self, url: str, video_dir: str, filename: str) -> Optional[str]:
        """Download video from URL"""
        try:
            import requests
            from urllib.parse import urlparse
            
            # Parse URL to get file extension if not .mp4
            parsed_url = urlparse(url)
            url_path = Path(parsed_url.path)
            if url_path.suffix and url_path.suffix != '.mp4':
                # Use original extension
                filename = Path(filename).with_suffix(url_path.suffix).name
            
            output_path = Path(video_dir) / filename
            
            print(f"📥 Downloading video...")
            
            # Download with progress indication
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r📥 Downloading... {progress:.1f}%", end='', flush=True)
            
            print(f"\n✅ Video downloaded successfully")
            return str(output_path)
            
        except Exception as e:
            print(f"⚠️ Warning: Could not download video: {e}")
            print(f"📋 Video URL: {url}")
            return None
    
    def _update_statistics(self, success: bool, metadata: Dict[str, Any]):
        """Update generation statistics"""
        stats = self.metadata.setdefault("statistics", {})
        
        # Basic counts
        stats["total_generations"] = stats.get("total_generations", 0) + 1
        if success:
            stats["successful_generations"] = stats.get("successful_generations", 0) + 1
        
        # Model usage
        model_stats = stats.setdefault("model_usage", {})
        if "result" in metadata and "model" in str(metadata):
            # Extract model from metadata (this could be improved)
            for model_key in ["kling_21_pro", "kling_21_standard", "kling_21_master", "kling_16_pro", "luma_dream", "haiper_20"]:
                if model_key in str(metadata):
                    model_stats[model_key] = model_stats.get(model_key, 0) + 1
                    break
        
        # Cost tracking
        if "cost_info" in metadata.get("result", {}):
            total_cost = stats.get("total_estimated_cost", 0.0)
            estimated_cost = metadata["result"]["cost_info"].get("estimated_cost", 0.0)
            stats["total_estimated_cost"] = total_cost + estimated_cost
        
        # Success rate
        if stats["total_generations"] > 0:
            stats["success_rate"] = (stats.get("successful_generations", 0) / stats["total_generations"]) * 100
    
    def get_recent_outputs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent generation outputs"""
        outputs = self.metadata.get("outputs", [])
        return sorted(outputs, key=lambda x: x.get("completion_time", ""), reverse=True)[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get generation statistics"""
        return self.metadata.get("statistics", {})
    
    def cleanup_old_outputs(self, days: int = 30, dry_run: bool = True) -> Dict[str, Any]:
        """Clean up old output files"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        outputs = self.metadata.get("outputs", [])
        
        cleanup_stats = {
            "files_found": 0,
            "files_cleaned": 0,
            "space_freed": 0,
            "errors": []
        }
        
        files_to_clean = []
        
        for output in outputs:
            try:
                completion_time = output.get("completion_time")
                if not completion_time:
                    continue
                
                output_time = datetime.fromisoformat(completion_time)
                if output_time < cutoff_date:
                    output_dir = output.get("output_paths", {}).get("output_dir")
                    if output_dir and Path(output_dir).exists():
                        files_to_clean.append((output, output_dir))
                        cleanup_stats["files_found"] += 1
            except Exception as e:
                cleanup_stats["errors"].append(f"Error processing output: {e}")
        
        if dry_run:
            print(f"🧹 Cleanup Preview (--dry-run):")
            print(f"Found {cleanup_stats['files_found']} output directories older than {days} days")
            
            for output, output_dir in files_to_clean[:5]:  # Show first 5
                dir_size = self._get_directory_size(output_dir)
                print(f"  📁 {output_dir} ({dir_size / (1024*1024):.1f} MB)")
            
            if len(files_to_clean) > 5:
                print(f"  ... and {len(files_to_clean) - 5} more directories")
            
        else:
            print(f"🧹 Cleaning up {cleanup_stats['files_found']} old output directories...")
            
            for output, output_dir in files_to_clean:
                try:
                    dir_size = self._get_directory_size(output_dir)
                    shutil.rmtree(output_dir)
                    cleanup_stats["files_cleaned"] += 1
                    cleanup_stats["space_freed"] += dir_size
                    print(f"  ✅ Removed: {output_dir}")
                except Exception as e:
                    cleanup_stats["errors"].append(f"Error removing {output_dir}: {e}")
            
            # Update metadata to remove cleaned outputs
            self.metadata["outputs"] = [
                output for output in outputs
                if not any(output is cleaned_output for cleaned_output, _ in files_to_clean)
            ]
            self._save_metadata()
        
        return cleanup_stats
    
    def _get_directory_size(self, directory: str) -> int:
        """Get total size of directory in bytes"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            return total_size
        except Exception:
            return 0
    
    def organize_by_date(self, source_dir: Optional[str] = None) -> Dict[str, Any]:
        """Organize existing outputs by date"""
        if not source_dir:
            source_dir = str(self.outputs_dir)
        
        source_path = Path(source_dir)
        if not source_path.exists():
            return {"error": "Source directory does not exist"}
        
        organization_stats = {
            "files_processed": 0,
            "files_organized": 0,
            "directories_created": 0,
            "errors": []
        }
        
        try:
            # Create date-based directory structure
            for item in source_path.iterdir():
                if item.is_dir() and "fal_output" in item.name:
                    try:
                        # Extract timestamp from directory name
                        parts = item.name.split("_")
                        timestamp_part = None
                        
                        for part in parts:
                            if len(part) == 15 and part.isdigit():  # YYYYMMDD_HHMMSS format
                                timestamp_part = part
                                break
                        
                        if timestamp_part:
                            # Parse date
                            date_str = timestamp_part[:8]  # YYYYMMDD
                            year = date_str[:4]
                            month = date_str[4:6]
                            day = date_str[6:8]
                            
                            # Create date directory structure
                            date_dir = source_path / year / f"{year}-{month}" / f"{year}-{month}-{day}"
                            date_dir.mkdir(parents=True, exist_ok=True)
                            
                            if not (date_dir / item.name).exists():
                                organization_stats["directories_created"] += 1
                            
                            # Move directory
                            new_location = date_dir / item.name
                            if not new_location.exists():
                                shutil.move(str(item), str(new_location))
                                organization_stats["files_organized"] += 1
                        
                        organization_stats["files_processed"] += 1
                        
                    except Exception as e:
                        organization_stats["errors"].append(f"Error organizing {item.name}: {e}")
            
        except Exception as e:
            organization_stats["errors"].append(f"Error during organization: {e}")
        
        return organization_stats
    
    def create_output_index(self, output_dir: Optional[str] = None) -> str:
        """Create an HTML index of all outputs"""
        if not output_dir:
            output_dir = str(self.outputs_dir)
        
        output_path = Path(output_dir)
        index_file = output_path / "index.html"
        
        outputs = self.get_recent_outputs(100)  # Get more for full index
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FAL.AI Video Generator - Output Index</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #333; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .stats {{ background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .output-item {{ background: white; padding: 15px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .success {{ border-left: 4px solid #4CAF50; }}
        .failed {{ border-left: 4px solid #f44336; }}
        .prompt {{ font-style: italic; color: #666; margin: 10px 0; }}
        .metadata {{ font-size: 0.9em; color: #888; }}
        .video-link {{ color: #1976D2; text-decoration: none; }}
        .video-link:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎬 FAL.AI Video Generator - Output Index</h1>
        <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </div>
    
    <div class="stats">
        <h2>📊 Statistics</h2>
        <p><strong>Total Outputs:</strong> {len(outputs)}</p>
        <p><strong>Success Rate:</strong> {self.get_statistics().get('success_rate', 0):.1f}%</p>
        <p><strong>Total Estimated Cost:</strong> ${self.get_statistics().get('total_estimated_cost', 0):.2f}</p>
    </div>
    
    <div class="outputs">
        <h2>📹 Recent Outputs</h2>
"""
        
        for output in outputs:
            success_class = "success" if output.get("success", False) else "failed"
            completion_time = output.get("completion_time", "Unknown")
            
            try:
                formatted_time = datetime.fromisoformat(completion_time).strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_time = completion_time
            
            video_url = output.get("video_url", "")
            local_path = output.get("local_video_path", "")
            
            video_link = ""
            if local_path and Path(local_path).exists():
                video_link = f'<a href="{local_path}" class="video-link">📁 Local Video</a>'
            elif video_url:
                video_link = f'<a href="{video_url}" class="video-link">🔗 Video URL</a>'
            
            result_info = output.get("result", {})
            prompt = "No prompt available"
            
            # Try to extract prompt from various locations
            if "prompt" in result_info:
                prompt = result_info["prompt"]
            elif "output_paths" in output:
                # Try to read prompt from file
                prompt_file = Path(output["output_paths"].get("metadata_dir", "")) / output["output_paths"].get("prompt_filename", "")
                if prompt_file.exists():
                    try:
                        prompt = prompt_file.read_text(encoding='utf-8')
                    except:
                        pass
            
            html_content += f"""
        <div class="output-item {success_class}">
            <h3>Generation {output.get('generation_id', 'Unknown')}</h3>
            <div class="prompt">"{prompt[:200]}{'...' if len(prompt) > 200 else ''}"</div>
            <div class="metadata">
                <strong>Time:</strong> {formatted_time}<br>
                <strong>Status:</strong> {'✅ Success' if output.get('success', False) else '❌ Failed'}<br>
                {video_link}
            </div>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"📄 Output index created: {index_file}")
            return str(index_file)
            
        except Exception as e:
            print(f"❌ Error creating output index: {e}")
            return ""

# Convenience functions
def create_output_structure(source_image_path: str, prompt: str, model: str, **parameters) -> Dict[str, str]:
    """Create organized output structure"""
    organizer = OutputOrganizer()
    return organizer.create_output_structure(source_image_path, prompt, model, **parameters)

def save_generation_result(output_paths: Dict[str, str], result: Dict[str, Any], success: bool = True) -> Optional[str]:
    """Save generation result"""
    organizer = OutputOrganizer()
    return organizer.save_generation_result(output_paths, result, success)

# Test function
if __name__ == "__main__":
    print("Testing Output Organizer...")
    
    organizer = OutputOrganizer()
    
    # Test creating output structure
    test_paths = organizer.create_output_structure(
        "test_image.jpg",
        "Test prompt for video generation",
        "kling_21_pro",
        duration=5,
        aspect_ratio="16:9"
    )
    
    print(f"Created output structure: {test_paths}")
    
    # Test statistics
    stats = organizer.get_statistics()
    print(f"Statistics: {stats}")
    
    print("Output Organizer test completed.")