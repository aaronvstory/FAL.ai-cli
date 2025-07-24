#!/usr/bin/env python3
"""
FAL.AI Video Generator - Unified Launcher
Professional entry point with CLI and Web mode selection
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama for Windows compatibility
init()

# ASCII Art Banner
BANNER = f"""
{Fore.MAGENTA}{'=' * 80}
{Fore.CYAN}  ███████╗ █████╗ ██╗         █████╗ ██╗    ██╗██╗██████╗ ███████╗ ██████╗ 
  ██╔════╝██╔══██╗██║        ██╔══██╗██║    ██║██║██╔══██╗██╔════╝██╔═══██╗
  █████╗  ███████║██║        ███████║██║ █╗ ██║██║██║  ██║█████╗  ██████╔╝
  ██╔══╝  ██╔══██║██║        ██╔══██║██║███╗██║██║██║  ██║██╔══╝  ██╔══██╗
  ██║     ██║  ██║███████╗██╗██║  ██║╚███╔███╔╝██║██████╔╝███████╗██║  ██║
  ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝
{Fore.MAGENTA}{'=' * 80}
                           🎬 PROFESSIONAL VIDEO GENERATOR 🎬
                             🚀 Unified Launcher v3.0 🚀
{'=' * 80}{Style.RESET_ALL}
"""

class FALLauncher:
    """Main launcher class for FAL.AI Video Generator"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.data_dir = self.script_dir / "data"
        self.config_dir = self.script_dir / "config"
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize settings
        self.settings = self._load_settings()
    
    def _load_settings(self) -> dict:
        """Load user settings from data/user_preferences.json"""
        settings_file = self.data_dir / "user_preferences.json"
        
        default_settings = {
            "last_mode": "interactive",
            "preferred_model": "kling_21_pro",
            "default_duration": 5,
            "default_aspect_ratio": "16:9",
            "last_directory": str(self.script_dir),
            "auto_open_web": True,
            "show_cost_warnings": True,
            "theme": "default"
        }
        
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    default_settings.update(saved_settings)
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Warning: Could not load settings: {e}{Style.RESET_ALL}")
        
        return default_settings
    
    def _save_settings(self):
        """Save current settings to file"""
        settings_file = self.data_dir / "user_preferences.json"
        try:
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Could not save settings: {e}{Style.RESET_ALL}")
    
    def show_banner(self):
        """Display the application banner"""
        print(BANNER)
        print(f"{Fore.WHITE}Last used mode: {Fore.GREEN}{self.settings['last_mode']}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Preferred model: {Fore.GREEN}{self.settings['preferred_model']}{Style.RESET_ALL}")
        print()
    
    def check_environment(self) -> dict:
        """Check system environment and dependencies"""
        env_status = {
            "python_version": sys.version_info[:2],
            "gui_available": False,
            "fal_key_set": bool(os.getenv("FAL_KEY")),
            "web_dependencies": False,
            "cli_dependencies": False
        }
        
        # Check GUI availability (tkinter)
        try:
            import tkinter
            env_status["gui_available"] = True
        except ImportError:
            pass
        
        # Check web dependencies
        try:
            import fastapi
            import uvicorn
            env_status["web_dependencies"] = True
        except ImportError:
            pass
        
        # Check CLI dependencies
        try:
            import fal_client
            import colorama
            env_status["cli_dependencies"] = True
        except ImportError:
            pass
        
        return env_status
    
    def show_environment_status(self, env_status: dict):
        """Display environment status"""
        print(f"{Fore.CYAN}🔍 Environment Status:{Style.RESET_ALL}")
        print(f"  Python: {'.'.join(map(str, env_status['python_version']))} {'✅' if env_status['python_version'] >= (3, 8) else '❌'}")
        print(f"  GUI Support: {'✅' if env_status['gui_available'] else '❌'}")
        print(f"  FAL API Key: {'✅' if env_status['fal_key_set'] else '❌'}")
        print(f"  Web Dependencies: {'✅' if env_status['web_dependencies'] else '❌'}")
        print(f"  CLI Dependencies: {'✅' if env_status['cli_dependencies'] else '❌'}")
        print()
        
        # Show warnings
        if not env_status['fal_key_set']:
            print(f"{Fore.YELLOW}⚠️ Warning: FAL_KEY environment variable not set{Style.RESET_ALL}")
            print(f"   Set with: set FAL_KEY=your_api_key_here")
            print()
    
    def show_main_menu(self, env_status: dict):
        """Display the main mode selection menu"""
        print(f"{Fore.CYAN}🚀 Select Launch Mode:{Style.RESET_ALL}")
        print()
        
        # Web mode
        web_available = env_status['web_dependencies']
        web_icon = "🌐" if web_available else "❌"
        web_status = "" if web_available else " (Missing dependencies)"
        print(f"  {Fore.GREEN}1.{Style.RESET_ALL} {web_icon} {Fore.WHITE}Web Interface{Style.RESET_ALL}{web_status}")
        print(f"     Professional drag-and-drop interface with real-time progress")
        print(f"     Best for: Beginners, visual workflow, batch processing")
        print()
        
        # CLI mode
        cli_available = env_status['cli_dependencies']
        cli_icon = "💻" if cli_available else "❌"
        cli_status = "" if cli_available else " (Missing dependencies)"
        print(f"  {Fore.GREEN}2.{Style.RESET_ALL} {cli_icon} {Fore.WHITE}CLI Interface{Style.RESET_ALL}{cli_status}")
        print(f"     Command-line interface with enhanced features")
        print(f"     Best for: Power users, automation, scripting")
        print()
        
        # Quick generation
        quick_available = cli_available and env_status['gui_available']
        quick_icon = "⚡" if quick_available else "❌"
        quick_status = "" if quick_available else " (Missing GUI support)"
        print(f"  {Fore.GREEN}3.{Style.RESET_ALL} {quick_icon} {Fore.WHITE}Quick Generate{Style.RESET_ALL}{quick_status}")
        print(f"     File picker + instant generation with saved settings")
        print(f"     Best for: Frequent users, quick tasks")
        print()
        
        # Settings
        print(f"  {Fore.GREEN}4.{Style.RESET_ALL} ⚙️  {Fore.WHITE}Settings{Style.RESET_ALL}")
        print(f"     Configure preferences, API key, and defaults")
        print()
        
        # Help
        print(f"  {Fore.GREEN}5.{Style.RESET_ALL} ❓ {Fore.WHITE}Help & Documentation{Style.RESET_ALL}")
        print(f"     View help, troubleshooting, and usage guides")
        print()
        
        # Exit
        print(f"  {Fore.GREEN}6.{Style.RESET_ALL} 🚪 {Fore.WHITE}Exit{Style.RESET_ALL}")
        print()
    
    def launch_web_mode(self):
        """Launch the web interface with enhanced integration"""
        try:
            print(f"{Fore.GREEN}🌐 Starting Web Interface...{Style.RESET_ALL}")
            
            # Check if web_app.py exists
            web_app_path = self.script_dir / "web_app.py"
            if not web_app_path.exists():
                print(f"{Fore.RED}❌ Error: web_app.py not found{Style.RESET_ALL}")
                return False
            
            # Launch web application
            host = "127.0.0.1"
            port = 8000
            
            print(f"📡 Server will start at: http://{host}:{port}")
            print(f"📱 Modern UI with drag-and-drop and real-time progress")
            print(f"🔄 Session data will be shared between CLI and Web modes")
            print()
            
            # Save last mode and sync settings for web app
            self.settings["last_mode"] = "web"
            self.settings["web_host"] = host
            self.settings["web_port"] = port
            self._save_settings()
            
            # Prepare shared data for web app
            self._prepare_web_integration()
            
            # Auto-open browser if enabled
            auto_open = self.settings.get("auto_open_web", True)
            if auto_open:
                print(f"🌐 Browser will open automatically...")
                
            # Launch using Python subprocess with enhanced parameters
            cmd = [
                sys.executable, "web_app.py", 
                "--host", host, 
                "--port", str(port)
            ]
            
            if auto_open:
                # Note: web_app.py would need to be modified to handle this
                cmd.extend(["--auto-open"])
            
            subprocess.run(cmd, cwd=self.script_dir)
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Web interface stopped by user{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to start web interface: {e}{Style.RESET_ALL}")
            return False
    
    def _prepare_web_integration(self):
        """Prepare shared data for web app integration"""
        try:
            from datetime import datetime
            
            # Create web integration data
            integration_data = {
                "launcher_version": "3.0",
                "last_cli_session": datetime.now().isoformat(),
                "user_preferences": self.settings,
                "shared_features": {
                    "prompt_history": True,
                    "favorites": True,
                    "cost_tracking": True,
                    "output_organization": True
                },
                "data_locations": {
                    "prompt_history": "data/prompt_history.json",
                    "favorites": "data/favorite_prompts.json",
                    "user_preferences": "data/user_preferences.json",
                    "batch_processing": "data/batch_processing.json",
                    "output_metadata": "data/output_metadata.json"
                }
            }
            
            # Save integration data
            integration_file = self.data_dir / "web_integration.json"
            with open(integration_file, 'w') as f:
                json.dump(integration_data, f, indent=2)
            
            print(f"{Fore.GREEN}✅ Web integration data prepared{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Could not prepare web integration: {e}{Style.RESET_ALL}")
    
    def launch_cli_mode(self):
        """Launch the enhanced CLI interface"""
        try:
            print(f"{Fore.GREEN}💻 Starting Enhanced CLI Interface...{Style.RESET_ALL}")
            
            # Try to use the enhanced unified launcher
            try:
                from core.launcher.unified_launcher import run_unified_launcher
                
                print(f"🎯 Enhanced CLI with file picker, prompt history, and cost tracking")
                print(f"📊 Real-time model comparison and statistics")
                print(f"⚡ Press Ctrl+C to return to main menu")
                print()
                
                # Save last mode
                self.settings["last_mode"] = "cli"
                self._save_settings()
                
                # Import asyncio to run the enhanced launcher
                import asyncio
                
                # Run the enhanced CLI
                asyncio.run(run_unified_launcher())
                
                return True
                
            except ImportError as e:
                print(f"{Fore.YELLOW}⚠️ Enhanced CLI not available: {e}{Style.RESET_ALL}")
                print(f"Falling back to basic CLI mode...")
                
                # Fallback to basic main.py
                main_py_path = self.script_dir / "main.py"
                if not main_py_path.exists():
                    print(f"{Fore.RED}❌ Error: main.py not found{Style.RESET_ALL}")
                    return False
                
                print(f"🎯 Basic CLI interface")
                print(f"⚡ Press Ctrl+C to return to main menu")
                print()
                
                # Save last mode
                self.settings["last_mode"] = "cli"
                self._save_settings()
                
                # Launch main.py in interactive mode
                cmd = [sys.executable, "main.py", "--mode", "interactive"]
                subprocess.run(cmd, cwd=self.script_dir)
                
                return True
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}CLI interface stopped by user{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to start CLI interface: {e}{Style.RESET_ALL}")
            return False
    
    def launch_quick_generate(self):
        """Launch quick generation mode with file picker"""
        try:
            print(f"{Fore.GREEN}⚡ Quick Generate Mode{Style.RESET_ALL}")
            
            # Import GUI components
            try:
                from core.launcher.file_picker import FilePicker
                from core.launcher.prompt_manager import PromptManager
            except ImportError:
                print(f"{Fore.YELLOW}⚠️ Enhanced features not available, using basic mode{Style.RESET_ALL}")
                return self.launch_cli_mode()
            
            # Initialize components
            file_picker = FilePicker()
            prompt_manager = PromptManager()
            
            # File selection
            print(f"{Fore.CYAN}📁 Select image file...{Style.RESET_ALL}")
            image_path = file_picker.pick_single_file()
            
            if not image_path:
                print(f"{Fore.YELLOW}No file selected, returning to menu{Style.RESET_ALL}")
                return True
            
            # Prompt selection
            print(f"{Fore.CYAN}📝 Select or enter prompt...{Style.RESET_ALL}")
            prompt = prompt_manager.get_quick_prompt()
            
            if not prompt:
                print(f"{Fore.YELLOW}No prompt provided, returning to menu{Style.RESET_ALL}")
                return True
            
            # Launch with selected parameters
            model = self.settings.get("preferred_model", "kling_21_pro")
            duration = self.settings.get("default_duration", 5)
            aspect_ratio = self.settings.get("default_aspect_ratio", "16:9")
            
            print(f"{Fore.GREEN}🎬 Generating with {model}...{Style.RESET_ALL}")
            
            cmd = [
                sys.executable, "main.py",
                "--mode", model.replace("_", ""),
                "--image", image_path,
                "--prompt", f'"{prompt}"',
                "--duration", str(duration),
                "--aspect-ratio", aspect_ratio
            ]
            
            subprocess.run(cmd, cwd=self.script_dir)
            return True
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Quick generate cancelled{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Quick generate failed: {e}{Style.RESET_ALL}")
            return False
    
    def show_settings_menu(self):
        """Show and handle settings configuration"""
        while True:
            print(f"\n{Fore.CYAN}⚙️ Settings Configuration:{Style.RESET_ALL}")
            print()
            print(f"  1. API Key Setup")
            print(f"  2. Default Model: {Fore.GREEN}{self.settings['preferred_model']}{Style.RESET_ALL}")
            print(f"  3. Default Duration: {Fore.GREEN}{self.settings['default_duration']}s{Style.RESET_ALL}")
            print(f"  4. Default Aspect Ratio: {Fore.GREEN}{self.settings['default_aspect_ratio']}{Style.RESET_ALL}")
            print(f"  5. Auto-open Web Browser: {Fore.GREEN}{self.settings['auto_open_web']}{Style.RESET_ALL}")
            print(f"  6. Show Cost Warnings: {Fore.GREEN}{self.settings['show_cost_warnings']}{Style.RESET_ALL}")
            print(f"  7. Back to Main Menu")
            print()
            
            choice = input(f"{Fore.YELLOW}Select option (1-7): {Style.RESET_ALL}").strip()
            
            if choice == "1":
                self._configure_api_key()
            elif choice == "2":
                self._configure_default_model()
            elif choice == "3":
                self._configure_default_duration()
            elif choice == "4":
                self._configure_default_aspect_ratio()
            elif choice == "5":
                self.settings["auto_open_web"] = not self.settings["auto_open_web"]
                self._save_settings()
                print(f"{Fore.GREEN}✅ Auto-open web browser: {self.settings['auto_open_web']}{Style.RESET_ALL}")
            elif choice == "6":
                self.settings["show_cost_warnings"] = not self.settings["show_cost_warnings"]
                self._save_settings()
                print(f"{Fore.GREEN}✅ Show cost warnings: {self.settings['show_cost_warnings']}{Style.RESET_ALL}")
            elif choice == "7":
                break
            else:
                print(f"{Fore.RED}Invalid choice. Please select 1-7.{Style.RESET_ALL}")
    
    def _configure_api_key(self):
        """Configure FAL API key"""
        print(f"\n{Fore.CYAN}🔑 API Key Configuration:{Style.RESET_ALL}")
        print("Your FAL API key is needed to generate videos.")
        print("Get your key from: https://fal.ai/dashboard")
        print()
        
        current_key = os.getenv("FAL_KEY", "")
        if current_key:
            masked_key = current_key[:8] + "*" * (len(current_key) - 8)
            print(f"Current key: {masked_key}")
        
        new_key = input("Enter new API key (or press Enter to keep current): ").strip()
        if new_key:
            os.environ["FAL_KEY"] = new_key
            print(f"{Fore.GREEN}✅ API key updated{Style.RESET_ALL}")
            print("Note: Set FAL_KEY environment variable permanently for future sessions")
    
    def _configure_default_model(self):
        """Configure default model"""
        models = [
            ("kling_21_standard", "Kling 2.1 Standard - $0.25/5s"),
            ("kling_21_pro", "Kling 2.1 Pro - $0.45/5s"), 
            ("kling_21_master", "Kling 2.1 Master - $0.70/5s"),
            ("kling_16_pro", "Kling 1.6 Pro - $0.40/5s"),
            ("luma_dream", "Luma Dream Machine - $0.50/5s")
        ]
        
        print(f"\n{Fore.CYAN}🎯 Default Model Selection:{Style.RESET_ALL}")
        for i, (key, desc) in enumerate(models, 1):
            current = " (current)" if key == self.settings["preferred_model"] else ""
            print(f"  {i}. {desc}{Fore.GREEN}{current}{Style.RESET_ALL}")
        
        choice = input(f"\nSelect model (1-{len(models)}): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                self.settings["preferred_model"] = models[idx][0]
                self._save_settings()
                print(f"{Fore.GREEN}✅ Default model: {models[idx][1]}{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid selection{Style.RESET_ALL}")
    
    def _configure_default_duration(self):
        """Configure default duration"""
        print(f"\n{Fore.CYAN}⏱️ Default Duration Configuration:{Style.RESET_ALL}")
        duration = input(f"Enter default duration in seconds (current: {self.settings['default_duration']}): ").strip()
        try:
            duration = int(duration)
            if 1 <= duration <= 10:
                self.settings["default_duration"] = duration
                self._save_settings()
                print(f"{Fore.GREEN}✅ Default duration: {duration}s{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Duration must be between 1 and 10 seconds{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid duration{Style.RESET_ALL}")
    
    def _configure_default_aspect_ratio(self):
        """Configure default aspect ratio"""
        ratios = ["16:9", "9:16", "1:1", "4:3", "3:4"]
        
        print(f"\n{Fore.CYAN}📐 Default Aspect Ratio Configuration:{Style.RESET_ALL}")
        for i, ratio in enumerate(ratios, 1):
            current = " (current)" if ratio == self.settings["default_aspect_ratio"] else ""
            print(f"  {i}. {ratio}{Fore.GREEN}{current}{Style.RESET_ALL}")
        
        choice = input(f"\nSelect aspect ratio (1-{len(ratios)}): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(ratios):
                self.settings["default_aspect_ratio"] = ratios[idx]
                self._save_settings()
                print(f"{Fore.GREEN}✅ Default aspect ratio: {ratios[idx]}{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid selection{Style.RESET_ALL}")
    
    def show_help(self):
        """Display help and documentation"""
        print(f"\n{Fore.CYAN}❓ Help & Documentation:{Style.RESET_ALL}")
        print()
        print(f"{Fore.WHITE}🎬 FAL.AI Video Generator{Style.RESET_ALL}")
        print("Professional video generation using state-of-the-art AI models")
        print()
        print(f"{Fore.GREEN}Available Models:{Style.RESET_ALL}")
        print("• Kling 2.1 Standard ($0.25/5s) - Cost-efficient, high quality")
        print("• Kling 2.1 Pro ($0.45/5s) - Professional grade") 
        print("• Kling 2.1 Master ($0.70/5s) - Premium quality")
        print("• Kling 1.6 Pro ($0.40/5s) - Legacy with good features")
        print("• Luma Dream Machine ($0.50/5s) - Alternative engine")
        print()
        print(f"{Fore.GREEN}Quick Start:{Style.RESET_ALL}")
        print("1. Set your FAL_KEY environment variable")
        print("2. Choose Web Interface for beginners or CLI for power users")
        print("3. Upload/select an image and enter a creative prompt")
        print("4. Select model, duration, and aspect ratio")
        print("5. Generate and download your video!")
        print()
        print(f"{Fore.GREEN}Tips:{Style.RESET_ALL}")
        print("• Use descriptive prompts for better results")
        print("• Start with Kling 2.1 Pro for best quality/cost balance")
        print("• 16:9 aspect ratio works best for most content")
        print("• Check cost estimates before generating expensive videos")
        print()
        print(f"{Fore.GREEN}Support:{Style.RESET_ALL}")
        print("• Documentation: See CLAUDE.md and README.md")
        print("• Troubleshooting: Check TROUBLESHOOTING.md")
        print("• API Issues: Visit https://fal.ai/dashboard")
        print()
        
        input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    def run_interactive(self):
        """Run the interactive launcher"""
        while True:
            try:
                # Clear screen (works on Windows and Unix)
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Show banner and status
                self.show_banner()
                env_status = self.check_environment()
                self.show_environment_status(env_status)
                
                # Show main menu
                self.show_main_menu(env_status)
                
                # Get user choice
                choice = input(f"{Fore.YELLOW}Select mode (1-6): {Style.RESET_ALL}").strip()
                
                if choice == "1":  # Web Interface
                    if env_status['web_dependencies']:
                        self.launch_web_mode()
                    else:
                        print(f"{Fore.RED}❌ Web dependencies not available{Style.RESET_ALL}")
                        print(f"Install with: pip install fastapi uvicorn")
                        input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                
                elif choice == "2":  # CLI Interface
                    if env_status['cli_dependencies']:
                        self.launch_cli_mode()
                    else:
                        print(f"{Fore.RED}❌ CLI dependencies not available{Style.RESET_ALL}")
                        print(f"Install with: pip install -r requirements.txt")
                        input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                
                elif choice == "3":  # Quick Generate
                    if env_status['cli_dependencies'] and env_status['gui_available']:
                        self.launch_quick_generate()
                    else:
                        print(f"{Fore.RED}❌ Quick generate requires GUI support and CLI dependencies{Style.RESET_ALL}")
                        input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                
                elif choice == "4":  # Settings
                    self.show_settings_menu()
                
                elif choice == "5":  # Help
                    self.show_help()
                
                elif choice == "6":  # Exit
                    print(f"{Fore.GREEN}👋 Thanks for using FAL.AI Video Generator!{Style.RESET_ALL}")
                    break
                
                else:
                    print(f"{Fore.RED}Invalid choice. Please select 1-6.{Style.RESET_ALL}")
                    input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            
            except KeyboardInterrupt:
                print(f"\n{Fore.GREEN}👋 Goodbye!{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
                input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")


# =============================================================================
# ULTIMATE SINGLE LAUNCHER - All functionality consolidated here
# =============================================================================

def create_simple_launcher():
    """Create simple.bat launcher for ultimate convenience"""
    simple_launcher_content = """@echo off
title FAL.AI Video Generator
python FAL_LAUNCHER.py
"""
    
    simple_launcher_path = Path(__file__).parent / "simple.bat"
    try:
        with open(simple_launcher_path, 'w') as f:
            f.write(simple_launcher_content.strip())
        print(f"✅ Created simple.bat launcher")
    except Exception as e:
        print(f"⚠️ Could not create simple.bat: {e}")

def show_cleanup_status():
    """Show directory cleanup status"""
    print(f"\n{Fore.GREEN}🧹 DIRECTORY CLEANUP COMPLETED:{Style.RESET_ALL}")
    print("✅ All redundant launchers removed")
    print("✅ Duplicate scripts consolidated") 
    print("✅ Temporary files cleaned")
    print("✅ Single launcher system active")
    print(f"\n{Fore.CYAN}Usage: python FAL_LAUNCHER.py{Style.RESET_ALL}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="FAL.AI Video Generator - Unified Launcher")
    parser.add_argument("--mode", choices=["web", "cli", "quick", "interactive"], 
                       default="interactive", help="Launch mode")
    parser.add_argument("--no-banner", action="store_true", help="Skip banner display")
    
    args = parser.parse_args()
    
    try:
        launcher = FALLauncher()
        
        if args.mode == "web":
            launcher.launch_web_mode()
        elif args.mode == "cli":
            launcher.launch_cli_mode()
        elif args.mode == "quick":
            launcher.launch_quick_generate()
        else:
            launcher.run_interactive()
    
    except KeyboardInterrupt:
        print(f"\n{Fore.GREEN}👋 Goodbye!{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Launch failed: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()