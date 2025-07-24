#!/usr/bin/env python3
"""
FAL.AI Video Generator - Main Application
Unified interface for FAL.AI video generation services
"""

import asyncio
import json
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import fal_client
import click
from colorama import init, Fore, Style
from security import security_manager, InputValidator

# Initialize colorama for Windows compatibility
init()

# ========================================================================
#                              Configuration                               
# ========================================================================

class Config:
    def __init__(self, config_path: str = "./config/settings.json"):
        self.config_path = Path(config_path)
        self.settings = self._load_config()
        self._setup_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if not self.config_path.exists():
            return self._create_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"{Fore.RED}Error loading config: {e}{Style.RESET_ALL}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        default_config = {
            "fal_api_key": "",
            "default_model": "fal-ai/kling-video/v1/pro/image-to-video",
            "output_directory": "./data/outputs",
            "log_level": "INFO",
            "max_duration": 10,
            "default_aspect_ratio": "9:16",
            "models": {
                "kling_21_master": {
                    "endpoint": "fal-ai/kling-video/v2.1/master/image-to-video",
                    "name": "Kling 2.1 Master",
                    "description": "Unparalleled motion fluidity, cinematic visuals, exceptional prompt precision",
                    "tier": "Premium",
                    "cost_5s": 1.40,
                    "cost_10s": 2.80,
                    "cost_per_second": 0.28,
                    "max_duration": 10,
                    "quality": "Premium",
                    "best_for": "Professional filmmaking, high-end content creation"
                },
                "kling_21_pro": {
                    "endpoint": "fal-ai/kling-video/v2.1/pro/image-to-video",
                    "name": "Kling 2.1 Pro",
                    "description": "Enhanced visual fidelity, precise camera movements, dynamic motion control",
                    "tier": "Professional",
                    "cost_5s": 0.45,
                    "cost_10s": 0.90,
                    "cost_per_second": 0.09,
                    "max_duration": 10,
                    "quality": "High",
                    "best_for": "Professional content creation, marketing videos"
                },
                "kling_21_standard": {
                    "endpoint": "fal-ai/kling-video/v2.1/standard/image-to-video",
                    "name": "Kling 2.1 Standard",
                    "description": "High-quality generation at cost-efficient pricing",
                    "tier": "Standard",
                    "cost_5s": 0.25,
                    "cost_10s": 0.50,
                    "cost_per_second": 0.05,
                    "max_duration": 10,
                    "quality": "Standard",
                    "best_for": "General content creation, budget-conscious projects"
                },
                "kling_20_master": {
                    "endpoint": "fal-ai/kling-video/v2/master/image-to-video",
                    "name": "Kling 2.0 Master",
                    "description": "Legacy premium model with excellent quality",
                    "tier": "Legacy Premium",
                    "cost_5s": 1.40,
                    "cost_10s": 2.80,
                    "cost_per_second": 0.28,
                    "max_duration": 10,
                    "quality": "High",
                    "best_for": "Users who don't need latest 2.1 features"
                },
                "kling_16_pro": {
                    "endpoint": "fal-ai/kling-video/v1.6/pro/image-to-video",
                    "name": "Kling 1.6 Pro",
                    "description": "Advanced async generation with good quality",
                    "tier": "Legacy",
                    "cost_5s": 0.475,
                    "cost_10s": 0.95,
                    "cost_per_second": 0.095,
                    "max_duration": 10,
                    "quality": "Good",
                    "best_for": "Testing and legacy projects"
                },
                "luma_dream": {
                    "endpoint": "fal-ai/luma-dream-machine",
                    "name": "Luma Dream Machine",
                    "description": "High-quality alternative with competitive pricing",
                    "tier": "Alternative",
                    "cost_5s": 0.50,
                    "cost_10s": 0.90,
                    "cost_per_second": 0.10,
                    "max_duration": 9,
                    "quality": "High",
                    "best_for": "Quick generation, alternative to Kling"
                },
                "haiper_20": {
                    "endpoint": "fal-ai/haiper-video-v2/image-to-video",
                    "name": "Haiper 2.0",
                    "description": "Affordable video generation with good results",
                    "tier": "Budget",
                    "cost_5s": 0.20,
                    "cost_10s": 0.40,
                    "cost_per_second": 0.04,
                    "max_duration": 10,
                    "quality": "Good",
                    "best_for": "Budget-friendly video generation"
                },
                "workflow": "workflows/dedkamaroz/image-to-video"
            }
        }
        
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save default config
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"fal_ai_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=getattr(logging, self.settings.get("log_level", "INFO")),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.settings.get(key, default)
    
    def set_api_key(self):
        """Set FAL API key securely"""
        try:
            api_key = security_manager.get_secure_api_key()
            os.environ["FAL_KEY"] = api_key
            print(f"{Fore.GREEN}✅ API key configured securely{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to configure API key: {e}{Style.RESET_ALL}")
            return False

