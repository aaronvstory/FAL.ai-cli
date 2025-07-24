#!/usr/bin/env python3
"""
Unified Launcher Module - Enhanced CLI Interface
Integrates with existing main.py VideoGenerator with enhanced UX
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add parent directory to path to import main modules
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from main import Config, VideoGenerator
    from security import InputValidator
    from colorama import init, Fore, Style
    
    # Import our enhanced modules
    from core.launcher.file_picker import FilePicker
    from core.launcher.prompt_manager import PromptManager
    
    # Initialize colorama
    init()
    
except ImportError as e:
    print(f"❌ Error importing dependencies: {e}")
    print("Please ensure all required modules are available")
    sys.exit(1)

class UnifiedLauncher:
    """Enhanced CLI launcher with integrated file picker and prompt management"""
    
    def __init__(self):
        self.config = Config()
        self.generator = VideoGenerator(self.config)
        self.file_picker = FilePicker()
        self.prompt_manager = PromptManager()
        
        # Enhanced model configurations with user-friendly names
        self.models = self._load_model_configs()
        
        print(f"{Fore.GREEN}✅ Unified Launcher initialized{Style.RESET_ALL}")
    
    def _load_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load and organize model configurations"""
        raw_models = self.config.get("models", {})
        organized_models = {}
        
        # Filter and organize models
        for key, model_data in raw_models.items():
            if isinstance(model_data, dict) and "endpoint" in model_data:
                organized_models[key] = {
                    **model_data,
                    "key": key,
                    "display_name": model_data.get("name", key.replace("_", " ").title()),
                    "cost_display": f"${model_data.get('cost_5s', 0):.2f}/5s",
                    "recommended": key in ["kling_21_pro", "kling_21_standard"]
                }
        
        return organized_models
    
    def show_enhanced_banner(self):
        """Display enhanced banner with system info"""
        banner = f"""
{Fore.MAGENTA}{'=' * 80}
{Fore.CYAN}              🎬 FAL.AI Video Generator - Enhanced CLI 🎬
{Fore.CYAN}                        🚀 Professional Interface 🚀
{Fore.MAGENTA}{'=' * 80}{Style.RESET_ALL}

{Fore.WHITE}📊 System Status:{Style.RESET_ALL}
  • API Key: {'✅ Configured' if os.getenv('FAL_KEY') else '❌ Not Set'}
  • Models Available: {Fore.GREEN}{len(self.models)}{Style.RESET_ALL}
  • GUI Support: {'✅ Available' if self._check_gui_support() else '❌ Not Available'}
  • Enhanced Features: {Fore.GREEN}✅ File Picker, Prompt Manager, Smart Output{Style.RESET_ALL}

{Fore.CYAN}🎯 Quick Actions:{Style.RESET_ALL}
  Press {Fore.YELLOW}Q{Style.RESET_ALL} for Quick Generate  |  {Fore.YELLOW}H{Style.RESET_ALL} for Help  |  {Fore.YELLOW}S{Style.RESET_ALL} for Statistics
"""
        print(banner)
    
    def _check_gui_support(self) -> bool:
        """Check if GUI (tkinter) is available"""
        try:
            import tkinter
            return True
        except ImportError:
            return False
    
    def show_model_menu(self):
        """Display enhanced model selection menu"""
        print(f"\n{Fore.CYAN}🎬 Select Video Generation Model:{Style.RESET_ALL}")
        print()
        
        # Group models by tier
        tiers = {
            "Premium": [],
            "Professional": [],
            "Standard": [],
            "Legacy": [],
            "Budget": [],
            "Alternative": []
        }
        
        for model in self.models.values():
            tier = model.get("tier", "Standard")
            tiers[tier].append(model)
        
        option_num = 1
        self.model_options = {}  # Store mapping of numbers to model keys
        
        for tier, models in tiers.items():
            if not models:
                continue
                
            print(f"{Fore.WHITE}  ━━ {tier} Models ━━{Style.RESET_ALL}")
            
            for model in models:
                # Visual indicators
                recommended = "⭐" if model.get("recommended") else "  "
                quality_icons = {
                    "Premium": "💎",
                    "High": "🔥", 
                    "Good": "👍",
                    "Standard": "✅"
                }
                quality_icon = quality_icons.get(model.get("quality", "Standard"), "📊")
                
                print(f"  {Fore.GREEN}{option_num:2d}.{Style.RESET_ALL} {recommended} {quality_icon} {Fore.WHITE}{model['display_name']}{Style.RESET_ALL}")
                print(f"       💰 {Fore.YELLOW}{model['cost_display']}{Style.RESET_ALL} • {model.get('description', 'No description')}")
                print(f"       📋 Best for: {model.get('best_for', 'General use')}")
                
                self.model_options[str(option_num)] = model['key']
                option_num += 1
                print()
        
        # Special options
        print(f"{Fore.WHITE}  ━━ Special Options ━━{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}{option_num:2d}.{Style.RESET_ALL} 🔄 {Fore.WHITE}Custom Workflow{Style.RESET_ALL}")
        print(f"       Run predefined workflow with custom parameters")
        self.model_options[str(option_num)] = "workflow"
        option_num += 1
        
        print(f"  {Fore.GREEN}{option_num:2d}.{Style.RESET_ALL} 📊 {Fore.WHITE}Model Comparison{Style.RESET_ALL}")
        print(f"       Compare models side-by-side with pricing")
        self.model_options[str(option_num)] = "compare"
        option_num += 1
        
        print(f"  {Fore.GREEN}{option_num:2d}.{Style.RESET_ALL} 🚪 {Fore.WHITE}Back to Main Menu{Style.RESET_ALL}")
        self.model_options[str(option_num)] = "back"
        print()
    
    def show_model_comparison(self):
        """Display detailed model comparison"""
        print(f"\n{Fore.CYAN}📊 Model Comparison Table:{Style.RESET_ALL}")
        print()
        
        # Header
        print(f"{'Model':<25} {'Tier':<12} {'Quality':<10} {'5s Cost':<8} {'10s Cost':<9} {'Max Dur':<7}")
        print(f"{'-' * 25} {'-' * 12} {'-' * 10} {'-' * 8} {'-' * 9} {'-' * 7}")
        
        # Sort models by cost for comparison
        sorted_models = sorted(self.models.values(), key=lambda x: x.get('cost_5s', 0))
        
        for model in sorted_models:
            name = model['display_name'][:24]
            tier = model.get('tier', 'Standard')[:11]
            quality = model.get('quality', 'Standard')[:9]
            cost_5s = f"${model.get('cost_5s', 0):.2f}"
            cost_10s = f"${model.get('cost_10s', 0):.2f}"
            max_dur = f"{model.get('max_duration', 5)}s"
            
            # Color coding by cost
            if model.get('cost_5s', 0) <= 0.30:
                color = Fore.GREEN  # Cheap
            elif model.get('cost_5s', 0) <= 0.50:
                color = Fore.YELLOW  # Medium
            else:
                color = Fore.RED  # Expensive
            
            print(f"{color}{name:<25} {tier:<12} {quality:<10} {cost_5s:<8} {cost_10s:<9} {max_dur:<7}{Style.RESET_ALL}")
        
        print()
        input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    def get_enhanced_file_input(self) -> Optional[str]:
        """Get file input with multiple options"""
        print(f"\n{Fore.CYAN}📁 Image Selection:{Style.RESET_ALL}")
        print("1. 🖼️  GUI File Picker (Recommended)")
        print("2. 📝 Type file path manually")
        print("3. 🔍 Browse with preview")
        print("4. ❌ Cancel")
        
        choice = input(f"\n{Fore.YELLOW}Select option (1-4): {Style.RESET_ALL}").strip()
        
        if choice == "1":
            if self._check_gui_support():
                file_path = self.file_picker.pick_single_file()
                if file_path:
                    print(f"{Fore.GREEN}✅ Selected: {Path(file_path).name}{Style.RESET_ALL}")
                return file_path
            else:
                print(f"{Fore.RED}❌ GUI not available, falling back to manual input{Style.RESET_ALL}")
                return self.file_picker.get_cli_file_path()
        
        elif choice == "2":
            return self.file_picker.get_cli_file_path()
        
        elif choice == "3":
            if self._check_gui_support():
                try:
                    file_path = self.file_picker.pick_with_preview()
                    if file_path:
                        print(f"{Fore.GREEN}✅ Selected: {Path(file_path).name}{Style.RESET_ALL}")
                    return file_path
                except Exception as e:
                    print(f"{Fore.YELLOW}⚠️ Preview not available: {e}{Style.RESET_ALL}")
                    return self.file_picker.pick_single_file()
            else:
                print(f"{Fore.RED}❌ GUI not available{Style.RESET_ALL}")
                return self.file_picker.get_cli_file_path()
        
        return None
    
    def get_enhanced_prompt_input(self) -> Optional[str]:
        """Get prompt input with smart suggestions"""
        print(f"\n{Fore.CYAN}📝 Prompt Selection:{Style.RESET_ALL}")
        
        # Quick stats
        recent_count = len(self.prompt_manager.get_recent_prompts(5))
        favorites_count = len(self.prompt_manager.get_favorites())
        
        print("1. ✏️  Enter new prompt")
        if recent_count > 0:
            print(f"2. 📋 Use recent prompt ({recent_count} available)")
        if favorites_count > 0:
            print(f"3. ⭐ Use favorite prompt ({favorites_count} available)")
        print("4. 🎨 Generate from template")
        print("5. 🔍 Search prompt history")
        print("6. ❌ Cancel")
        
        choice = input(f"\n{Fore.YELLOW}Select option: {Style.RESET_ALL}").strip()
        
        if choice == "1":
            return self._get_new_prompt_with_validation()
        elif choice == "2" and recent_count > 0:
            return self._select_from_recent()
        elif choice == "3" and favorites_count > 0:
            return self._select_from_favorites()
        elif choice == "4":
            return self._generate_template_prompt()
        elif choice == "5":
            return self._search_prompt_history()
        
        return None
    
    def _get_new_prompt_with_validation(self) -> Optional[str]:
        """Get new prompt with real-time validation and suggestions"""
        try:
            prompt = input(f"\n{Fore.CYAN}Enter your prompt: {Style.RESET_ALL}").strip()
            
            if not prompt:
                return None
            
            # Security validation
            validated_prompt = InputValidator.sanitize_prompt(prompt)
            if not validated_prompt:
                print(f"{Fore.RED}❌ Prompt contains unsafe content{Style.RESET_ALL}")
                return None
            
            # Show improvement suggestions
            suggestions = self.prompt_manager.suggest_improvements(prompt)
            if suggestions:
                print(f"\n{Fore.YELLOW}💡 Suggestions to improve your prompt:{Style.RESET_ALL}")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"  {i}. {suggestion}")
                
                improve = input(f"\n{Fore.CYAN}Apply suggestions? (y/n): {Style.RESET_ALL}").strip().lower()
                if improve == 'y':
                    improved_prompt = input(f"{Fore.CYAN}Enter improved prompt: {Style.RESET_ALL}").strip()
                    if improved_prompt:
                        validated_improved = InputValidator.sanitize_prompt(improved_prompt)
                        if validated_improved:
                            return validated_improved
            
            return validated_prompt
            
        except KeyboardInterrupt:
            return None
    
    def _select_from_recent(self) -> Optional[str]:
        """Select from recent prompts"""
        recent = self.prompt_manager.get_recent_prompts(10)
        
        print(f"\n{Fore.CYAN}📋 Recent Prompts:{Style.RESET_ALL}")
        for i, entry in enumerate(recent, 1):
            display_prompt = entry["prompt"][:70] + ("..." if len(entry["prompt"]) > 70 else "")
            timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%m/%d %H:%M")
            model = entry.get("model", "unknown")
            success_icon = "✅" if entry.get("success", True) else "❌"
            
            print(f"  {i:2d}. {display_prompt}")
            print(f"      {success_icon} {Fore.GREEN}[{model}] {timestamp}{Style.RESET_ALL}")
        
        try:
            choice = input(f"\n{Fore.YELLOW}Select prompt (1-{len(recent)}): {Style.RESET_ALL}").strip()
            if choice:
                idx = int(choice) - 1
                if 0 <= idx < len(recent):
                    return recent[idx]["prompt"]
        except ValueError:
            pass
        
        return None
    
    def _select_from_favorites(self) -> Optional[str]:
        """Select from favorite prompts with usage tracking"""
        favorites = self.prompt_manager.get_favorites()
        
        print(f"\n{Fore.CYAN}⭐ Favorite Prompts:{Style.RESET_ALL}")
        for i, fav in enumerate(favorites, 1):
            usage = fav.get("usage_count", 0)
            category = fav.get("category", "general")
            
            print(f"  {i:2d}. {fav['name']}")
            print(f"      {Fore.GREEN}[{category}] Used {usage} times{Style.RESET_ALL}")
        
        try:
            choice = input(f"\n{Fore.YELLOW}Select favorite (1-{len(favorites)}): {Style.RESET_ALL}").strip()
            if choice:
                idx = int(choice) - 1
                if 0 <= idx < len(favorites):
                    return self.prompt_manager.use_favorite(idx)
        except ValueError:
            pass
        
        return None
    
    def _generate_template_prompt(self) -> Optional[str]:
        """Generate prompt from template with customization"""
        print(f"\n{Fore.CYAN}🎨 Template Categories:{Style.RESET_ALL}")
        categories = list(self.prompt_manager.templates.keys())
        
        for i, category in enumerate(categories, 1):
            print(f"  {i}. {category.title()}")
        
        try:
            choice = input(f"\n{Fore.YELLOW}Select category (1-{len(categories)}): {Style.RESET_ALL}").strip()
            if choice:
                idx = int(choice) - 1
                if 0 <= idx < len(categories):
                    category = categories[idx]
                    
                    subject = input(f"{Fore.CYAN}Enter subject/theme: {Style.RESET_ALL}").strip()
                    template_prompt = self.prompt_manager.generate_template_prompt(category, subject)
                    
                    if template_prompt:
                        print(f"\n{Fore.GREEN}Generated prompt:{Style.RESET_ALL} {template_prompt}")
                        
                        use_it = input(f"\n{Fore.CYAN}Use this prompt? (y/n): {Style.RESET_ALL}").strip().lower()
                        if use_it == 'y':
                            return template_prompt
        except ValueError:
            pass
        
        return None
    
    def _search_prompt_history(self) -> Optional[str]:
        """Search through prompt history"""
        query = input(f"\n{Fore.CYAN}Enter search terms: {Style.RESET_ALL}").strip()
        
        if not query:
            return None
        
        matches = self.prompt_manager.search_history(query, 15)
        
        if not matches:
            print(f"{Fore.YELLOW}No matching prompts found{Style.RESET_ALL}")
            return None
        
        print(f"\n{Fore.CYAN}🔍 Search Results for '{query}':{Style.RESET_ALL}")
        for i, entry in enumerate(matches, 1):
            # Highlight search terms
            display_prompt = entry["prompt"]
            for term in query.split():
                display_prompt = display_prompt.replace(
                    term, f"{Fore.YELLOW}{term}{Style.RESET_ALL}"
                )
            
            if len(display_prompt) > 80:
                display_prompt = display_prompt[:80] + "..."
            
            timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%m/%d %H:%M")
            model = entry.get("model", "unknown")
            success_icon = "✅" if entry.get("success", True) else "❌"
            
            print(f"  {i:2d}. {display_prompt}")
            print(f"      {success_icon} {Fore.GREEN}[{model}] {timestamp}{Style.RESET_ALL}")
        
        try:
            choice = input(f"\n{Fore.YELLOW}Select prompt (1-{len(matches)}): {Style.RESET_ALL}").strip()
            if choice:
                idx = int(choice) - 1
                if 0 <= idx < len(matches):
                    return matches[idx]["prompt"]
        except ValueError:
            pass
        
        return None
    
    def get_generation_parameters(self, model_key: str) -> Dict[str, Any]:
        """Get generation parameters with smart defaults"""
        model_config = self.models[model_key]
        
        print(f"\n{Fore.CYAN}⚙️ Generation Parameters for {model_config['display_name']}:{Style.RESET_ALL}")
        
        # Duration
        max_duration = model_config.get("max_duration", 10)
        default_duration = min(5, max_duration)
        
        print(f"Duration (1-{max_duration}s, default: {default_duration}s):")
        duration_input = input(f"  {Fore.YELLOW}Enter duration: {Style.RESET_ALL}").strip()
        
        try:
            duration = int(duration_input) if duration_input else default_duration
            duration = max(1, min(duration, max_duration))
        except ValueError:
            duration = default_duration
        
        # Calculate and show cost
        cost_5s = model_config.get("cost_5s", 0)
        cost_per_second = model_config.get("cost_per_second", cost_5s / 5)
        estimated_cost = cost_per_second * duration
        
        print(f"  💰 Estimated cost: {Fore.YELLOW}${estimated_cost:.3f}{Style.RESET_ALL}")
        
        # Aspect ratio
        print(f"\nAspect Ratio:")
        ratios = ["16:9", "9:16", "1:1", "4:3", "3:4"]
        for i, ratio in enumerate(ratios, 1):
            print(f"  {i}. {ratio}")
        
        ratio_choice = input(f"  {Fore.YELLOW}Select ratio (1-{len(ratios)}, default: 1): {Style.RESET_ALL}").strip()
        try:
            ratio_idx = int(ratio_choice) - 1 if ratio_choice else 0
            aspect_ratio = ratios[ratio_idx] if 0 <= ratio_idx < len(ratios) else "16:9"
        except ValueError:
            aspect_ratio = "16:9"
        
        parameters = {
            "duration": duration,
            "aspect_ratio": aspect_ratio
        }
        
        # Advanced parameters for newer models
        if "21" in model_key or "16" in model_key:
            print(f"\n{Fore.CYAN}🔧 Advanced Parameters (optional):{Style.RESET_ALL}")
            
            # Negative prompt
            neg_prompt = input(f"Negative prompt (things to avoid): {Style.RESET_ALL}").strip()
            if neg_prompt:
                parameters["negative_prompt"] = neg_prompt
            
            # CFG Scale
            cfg_input = input(f"CFG Scale (0.1-1.0, default: 0.5): {Style.RESET_ALL}").strip()
            if cfg_input:
                try:
                    cfg_scale = float(cfg_input)
                    if 0.1 <= cfg_scale <= 1.0:
                        parameters["cfg_scale"] = cfg_scale
                except ValueError:
                    pass
        
        return parameters
    
    async def generate_with_progress(self, model_key: str, image_path: str, 
                                   prompt: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Generate video with enhanced progress tracking"""
        try:
            print(f"\n{Fore.GREEN}🎬 Starting generation with {self.models[model_key]['display_name']}...{Style.RESET_ALL}")
            print(f"📁 Image: {Path(image_path).name}")
            print(f"📝 Prompt: {prompt}")
            print(f"⚙️ Parameters: {kwargs}")
            print()
            
            # Get model configuration
            model_config = self.models[model_key]
            endpoint = model_config["endpoint"]
            
            # Generate video using appropriate method
            if model_key == "workflow":
                result = await self.generator.run_workflow(arguments={"image_path": image_path, "prompt": prompt, **kwargs})
            else:
                result = await self.generator.generate_video(endpoint, image_path, prompt, **kwargs)
            
            # Save prompt to history
            self.prompt_manager.save_prompt(prompt, model_key, True, {
                "image_path": image_path,
                "parameters": kwargs,
                "result": result
            })
            
            print(f"\n{Fore.GREEN}✅ Generation completed successfully!{Style.RESET_ALL}")
            
            # Show result summary
            if isinstance(result, dict):
                if "video" in result:
                    video_info = result["video"]
                    if isinstance(video_info, dict) and "url" in video_info:
                        print(f"📹 Video URL: {video_info['url']}")
                    elif isinstance(video_info, str):
                        print(f"📹 Video URL: {video_info}")
                
                if "duration" in result:
                    print(f"⏱️ Duration: {result['duration']}s")
            
            # Ask to save as favorite
            save_fav = input(f"\n{Fore.CYAN}Save this prompt as favorite? (y/n): {Style.RESET_ALL}").strip().lower()
            if save_fav == 'y':
                name = input(f"Enter name for favorite (or press Enter for auto-name): {Style.RESET_ALL}").strip()
                self.prompt_manager.add_to_favorites(prompt, name)
            
            return result
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Generation failed: {e}{Style.RESET_ALL}")
            
            # Save failed prompt to history
            self.prompt_manager.save_prompt(prompt, model_key, False, {
                "image_path": image_path,
                "parameters": kwargs,
                "error": str(e)
            })
            
            return None
    
    def show_statistics(self):
        """Show usage statistics and insights"""
        stats = self.prompt_manager.get_stats()
        
        print(f"\n{Fore.CYAN}📊 Usage Statistics:{Style.RESET_ALL}")
        print(f"Total prompts generated: {stats['total_prompts']}")
        print(f"Successful generations: {stats['successful_prompts']}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Favorite prompts: {stats['total_favorites']}")
        print(f"Favorite categories: {stats['favorite_categories']}")
        
        if stats['popular_models']:
            print(f"\n{Fore.CYAN}🏆 Most Used Models:{Style.RESET_ALL}")
            for model, count in stats['popular_models']:
                print(f"  {model}: {count} times")
        
        print()
        input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    def show_help(self):
        """Show comprehensive help"""
        help_text = f"""
{Fore.CYAN}❓ Enhanced CLI Help:{Style.RESET_ALL}

{Fore.WHITE}🎬 Generation Process:{Style.RESET_ALL}
1. Select a model from the menu (⭐ indicates recommended)
2. Choose image using GUI file picker or manual input
3. Enter prompt using various input methods
4. Configure generation parameters
5. Review cost estimate and generate

{Fore.WHITE}🔧 Enhanced Features:{Style.RESET_ALL}
• {Fore.GREEN}GUI File Picker{Style.RESET_ALL}: Visual file selection with preview
• {Fore.GREEN}Prompt Manager{Style.RESET_ALL}: History, favorites, and templates
• {Fore.GREEN}Smart Suggestions{Style.RESET_ALL}: Automatic prompt improvements
• {Fore.GREEN}Cost Calculator{Style.RESET_ALL}: Real-time cost estimation
• {Fore.GREEN}Usage Statistics{Style.RESET_ALL}: Track your generation patterns

{Fore.WHITE}💡 Pro Tips:{Style.RESET_ALL}
• Use descriptive prompts for better results
• Start with Kling 2.1 Pro for best quality/cost balance
• Save good prompts as favorites for reuse
• Use templates for inspiration
• Check cost estimates before expensive generations

{Fore.WHITE}⌨️ Keyboard Shortcuts:{Style.RESET_ALL}
• Q: Quick generate mode
• S: Show statistics  
• H: Show this help
• Ctrl+C: Cancel current operation

{Fore.WHITE}📁 File Organization:{Style.RESET_ALL}
• Prompt history: data/prompt_history.json
• Favorites: data/favorite_prompts.json
• Settings: data/user_preferences.json
"""
        print(help_text)
        input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def run_interactive(self):
        """Run the enhanced interactive CLI"""
        while True:
            try:
                # Clear screen
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Show banner
                self.show_enhanced_banner()
                
                # Handle quick shortcuts
                print(f"{Fore.YELLOW}Quick Actions: [Q]uick Generate | [S]tatistics | [H]elp | [E]xit{Style.RESET_ALL}")
                
                # Show model menu
                self.show_model_menu()
                
                # Get user choice
                choice = input(f"{Fore.YELLOW}Select option or shortcut: {Style.RESET_ALL}").strip().upper()
                
                # Handle shortcuts
                if choice == 'Q':
                    await self._quick_generate()
                    continue
                elif choice == 'S':
                    self.show_statistics()
                    continue
                elif choice == 'H':
                    self.show_help()
                    continue
                elif choice == 'E':
                    print(f"{Fore.GREEN}👋 Thanks for using FAL.AI Video Generator!{Style.RESET_ALL}")
                    break
                
                # Handle model selection
                if choice in self.model_options:
                    model_key = self.model_options[choice]
                    
                    if model_key == "back":
                        break
                    elif model_key == "compare":
                        self.show_model_comparison()
                        continue
                    elif model_key == "workflow":
                        await self._run_workflow()
                        continue
                    else:
                        await self._run_generation(model_key)
                else:
                    print(f"{Fore.RED}Invalid selection. Please try again.{Style.RESET_ALL}")
                    input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Operation cancelled by user{Style.RESET_ALL}")
                continue
            except Exception as e:
                print(f"\n{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
                input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _quick_generate(self):
        """Quick generation with last used settings"""
        print(f"\n{Fore.GREEN}⚡ Quick Generate Mode{Style.RESET_ALL}")
        
        # Use last successful model or default
        recent_prompts = self.prompt_manager.get_recent_prompts(1, successful_only=True)
        if recent_prompts:
            last_model = recent_prompts[0].get("model", "kling_21_pro")
        else:
            last_model = "kling_21_pro"
        
        if last_model not in self.models:
            last_model = list(self.models.keys())[0]
        
        print(f"Using model: {Fore.GREEN}{self.models[last_model]['display_name']}{Style.RESET_ALL}")
        
        # Get image
        image_path = self.get_enhanced_file_input()
        if not image_path:
            return
        
        # Get prompt
        prompt = self.get_enhanced_prompt_input()
        if not prompt:
            return
        
        # Use default parameters
        default_params = {
            "duration": 5,
            "aspect_ratio": "16:9"
        }
        
        # Generate
        await self.generate_with_progress(last_model, image_path, prompt, **default_params)
        
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _run_generation(self, model_key: str):
        """Run full generation process for selected model"""
        print(f"\n{Fore.GREEN}🎬 {self.models[model_key]['display_name']} Generation{Style.RESET_ALL}")
        
        # Get image
        image_path = self.get_enhanced_file_input()
        if not image_path:
            return
        
        # Get prompt
        prompt = self.get_enhanced_prompt_input()
        if not prompt:
            return
        
        # Get parameters
        parameters = self.get_generation_parameters(model_key)
        
        # Confirm generation
        print(f"\n{Fore.CYAN}📋 Generation Summary:{Style.RESET_ALL}")
        print(f"Model: {self.models[model_key]['display_name']}")
        print(f"Image: {Path(image_path).name}")
        print(f"Prompt: {prompt}")
        for key, value in parameters.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        confirm = input(f"\n{Fore.YELLOW}Start generation? (y/n): {Style.RESET_ALL}").strip().lower()
        if confirm != 'y':
            return
        
        # Generate
        await self.generate_with_progress(model_key, image_path, prompt, **parameters)
        
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    async def _run_workflow(self):
        """Run custom workflow"""
        print(f"\n{Fore.GREEN}🔄 Custom Workflow{Style.RESET_ALL}")
        print("Custom workflows allow advanced parameter control")
        
        # Get basic inputs
        image_path = self.get_enhanced_file_input()
        if not image_path:
            return
        
        prompt = self.get_enhanced_prompt_input()
        if not prompt:
            return
        
        # Workflow-specific parameters
        print(f"\n{Fore.CYAN}🔧 Workflow Parameters:{Style.RESET_ALL}")
        
        arguments = {
            "image_path": image_path,
            "prompt": prompt
        }
        
        # Add any additional workflow parameters here
        custom_params = input(f"Additional parameters (JSON format, optional): {Style.RESET_ALL}").strip()
        if custom_params:
            try:
                import json
                extra_params = json.loads(custom_params)
                arguments.update(extra_params)
            except json.JSONDecodeError:
                print(f"{Fore.YELLOW}⚠️ Invalid JSON, using basic parameters{Style.RESET_ALL}")
        
        # Run workflow
        try:
            result = await self.generator.run_workflow(arguments=arguments)
            
            self.prompt_manager.save_prompt(prompt, "workflow", True, {
                "image_path": image_path,
                "arguments": arguments,
                "result": result
            })
            
            print(f"\n{Fore.GREEN}✅ Workflow completed!{Style.RESET_ALL}")
            print(f"Result: {result}")
            
        except Exception as e:
            print(f"\n{Fore.RED}❌ Workflow failed: {e}{Style.RESET_ALL}")
            self.prompt_manager.save_prompt(prompt, "workflow", False, {
                "image_path": image_path,
                "arguments": arguments,
                "error": str(e)
            })
        
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")

# Convenience function
async def run_unified_launcher():
    """Run the unified launcher"""
    launcher = UnifiedLauncher()
    await launcher.run_interactive()

# Test function
if __name__ == "__main__":
    print("Testing Unified Launcher...")
    
    try:
        asyncio.run(run_unified_launcher())
    except KeyboardInterrupt:
        print(f"\n{Fore.GREEN}👋 Goodbye!{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Launcher error: {e}{Style.RESET_ALL}")