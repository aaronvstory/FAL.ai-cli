#!/usr/bin/env python3
"""
Prompt Manager Module - History and favorites management
Provides prompt history, favorites, and intelligent suggestions
"""

import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from colorama import Fore, Style

class PromptManager:
    """Manages prompt history, favorites, and suggestions"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.history_file = self.data_dir / "prompt_history.json"
        self.favorites_file = self.data_dir / "favorite_prompts.json"
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data structures
        self.history = self._load_history()
        self.favorites = self._load_favorites()
        
        # Prompt templates for common scenarios
        self.templates = {
            "cinematic": [
                "Cinematic shot of {subject}, dramatic lighting, film noir style",
                "Epic cinematic scene with {subject}, golden hour lighting",
                "Professional film shot, {subject} in dramatic pose, high contrast"
            ],
            "nature": [
                "Beautiful natural landscape with {subject}, soft morning light",
                "Serene nature scene featuring {subject}, peaceful atmosphere",
                "Stunning outdoor environment with {subject}, vibrant colors"
            ],
            "portrait": [
                "Professional portrait of {subject}, studio lighting, shallow depth of field",
                "Artistic portrait featuring {subject}, soft natural lighting",
                "Creative headshot of {subject}, professional photography style"
            ],
            "action": [
                "Dynamic action scene with {subject}, motion blur, high energy",
                "Fast-paced movement of {subject}, dramatic camera angle",
                "Intense action sequence featuring {subject}, cinematic motion"
            ],
            "abstract": [
                "Abstract artistic interpretation of {subject}, surreal atmosphere",
                "Creative abstract concept with {subject}, dream-like quality",
                "Surreal artistic vision of {subject}, imaginative composition"
            ]
        }
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load prompt history from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Could not load prompt history: {e}{Style.RESET_ALL}")
        return []
    
    def _save_history(self):
        """Save prompt history to file"""
        try:
            # Keep only last 100 entries
            self.history = self.history[-100:]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Could not save prompt history: {e}{Style.RESET_ALL}")
    
    def _load_favorites(self) -> List[Dict[str, Any]]:
        """Load favorite prompts from file"""
        try:
            if self.favorites_file.exists():
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Could not load favorites: {e}{Style.RESET_ALL}")
        return []
    
    def _save_favorites(self):
        """Save favorite prompts to file"""
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Could not save favorites: {e}{Style.RESET_ALL}")
    
    def save_prompt(self, prompt: str, model: str, success: bool = True, 
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """Save a prompt to history"""
        entry = {
            "prompt": prompt.strip(),
            "model": model,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Don't save duplicates from recent history (last 10 entries)
        recent_prompts = [h["prompt"] for h in self.history[-10:]]
        if prompt.strip() not in recent_prompts:
            self.history.append(entry)
            self._save_history()
    
    def get_recent_prompts(self, limit: int = 10, successful_only: bool = True) -> List[Dict[str, Any]]:
        """Get recent prompts from history"""
        filtered_history = self.history
        
        if successful_only:
            filtered_history = [h for h in self.history if h.get("success", True)]
        
        # Return most recent first
        return list(reversed(filtered_history[-limit:]))
    
    def search_history(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search prompt history by text"""
        query = query.lower().strip()
        if not query:
            return self.get_recent_prompts(limit)
        
        matches = []
        for entry in reversed(self.history):
            if query in entry["prompt"].lower():
                matches.append(entry)
                if len(matches) >= limit:
                    break
        
        return matches
    
    def add_to_favorites(self, prompt: str, name: Optional[str] = None, 
                        category: str = "general") -> bool:
        """Add a prompt to favorites"""
        try:
            # Check if already in favorites
            for fav in self.favorites:
                if fav["prompt"] == prompt.strip():
                    print(f"{Fore.YELLOW}Prompt already in favorites{Style.RESET_ALL}")
                    return False
            
            favorite = {
                "name": name or prompt[:50] + ("..." if len(prompt) > 50 else ""),
                "prompt": prompt.strip(),
                "category": category,
                "created": datetime.now().isoformat(),
                "usage_count": 0
            }
            
            self.favorites.append(favorite)
            self._save_favorites()
            print(f"{Fore.GREEN}✅ Added to favorites{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error adding to favorites: {e}{Style.RESET_ALL}")
            return False
    
    def remove_from_favorites(self, index: int) -> bool:
        """Remove a prompt from favorites by index"""
        try:
            if 0 <= index < len(self.favorites):
                removed = self.favorites.pop(index)
                self._save_favorites()
                print(f"{Fore.GREEN}✅ Removed '{removed['name']}' from favorites{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}❌ Invalid favorite index{Style.RESET_ALL}")
                return False
        except Exception as e:
            print(f"{Fore.RED}❌ Error removing favorite: {e}{Style.RESET_ALL}")
            return False
    
    def get_favorites(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get favorite prompts, optionally filtered by category"""
        favorites = self.favorites
        
        if category:
            favorites = [f for f in favorites if f.get("category", "general") == category]
        
        # Sort by usage count (descending) then by creation date (descending)
        return sorted(favorites, key=lambda x: (x.get("usage_count", 0), x.get("created", "")), reverse=True)
    
    def get_favorite_categories(self) -> List[str]:
        """Get all favorite categories"""
        categories = set()
        for fav in self.favorites:
            categories.add(fav.get("category", "general"))
        return sorted(list(categories))
    
    def use_favorite(self, index: int) -> Optional[str]:
        """Use a favorite prompt (increment usage count)"""
        try:
            if 0 <= index < len(self.favorites):
                favorite = self.favorites[index]
                favorite["usage_count"] = favorite.get("usage_count", 0) + 1
                favorite["last_used"] = datetime.now().isoformat()
                self._save_favorites()
                return favorite["prompt"]
            return None
        except Exception:
            return None
    
    def generate_template_prompt(self, template_type: str, subject: str = "") -> Optional[str]:
        """Generate a prompt from a template"""
        if template_type not in self.templates:
            return None
        
        import random
        template = random.choice(self.templates[template_type])
        
        if "{subject}" in template and subject:
            return template.format(subject=subject)
        elif "{subject}" in template:
            return template.replace("{subject}", "the subject")
        else:
            return template
    
    def suggest_improvements(self, prompt: str) -> List[str]:
        """Suggest improvements to a prompt"""
        suggestions = []
        prompt_lower = prompt.lower()
        
        # Check for common improvement opportunities
        if len(prompt) < 20:
            suggestions.append("Consider adding more descriptive details")
        
        if not any(word in prompt_lower for word in ["lighting", "light", "bright", "dark", "shadow"]):
            suggestions.append("Add lighting description (e.g., 'soft natural lighting', 'dramatic shadows')")
        
        if not any(word in prompt_lower for word in ["cinematic", "professional", "artistic", "beautiful", "stunning"]):
            suggestions.append("Consider adding style descriptors (e.g., 'cinematic', 'professional', 'artistic')")
        
        if not any(word in prompt_lower for word in ["detailed", "high quality", "4k", "hd"]):
            suggestions.append("Add quality indicators (e.g., 'highly detailed', 'high quality')")
        
        # Check for camera angles
        if not any(word in prompt_lower for word in ["close-up", "wide shot", "medium shot", "angle", "view"]):
            suggestions.append("Specify camera angle or shot type (e.g., 'close-up', 'wide angle shot')")
        
        return suggestions
    
    def get_quick_prompt(self) -> Optional[str]:
        """Interactive prompt selection for quick mode"""
        try:
            print(f"\n{Fore.CYAN}📝 Prompt Selection:{Style.RESET_ALL}")
            print("1. Enter new prompt")
            print("2. Use recent prompt")
            if self.favorites:
                print("3. Use favorite prompt")
            print("4. Generate from template")
            print("5. Cancel")
            
            choice = input(f"\n{Fore.YELLOW}Select option: {Style.RESET_ALL}").strip()
            
            if choice == "1":
                return self._get_new_prompt()
            elif choice == "2":
                return self._select_recent_prompt()
            elif choice == "3" and self.favorites:
                return self._select_favorite_prompt()
            elif choice == "4":
                return self._generate_template_prompt()
            else:
                return None
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Prompt selection cancelled{Style.RESET_ALL}")
            return None
    
    def _get_new_prompt(self) -> Optional[str]:
        """Get a new prompt from user input"""
        try:
            prompt = input(f"\n{Fore.CYAN}Enter your prompt: {Style.RESET_ALL}").strip()
            
            if not prompt:
                return None
            
            # Show suggestions
            suggestions = self.suggest_improvements(prompt)
            if suggestions:
                print(f"\n{Fore.YELLOW}💡 Suggestions to improve your prompt:{Style.RESET_ALL}")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"  {i}. {suggestion}")
                
                improve = input(f"\n{Fore.CYAN}Would you like to revise your prompt? (y/n): {Style.RESET_ALL}").strip().lower()
                if improve == 'y':
                    revised_prompt = input(f"{Fore.CYAN}Enter revised prompt: {Style.RESET_ALL}").strip()
                    if revised_prompt:
                        prompt = revised_prompt
            
            return prompt
            
        except KeyboardInterrupt:
            return None
    
    def _select_recent_prompt(self) -> Optional[str]:
        """Select from recent prompts"""
        recent = self.get_recent_prompts(10)
        
        if not recent:
            print(f"{Fore.YELLOW}No recent prompts found{Style.RESET_ALL}")
            return None
        
        print(f"\n{Fore.CYAN}Recent Prompts:{Style.RESET_ALL}")
        for i, entry in enumerate(recent, 1):
            # Truncate long prompts for display
            display_prompt = entry["prompt"][:60] + ("..." if len(entry["prompt"]) > 60 else "")
            timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%m/%d %H:%M")
            model = entry.get("model", "unknown")
            
            print(f"  {i}. {display_prompt}")
            print(f"     {Fore.GREEN}[{model}] {timestamp}{Style.RESET_ALL}")
        
        try:
            choice = input(f"\n{Fore.YELLOW}Select prompt (1-{len(recent)}) or Enter to cancel: {Style.RESET_ALL}").strip()
            if choice:
                idx = int(choice) - 1
                if 0 <= idx < len(recent):
                    return recent[idx]["prompt"]
        except ValueError:
            pass
        
        return None
    
    def _select_favorite_prompt(self) -> Optional[str]:
        """Select from favorite prompts"""
        favorites = self.get_favorites()
        
        if not favorites:
            print(f"{Fore.YELLOW}No favorite prompts found{Style.RESET_ALL}")
            return None
        
        print(f"\n{Fore.CYAN}Favorite Prompts:{Style.RESET_ALL}")
        for i, fav in enumerate(favorites, 1):
            usage = fav.get("usage_count", 0)
            category = fav.get("category", "general")
            
            print(f"  {i}. {fav['name']}")
            print(f"     {Fore.GREEN}[{category}] Used {usage} times{Style.RESET_ALL}")
        
        try:
            choice = input(f"\n{Fore.YELLOW}Select favorite (1-{len(favorites)}) or Enter to cancel: {Style.RESET_ALL}").strip()
            if choice:
                idx = int(choice) - 1
                if 0 <= idx < len(favorites):
                    return self.use_favorite(idx)
        except ValueError:
            pass
        
        return None
    
    def _generate_template_prompt(self) -> Optional[str]:
        """Generate prompt from template"""
        print(f"\n{Fore.CYAN}Template Categories:{Style.RESET_ALL}")
        categories = list(self.templates.keys())
        
        for i, category in enumerate(categories, 1):
            print(f"  {i}. {category.title()}")
        
        try:
            choice = input(f"\n{Fore.YELLOW}Select category (1-{len(categories)}) or Enter to cancel: {Style.RESET_ALL}").strip()
            if choice:
                idx = int(choice) - 1
                if 0 <= idx < len(categories):
                    category = categories[idx]
                    
                    subject = input(f"{Fore.CYAN}Enter subject (optional): {Style.RESET_ALL}").strip()
                    return self.generate_template_prompt(category, subject)
        except ValueError:
            pass
        
        return None
    
    def cleanup_old_history(self, days: int = 30):
        """Remove history entries older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        original_count = len(self.history)
        self.history = [
            entry for entry in self.history
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
        ]
        
        if len(self.history) < original_count:
            self._save_history()
            removed = original_count - len(self.history)
            print(f"{Fore.GREEN}✅ Cleaned up {removed} old history entries{Style.RESET_ALL}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get prompt usage statistics"""
        if not self.history:
            return {"total_prompts": 0, "success_rate": 0, "popular_models": []}
        
        total = len(self.history)
        successful = len([h for h in self.history if h.get("success", True)])
        success_rate = (successful / total) * 100 if total > 0 else 0
        
        # Count model usage
        model_counts = {}
        for entry in self.history:
            model = entry.get("model", "unknown")
            model_counts[model] = model_counts.get(model, 0) + 1
        
        popular_models = sorted(model_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "total_prompts": total,
            "successful_prompts": successful,
            "success_rate": success_rate,
            "popular_models": popular_models[:5],
            "total_favorites": len(self.favorites),
            "favorite_categories": len(self.get_favorite_categories())
        }

# Convenience functions
def get_quick_prompt() -> Optional[str]:
    """Quick prompt selection function"""
    manager = PromptManager()
    return manager.get_quick_prompt()

def save_prompt_result(prompt: str, model: str, success: bool = True):
    """Save prompt result to history"""
    manager = PromptManager()
    manager.save_prompt(prompt, model, success)

# Test function
if __name__ == "__main__":
    print("Testing Prompt Manager...")
    
    manager = PromptManager()
    
    # Test saving a prompt
    manager.save_prompt("Beautiful sunset over mountains", "kling_21_pro", True)
    
    # Test getting recent prompts
    recent = manager.get_recent_prompts(5)
    print(f"Recent prompts: {len(recent)}")
    
    # Test statistics
    stats = manager.get_stats()
    print(f"Stats: {stats}")
    
    print("Prompt Manager test completed.")