# ========================================================================
#                            Video Generators                             
# ========================================================================

class VideoGenerator:
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Ensure output directory exists
        output_dir = Path(config.get("output_directory", "./data/outputs"))
        output_dir.mkdir(parents=True, exist_ok=True)
    
    def upload_file(self, file_path: str) -> str:
        """Upload file to FAL and return URL"""
        try:
            self.logger.info(f"Uploading file: {file_path}")
            url = fal_client.upload_file(file_path)
            self.logger.info(f"File uploaded successfully: {url}")
            return url
        except Exception as e:
            self.logger.error(f"Failed to upload file: {e}")
            raise
    
    def on_queue_update(self, update):
        """Handle queue updates with progress"""
        if isinstance(update, fal_client.InProgress):
            for log_entry in update.logs:
                print(f"{Fore.CYAN}[Progress] {log_entry['message']}{Style.RESET_ALL}")
    
    async def generate_kling_pro(self, image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate video using Kling Pro model with security validation"""
        try:
            print(f"{Fore.GREEN}🎬 Starting Kling Pro generation...{Style.RESET_ALL}")
            
            # Validate and sanitize all inputs
            validated_inputs = security_manager.validate_and_sanitize_inputs(
                image_path=image_path,
                prompt=prompt,
                duration=kwargs.get("duration", self.config.get("max_duration", 10)),
                aspect_ratio=kwargs.get("aspect_ratio", self.config.get("default_aspect_ratio", "9:16")),
                **{k: v for k, v in kwargs.items() if k in ["tail_image_path", "negative_prompt", "cfg_scale"]}
            )
            
            print(f"{Fore.CYAN}✅ Input validation passed{Style.RESET_ALL}")
            
            # Upload image
            image_url = self.upload_file(validated_inputs["image_path"])
            
            # Prepare arguments
            arguments = {
                "prompt": validated_inputs["prompt"],
                "image_url": image_url,
                "duration": validated_inputs["duration"],
                "aspect_ratio": validated_inputs["aspect_ratio"]
            }
            
            # Add optional tail image
            if "tail_image_path" in validated_inputs:
                tail_url = self.upload_file(validated_inputs["tail_image_path"])
                arguments["tail_image_url"] = tail_url
            
            # Add optional parameters
            if "negative_prompt" in validated_inputs:
                arguments["negative_prompt"] = validated_inputs["negative_prompt"]
            if "cfg_scale" in validated_inputs:
                arguments["cfg_scale"] = validated_inputs["cfg_scale"]
            
            self.logger.info(f"Submitting job with arguments: {arguments}")
            
            # Submit job
            result = fal_client.subscribe(
                self.config.get("models", {}).get("kling_pro", "fal-ai/kling-video/v1/pro/image-to-video"),
                arguments=arguments,
                with_logs=True,
                on_queue_update=self.on_queue_update,
            )
            
            self.logger.info(f"Generation completed: {result}")
            print(f"{Fore.GREEN}✅ Video generation completed!{Style.RESET_ALL}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Kling Pro generation failed: {e}")
            print(f"{Fore.RED}❌ Generation failed: {e}{Style.RESET_ALL}")
            raise
    
    async def generate_kling_v16(self, image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate video using Kling v1.6 model with async support"""
        try:
            print(f"{Fore.GREEN}🎬 Starting Kling v1.6 generation...{Style.RESET_ALL}")
            
            # Upload images
            start_url = self.upload_file(image_path)
            
            # Prepare arguments
            arguments = {
                "prompt": prompt,
                "image_url": start_url,
                "duration": str(kwargs.get("duration", 5)),
                "aspect_ratio": kwargs.get("aspect_ratio", "9:16")
            }
            
            # Add optional parameters
            if "tail_image_path" in kwargs:
                tail_url = self.upload_file(kwargs["tail_image_path"])
                arguments["tail_image_url"] = tail_url
            
            if "negative_prompt" in kwargs:
                arguments["negative_prompt"] = kwargs["negative_prompt"]
            if "cfg_scale" in kwargs:
                arguments["cfg_scale"] = kwargs["cfg_scale"]
            
            self.logger.info(f"Submitting async job with arguments: {arguments}")
            
            # Submit async job
            handler = await fal_client.submit_async(
                self.config.get("models", {}).get("kling_v16", "fal-ai/kling-video/v1.6/pro/image-to-video"),
                arguments=arguments,
            )
            
            # Monitor progress
            async for event in handler.iter_events(with_logs=True):
                print(f"{Fore.CYAN}[Event] {event}{Style.RESET_ALL}")
            
            # Get final result
            result = await handler.get()
            
            self.logger.info(f"Generation completed: {result}")
            print(f"{Fore.GREEN}✅ Video generation completed!{Style.RESET_ALL}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Kling v1.6 generation failed: {e}")
            print(f"{Fore.RED}❌ Generation failed: {e}{Style.RESET_ALL}")
            raise
    
    async def generate_kling_21_standard(self, image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate video using Kling 2.1 Standard model"""
        try:
            print(f"{Fore.GREEN}🎬 Starting Kling 2.1 Standard generation...{Style.RESET_ALL}")
            
            # Upload image
            image_url = self.upload_file(image_path)
            
            # Prepare arguments
            arguments = {
                "prompt": prompt,
                "image_url": image_url,
                "duration": str(kwargs.get("duration", 5)),
                "aspect_ratio": kwargs.get("aspect_ratio", self.config.get("default_aspect_ratio", "16:9"))
            }
            
            # Add optional parameters
            if "negative_prompt" in kwargs:
                arguments["negative_prompt"] = kwargs["negative_prompt"]
            if "cfg_scale" in kwargs:
                arguments["cfg_scale"] = kwargs["cfg_scale"]
            
            self.logger.info(f"Submitting Kling 2.1 Standard job with arguments: {arguments}")
            
            # Submit job
            result = fal_client.subscribe(
                self.config.get("models", {}).get("kling_21_standard", "fal-ai/kling-video/v2.1/standard/image-to-video"),
                arguments=arguments,
                with_logs=True,
                on_queue_update=self.on_queue_update,
            )
            
            self.logger.info(f"Generation completed: {result}")
            print(f"{Fore.GREEN}✅ Video generation completed!{Style.RESET_ALL}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Kling 2.1 Standard generation failed: {e}")
            print(f"{Fore.RED}❌ Generation failed: {e}{Style.RESET_ALL}")
            raise
    
    async def generate_kling_21_pro(self, image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate video using Kling 2.1 Pro model"""
        try:
            print(f"{Fore.GREEN}🎬 Starting Kling 2.1 Pro generation...{Style.RESET_ALL}")
            
            # Upload image
            image_url = self.upload_file(image_path)
            
            # Prepare arguments
            arguments = {
                "prompt": prompt,
                "image_url": image_url,
                "duration": str(kwargs.get("duration", 5)),
                "aspect_ratio": kwargs.get("aspect_ratio", self.config.get("default_aspect_ratio", "16:9"))
            }
            
            # Add optional parameters
            if "negative_prompt" in kwargs:
                arguments["negative_prompt"] = kwargs["negative_prompt"]
            if "cfg_scale" in kwargs:
                arguments["cfg_scale"] = kwargs["cfg_scale"]
            
            self.logger.info(f"Submitting Kling 2.1 Pro job with arguments: {arguments}")
            
            # Submit job
            result = fal_client.subscribe(
                self.config.get("models", {}).get("kling_21_pro", "fal-ai/kling-video/v2.1/pro/image-to-video"),
                arguments=arguments,
                with_logs=True,
                on_queue_update=self.on_queue_update,
            )
            
            self.logger.info(f"Generation completed: {result}")
            print(f"{Fore.GREEN}✅ Video generation completed!{Style.RESET_ALL}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Kling 2.1 Pro generation failed: {e}")
            print(f"{Fore.RED}❌ Generation failed: {e}{Style.RESET_ALL}")
            raise
    
    async def generate_kling_21_master(self, image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate video using Kling 2.1 Master model"""
        try:
            print(f"{Fore.GREEN}🎬 Starting Kling 2.1 Master generation...{Style.RESET_ALL}")
            
            # Upload image
            image_url = self.upload_file(image_path)
            
            # Prepare arguments
            arguments = {
                "prompt": prompt,
                "image_url": image_url,
                "duration": str(kwargs.get("duration", 5)),
                "aspect_ratio": kwargs.get("aspect_ratio", self.config.get("default_aspect_ratio", "16:9"))
            }
            
            # Add optional parameters
            if "negative_prompt" in kwargs:
                arguments["negative_prompt"] = kwargs["negative_prompt"]
            if "cfg_scale" in kwargs:
                arguments["cfg_scale"] = kwargs["cfg_scale"]
            
            self.logger.info(f"Submitting Kling 2.1 Master job with arguments: {arguments}")
            
            # Submit job
            result = fal_client.subscribe(
                self.config.get("models", {}).get("kling_21_master", "fal-ai/kling-video/v2.1/master/image-to-video"),
                arguments=arguments,
                with_logs=True,
                on_queue_update=self.on_queue_update,
            )
            
            self.logger.info(f"Generation completed: {result}")
            print(f"{Fore.GREEN}✅ Video generation completed!{Style.RESET_ALL}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Kling 2.1 Master generation failed: {e}")
            print(f"{Fore.RED}❌ Generation failed: {e}{Style.RESET_ALL}")
            raise

    async def run_workflow(self, **kwargs) -> Dict[str, Any]:
        """Run custom workflow"""
        try:
            print(f"{Fore.GREEN}🔄 Starting custom workflow...{Style.RESET_ALL}")
            
            arguments = kwargs.get("arguments", {})
            
            stream = fal_client.stream_async(
                self.config.get("models", {}).get("workflow", "workflows/dedkamaroz/image-to-video"),
                arguments=arguments,
            )
            
            results = []
            event_count = 0
            max_events = 50  # Prevent infinite loop
            
            async for event in stream:
                print(f"{Fore.CYAN}[Workflow Event {event_count + 1}] {event}{Style.RESET_ALL}")
                results.append(event)
                event_count += 1
                
                # Break if we get too many events or a completion event
                if event_count >= max_events:
                    print(f"{Fore.YELLOW}⚠️ Maximum events reached, stopping workflow...{Style.RESET_ALL}")
                    break
                
                # Check for completion indicators
                if isinstance(event, dict) and any(key in str(event).lower() for key in ['complete', 'finished', 'done', 'success']):
                    print(f"{Fore.GREEN}✅ Workflow completion detected!{Style.RESET_ALL}")
                    break
                
                # Add timeout for each event
                await asyncio.sleep(0.1)
            
            print(f"{Fore.GREEN}✅ Workflow completed with {event_count} events!{Style.RESET_ALL}")
            return {"events": results, "total_events": event_count}
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            print(f"{Fore.RED}❌ Workflow failed: {e}{Style.RESET_ALL}")
            raise
    
    async def generate_video(self, endpoint: str, image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Universal video generation method for any endpoint"""
        try:
            print(f"{Fore.GREEN}🎬 Starting video generation with {endpoint}...{Style.RESET_ALL}")
            
            # Upload image
            image_url = self.upload_file(image_path)
            
            # Prepare arguments
            arguments = {
                "prompt": prompt,
                "image_url": image_url,
                "duration": str(kwargs.get("duration", 5)),
                "aspect_ratio": kwargs.get("aspect_ratio", self.config.get("default_aspect_ratio", "16:9"))
            }
            
            # Add optional parameters
            if "negative_prompt" in kwargs:
                arguments["negative_prompt"] = kwargs["negative_prompt"]
            if "cfg_scale" in kwargs:
                arguments["cfg_scale"] = kwargs["cfg_scale"]
            if "tail_image_path" in kwargs:
                tail_image_url = self.upload_file(kwargs["tail_image_path"])
                arguments["tail_image_url"] = tail_image_url
            
            self.logger.info(f"Submitting job to {endpoint} with arguments: {arguments}")
            
            # Submit async job
            handler = await fal_client.submit_async(
                endpoint,
                arguments=arguments,
            )
            
            # Monitor progress
            async for event in handler.iter_events(with_logs=True):
                print(f"{Fore.CYAN}[Event] {event}{Style.RESET_ALL}")
            
            # Get final result
            result = await handler.get()
            
            self.logger.info(f"Generation completed: {result}")
            print(f"{Fore.GREEN}✅ Video generation completed!{Style.RESET_ALL}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Video generation failed for {endpoint}: {e}")
            print(f"{Fore.RED}❌ Generation failed: {e}{Style.RESET_ALL}")
            raise

# ========================================================================
#                            Interactive CLI                              
# ========================================================================

class InteractiveCLI:
    def __init__(self, generator: VideoGenerator):
        self.generator = generator
    
    def show_banner(self):
        """Display application banner"""
        banner = f"""
{Fore.MAGENTA}{'=' * 72}
                        FAL.AI Video Generator                        
                         Professional Interface                       
{'=' * 72}{Style.RESET_ALL}

{Fore.CYAN}Available modes:
  1. Kling Pro (v1.0) - Standard video generation
  2. Kling v1.6 - Advanced async generation
  3. Kling 2.1 Standard - Cost-efficient latest model ($0.25/5s)
  4. Kling 2.1 Pro - Professional grade ($0.45/5s)
  5. Kling 2.1 Master - Premium quality ($0.70/5s)
  6. Custom Workflow - Run predefined workflow
  7. Exit{Style.RESET_ALL}
"""
        print(banner)
    
    def get_file_path(self, prompt: str) -> Optional[str]:
        """Get and validate file path from user with security checks"""
        while True:
            try:
                path = input(f"{prompt}: ").strip()
                if not path:
                    return None
                
                # Use security validation
                validated_path = InputValidator.sanitize_file_path(path)
                if validated_path:
                    print(f"{Fore.GREEN}✅ File validated: {validated_path}{Style.RESET_ALL}")
                    return validated_path
                else:
                    print(f"{Fore.RED}❌ Invalid or unsafe file path. Please try again.{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Operation cancelled.{Style.RESET_ALL}")
                return None
            except Exception as e:
                print(f"{Fore.RED}❌ Error validating file: {e}{Style.RESET_ALL}")
    
    async def run_interactive(self):
        """Run interactive mode"""
        while True:
            self.show_banner()
            
            try:
                choice = input(f"\n{Fore.YELLOW}Choose mode (1-7): {Style.RESET_ALL}").strip()
                
                if choice == "7":
                    print(f"{Fore.GREEN}Goodbye!{Style.RESET_ALL}")
                    break
                
                elif choice in ["1", "2", "3", "4", "5"]:
                    # Get common inputs
                    image_path = self.get_file_path("Enter image path")
                    if not image_path:
                        continue
                    
                    while True:
                        raw_prompt = input("Enter prompt: ").strip()
                        if not raw_prompt:
                            print(f"{Fore.RED}Prompt is required{Style.RESET_ALL}")
                            continue
                        
                        # Validate prompt for security
                        prompt = InputValidator.sanitize_prompt(raw_prompt)
                        if prompt:
                            print(f"{Fore.GREEN}✅ Prompt validated{Style.RESET_ALL}")
                            break
                        else:
                            print(f"{Fore.RED}❌ Prompt contains unsafe content. Please modify and try again.{Style.RESET_ALL}")
                    
                    # Optional parameters with model-specific defaults
                    default_duration = 5 if choice in ["3", "4", "5"] else self.generator.config.get('max_duration', 10)
                    default_aspect = "16:9" if choice in ["3", "4", "5"] else self.generator.config.get('default_aspect_ratio', '9:16')
                    
                    duration = input(f"Duration (default: {default_duration}): ").strip()
                    if duration:
                        try:
                            duration = int(duration)
                        except ValueError:
                            duration = default_duration
                    else:
                        duration = default_duration
                    
                    aspect_ratio = input(f"Aspect ratio (default: {default_aspect}): ").strip()
                    if not aspect_ratio:
                        aspect_ratio = default_aspect
                    
                    # Advanced options for newer models
                    negative_prompt = None
                    cfg_scale = None
                    
                    if choice in ["3", "4", "5"]:
                        neg_input = input("Negative prompt (optional): ").strip()
                        if neg_input:
                            negative_prompt = neg_input
                        
                        cfg_input = input("CFG scale 0-1 (default: 0.5): ").strip()
                        if cfg_input:
                            try:
                                cfg_scale = float(cfg_input)
                                if not 0 <= cfg_scale <= 1:
                                    cfg_scale = 0.5
                            except ValueError:
                                cfg_scale = 0.5
                    
                    # Optional tail image for v1.6
                    tail_image_path = None
                    if choice == "2":
                        tail_input = input("Tail image path (optional): ").strip()
                        if tail_input and Path(tail_input).exists():
                            tail_image_path = tail_input
                    
                    kwargs = {
                        "duration": duration,
                        "aspect_ratio": aspect_ratio
                    }
                    
                    if tail_image_path:
                        kwargs["tail_image_path"] = tail_image_path
                    if negative_prompt:
                        kwargs["negative_prompt"] = negative_prompt
                    if cfg_scale is not None:
                        kwargs["cfg_scale"] = cfg_scale
                    
                    # Generate video based on choice
                    if choice == "1":
                        result = await self.generator.generate_kling_pro(image_path, prompt, **kwargs)
                    elif choice == "2":
                        result = await self.generator.generate_kling_v16(image_path, prompt, **kwargs)
                    elif choice == "3":
                        result = await self.generator.generate_kling_21_standard(image_path, prompt, **kwargs)
                    elif choice == "4":
                        result = await self.generator.generate_kling_21_pro(image_path, prompt, **kwargs)
                    elif choice == "5":
                        result = await self.generator.generate_kling_21_master(image_path, prompt, **kwargs)
                    
                    print(f"\n{Fore.GREEN}Result: {json.dumps(result, indent=2)}{Style.RESET_ALL}")
                
                elif choice == "6":
                    result = await self.generator.run_workflow()
                    print(f"\n{Fore.GREEN}Workflow Result: {json.dumps(result, indent=2)}{Style.RESET_ALL}")
                
                else:
                    print(f"{Fore.RED}Invalid choice. Please select 1-7.{Style.RESET_ALL}")
                
                input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Operation cancelled by user.{Style.RESET_ALL}")
            except Exception as e:
                print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
                input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

# ========================================================================
#                               Main Logic                                
# ========================================================================

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="FAL.AI Video Generator")
    parser.add_argument("--mode", choices=["kling", "kling16", "kling21std", "kling21pro", "kling21master", "workflow", "interactive"], 
                       default="interactive", help="Generation mode")
    parser.add_argument("--image", help="Input image path")
    parser.add_argument("--prompt", help="Generation prompt")
    parser.add_argument("--duration", type=int, help="Video duration")
    parser.add_argument("--aspect-ratio", help="Video aspect ratio")
    parser.add_argument("--config", default="./config/settings.json", 
                       help="Config file path")
    
    args = parser.parse_args()
    
    try:
        # Initialize configuration
        config = Config(args.config)
        
        # Set up API key
        if not config.set_api_key():
            sys.exit(1)
        
        # Initialize generator
        generator = VideoGenerator(config)
        
        if args.mode == "interactive":
            # Run interactive CLI
            cli = InteractiveCLI(generator)
            asyncio.run(cli.run_interactive())
        
        elif args.mode in ["kling", "kling16", "kling21std", "kling21pro", "kling21master"]:
            if not args.image or not args.prompt:
                print(f"{Fore.RED}Image and prompt required for {args.mode} mode{Style.RESET_ALL}")
                sys.exit(1)
            
            kwargs = {}
            if args.duration:
                kwargs["duration"] = args.duration
            if args.aspect_ratio:
                kwargs["aspect_ratio"] = args.aspect_ratio
            
            # Select the appropriate generation method
            if args.mode == "kling":
                result = asyncio.run(generator.generate_kling_pro(args.image, args.prompt, **kwargs))
            elif args.mode == "kling16":
                result = asyncio.run(generator.generate_kling_v16(args.image, args.prompt, **kwargs))
            elif args.mode == "kling21std":
                result = asyncio.run(generator.generate_kling_21_standard(args.image, args.prompt, **kwargs))
            elif args.mode == "kling21pro":
                result = asyncio.run(generator.generate_kling_21_pro(args.image, args.prompt, **kwargs))
            elif args.mode == "kling21master":
                result = asyncio.run(generator.generate_kling_21_master(args.image, args.prompt, **kwargs))
            
            print(json.dumps(result, indent=2))
        
        elif args.mode == "workflow":
            result = asyncio.run(generator.run_workflow())
            print(json.dumps(result, indent=2))
    
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Application terminated by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Application error: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()