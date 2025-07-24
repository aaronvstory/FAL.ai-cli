#!/usr/bin/env python3
"""
Menu System Module - Questionnaire-style workflows
Provides guided experiences for different user types and scenarios
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from colorama import Fore, Style

class MenuSystem:
    """Advanced menu system with questionnaire-style workflows"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.workflows_file = self.data_dir / "workflow_templates.json"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create workflow templates
        self.workflows = self._load_workflow_templates()
        
        # User type classifications
        self.user_types = {
            "beginner": {
                "name": "Beginner",
                "description": "New to AI video generation",
                "workflow": "beginner_guided",
                "features": ["step_by_step", "explanations", "safe_defaults", "cost_warnings"]
            },
            "creator": {
                "name": "Content Creator",
                "description": "Creating content for social media, marketing, etc.",
                "workflow": "creator_focused",
                "features": ["batch_processing", "template_prompts", "format_presets", "trend_suggestions"]
            },
            "professional": {
                "name": "Professional",
                "description": "Professional video production and commercial use",
                "workflow": "professional_grade",
                "features": ["quality_priority", "advanced_parameters", "batch_operations", "cost_optimization"]
            },
            "developer": {
                "name": "Developer/Power User",
                "description": "Technical user who wants full control",
                "workflow": "advanced_control",
                "features": ["all_parameters", "cli_shortcuts", "automation", "technical_details"]
            },
            "experimenter": {
                "name": "AI Experimenter",
                "description": "Exploring AI capabilities and testing models",
                "workflow": "experimentation",
                "features": ["model_comparison", "parameter_testing", "quality_analysis", "cost_tracking"]
            }
        }
    
    def _load_workflow_templates(self) -> Dict[str, Any]:
        """Load workflow templates or create defaults"""
        try:
            if self.workflows_file.exists():
                with open(self.workflows_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Could not load workflow templates: {e}{Style.RESET_ALL}")
        
        # Create default workflow templates
        default_workflows = {
            "beginner_guided": {
                "name": "Beginner-Friendly Workflow",
                "description": "Step-by-step guidance for first-time users",
                "steps": [
                    {"type": "welcome", "title": "Welcome to AI Video Generation!"},
                    {"type": "safety_check", "title": "Let's ensure everything is set up"},
                    {"type": "use_case", "title": "What would you like to create?"},
                    {"type": "model_recommendation", "title": "Choosing the right model"},
                    {"type": "image_selection", "title": "Select your starting image"},
                    {"type": "prompt_guidance", "title": "Describe your vision"},
                    {"type": "parameter_simple", "title": "Basic settings"},
                    {"type": "cost_review", "title": "Cost confirmation"},
                    {"type": "generation", "title": "Creating your video"},
                    {"type": "result_explanation", "title": "Understanding your results"}
                ]
            },
            "creator_focused": {
                "name": "Content Creator Workflow",
                "description": "Optimized for social media and marketing content",
                "steps": [
                    {"type": "content_type", "title": "What type of content are you creating?"},
                    {"type": "platform_optimization", "title": "Which platform will this be for?"},
                    {"type": "batch_planning", "title": "Single video or batch creation?"},
                    {"type": "brand_consistency", "title": "Brand and style preferences"},
                    {"type": "quick_generation", "title": "Streamlined creation process"}
                ]
            },
            "professional_grade": {
                "name": "Professional Workflow",
                "description": "High-quality production with advanced controls",
                "steps": [
                    {"type": "project_brief", "title": "Project requirements and specifications"},
                    {"type": "quality_standards", "title": "Quality and technical requirements"},
                    {"type": "model_comparison", "title": "Model selection and optimization"},
                    {"type": "advanced_parameters", "title": "Fine-tuning generation parameters"},
                    {"type": "batch_optimization", "title": "Batch processing and efficiency"},
                    {"type": "quality_assurance", "title": "Review and validation process"}
                ]
            },
            "advanced_control": {
                "name": "Developer/Power User Workflow",
                "description": "Full control with technical options",
                "steps": [
                    {"type": "technical_requirements", "title": "Technical specifications"},
                    {"type": "model_analysis", "title": "Model comparison and selection"},
                    {"type": "parameter_customization", "title": "Advanced parameter control"},
                    {"type": "automation_setup", "title": "Automation and scripting options"},
                    {"type": "monitoring_setup", "title": "Performance monitoring and logging"}
                ]
            },
            "experimentation": {
                "name": "AI Experimentation Workflow",
                "description": "Testing and comparing AI models and parameters",
                "steps": [
                    {"type": "experiment_design", "title": "Experiment planning and objectives"},
                    {"type": "model_matrix", "title": "Model and parameter combinations"},
                    {"type": "controlled_testing", "title": "Systematic testing approach"},
                    {"type": "result_analysis", "title": "Performance analysis and comparison"},
                    {"type": "documentation", "title": "Results documentation and insights"}
                ]
            }
        }
        
        # Save default templates
        try:
            with open(self.workflows_file, 'w', encoding='utf-8') as f:
                json.dump(default_workflows, f, indent=2, ensure_ascii=False)
        except Exception:
            pass  # Fail silently if we can't save
        
        return default_workflows
    
    def detect_user_type(self) -> str:
        """Interactive user type detection"""
        print(f"\n{Fore.CYAN}🎯 Let's customize your experience!{Style.RESET_ALL}")
        print("Answer a few quick questions to get personalized recommendations.")
        print()
        
        # Question 1: Experience level
        print(f"{Fore.WHITE}1. How familiar are you with AI video generation?{Style.RESET_ALL}")
        print("   a) I'm completely new to this")
        print("   b) I've tried a few AI tools before")
        print("   c) I'm experienced with AI tools")
        print("   d) I'm a developer/technical expert")
        
        experience = input(f"\n{Fore.YELLOW}Your choice (a-d): {Style.RESET_ALL}").lower().strip()
        
        # Question 2: Primary use case
        print(f"\n{Fore.WHITE}2. What's your primary goal?{Style.RESET_ALL}")
        print("   a) Learn and explore AI capabilities")
        print("   b) Create content for social media/marketing")
        print("   c) Professional video production")
        print("   d) Testing and comparing AI models")
        print("   e) Personal creative projects")
        
        use_case = input(f"\n{Fore.YELLOW}Your choice (a-e): {Style.RESET_ALL}").lower().strip()
        
        # Question 3: Workflow preference
        print(f"\n{Fore.WHITE}3. How do you prefer to work?{Style.RESET_ALL}")
        print("   a) Guide me through everything step-by-step")
        print("   b) Show me efficient workflows for my use case")
        print("   c) Give me full control over all settings")
        print("   d) Help me compare and optimize results")
        
        workflow = input(f"\n{Fore.YELLOW}Your choice (a-d): {Style.RESET_ALL}").lower().strip()
        
        # Scoring logic
        scores = {
            "beginner": 0,
            "creator": 0,
            "professional": 0,
            "developer": 0,
            "experimenter": 0
        }
        
        # Experience level scoring
        if experience == 'a':
            scores["beginner"] += 3
        elif experience == 'b':
            scores["creator"] += 2
            scores["beginner"] += 1
        elif experience == 'c':
            scores["professional"] += 2
            scores["creator"] += 1
        elif experience == 'd':
            scores["developer"] += 3
        
        # Use case scoring
        if use_case == 'a':
            scores["beginner"] += 2
            scores["experimenter"] += 1
        elif use_case == 'b':
            scores["creator"] += 3
        elif use_case == 'c':
            scores["professional"] += 3
        elif use_case == 'd':
            scores["experimenter"] += 3
        elif use_case == 'e':
            scores["beginner"] += 1
            scores["creator"] += 1
        
        # Workflow preference scoring
        if workflow == 'a':
            scores["beginner"] += 3
        elif workflow == 'b':
            scores["creator"] += 2
            scores["professional"] += 1
        elif workflow == 'c':
            scores["developer"] += 3
            scores["professional"] += 1
        elif workflow == 'd':
            scores["experimenter"] += 3
        
        # Determine user type
        detected_type = max(scores, key=scores.get)
        
        # Show result
        user_info = self.user_types[detected_type]
        print(f"\n{Fore.GREEN}🎯 Based on your answers, you're a: {Fore.WHITE}{user_info['name']}{Style.RESET_ALL}")
        print(f"   {user_info['description']}")
        print()
        
        # Confirm or allow manual selection
        confirm = input(f"{Fore.CYAN}Does this sound right? (y/n): {Style.RESET_ALL}").lower().strip()
        
        if confirm != 'y':
            return self.manual_user_type_selection()
        
        return detected_type
    
    def manual_user_type_selection(self) -> str:
        """Manual user type selection"""
        print(f"\n{Fore.CYAN}👤 Select Your User Type:{Style.RESET_ALL}")
        
        type_list = list(self.user_types.items())
        for i, (key, info) in enumerate(type_list, 1):
            print(f"  {i}. {Fore.WHITE}{info['name']}{Style.RESET_ALL}")
            print(f"     {info['description']}")
        
        while True:
            try:
                choice = input(f"\n{Fore.YELLOW}Select type (1-{len(type_list)}): {Style.RESET_ALL}").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(type_list):
                    return type_list[idx][0]
                else:
                    print(f"{Fore.RED}Please enter a number between 1 and {len(type_list)}{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Please enter a valid number{Style.RESET_ALL}")
    
    def run_workflow(self, workflow_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run a specific workflow"""
        if workflow_name not in self.workflows:
            return {"error": f"Workflow '{workflow_name}' not found"}
        
        workflow = self.workflows[workflow_name]
        context = context or {}
        
        print(f"\n{Fore.MAGENTA}🚀 Starting: {workflow['name']}{Style.RESET_ALL}")
        print(f"   {workflow['description']}")
        print()
        
        results = {"workflow": workflow_name, "steps_completed": [], "context": context}
        
        for step in workflow["steps"]:
            step_result = self._execute_step(step, context)
            
            if step_result.get("skip_remaining"):
                break
            
            if step_result.get("cancel"):
                results["cancelled"] = True
                return results
            
            results["steps_completed"].append({
                "step": step,
                "result": step_result
            })
            
            # Update context with step results
            context.update(step_result.get("context_updates", {}))
        
        results["completed"] = True
        print(f"\n{Fore.GREEN}✅ Workflow completed successfully!{Style.RESET_ALL}")
        
        return results
    
    def _execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        step_type = step["type"]
        step_title = step["title"]
        
        print(f"\n{Fore.CYAN}📋 {step_title}{Style.RESET_ALL}")
        
        # Route to appropriate step handler
        handlers = {
            "welcome": self._step_welcome,
            "safety_check": self._step_safety_check,
            "use_case": self._step_use_case,
            "model_recommendation": self._step_model_recommendation,
            "image_selection": self._step_image_selection,
            "prompt_guidance": self._step_prompt_guidance,
            "parameter_simple": self._step_parameter_simple,
            "cost_review": self._step_cost_review,
            "generation": self._step_generation,
            "result_explanation": self._step_result_explanation,
            "content_type": self._step_content_type,
            "platform_optimization": self._step_platform_optimization,
            "batch_planning": self._step_batch_planning,
            "brand_consistency": self._step_brand_consistency,
            "quick_generation": self._step_quick_generation,
            "project_brief": self._step_project_brief,
            "quality_standards": self._step_quality_standards,
            "model_comparison": self._step_model_comparison,
            "advanced_parameters": self._step_advanced_parameters,
            "batch_optimization": self._step_batch_optimization,
            "quality_assurance": self._step_quality_assurance,
            "technical_requirements": self._step_technical_requirements,
            "model_analysis": self._step_model_analysis,
            "parameter_customization": self._step_parameter_customization,
            "automation_setup": self._step_automation_setup,
            "monitoring_setup": self._step_monitoring_setup,
            "experiment_design": self._step_experiment_design,
            "model_matrix": self._step_model_matrix,
            "controlled_testing": self._step_controlled_testing,
            "result_analysis": self._step_result_analysis,
            "documentation": self._step_documentation
        }
        
        handler = handlers.get(step_type, self._step_generic)
        
        try:
            return handler(step, context)
        except KeyboardInterrupt:
            return {"cancel": True}
        except Exception as e:
            print(f"{Fore.RED}❌ Error in step: {e}{Style.RESET_ALL}")
            return {"error": str(e)}
    
    # Step handler implementations
    def _step_welcome(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Welcome step for beginners"""
        print("Welcome to the FAL.AI Video Generator! 🎬")
        print()
        print("This tool helps you create amazing videos from still images using AI.")
        print("Don't worry if you're new to this - I'll guide you through every step!")
        print()
        print(f"{Fore.GREEN}💡 Pro tip:{Style.RESET_ALL} You can press Ctrl+C at any time to cancel and return to the main menu.")
        
        input(f"\n{Fore.YELLOW}Press Enter when you're ready to continue...{Style.RESET_ALL}")
        
        return {"completed": True}
    
    def _step_safety_check(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Safety and setup check"""
        print("Let's make sure everything is ready:")
        print()
        
        checks = []
        
        # Check API key
        import os
        if os.getenv("FAL_KEY"):
            print(f"✅ {Fore.GREEN}API Key: Configured{Style.RESET_ALL}")
            checks.append(True)
        else:
            print(f"❌ {Fore.RED}API Key: Not set{Style.RESET_ALL}")
            print("   You'll need to set your FAL_KEY environment variable")
            checks.append(False)
        
        # Check GUI support
        try:
            import tkinter
            print(f"✅ {Fore.GREEN}File Picker: Available{Style.RESET_ALL}")
            checks.append(True)
        except ImportError:
            print(f"⚠️ {Fore.YELLOW}File Picker: Manual input only{Style.RESET_ALL}")
            checks.append(True)  # Not critical
        
        # Check dependencies
        try:
            import requests
            import PIL
            print(f"✅ {Fore.GREEN}Dependencies: All good{Style.RESET_ALL}")
            checks.append(True)
        except ImportError:
            print(f"❌ {Fore.RED}Dependencies: Missing packages{Style.RESET_ALL}")
            checks.append(False)
        
        all_good = all(checks)
        
        if not all_good:
            print(f"\n{Fore.YELLOW}Some issues were found. You can continue, but some features may not work properly.{Style.RESET_ALL}")
            proceed = input(f"Continue anyway? (y/n): {Style.RESET_ALL}").lower().strip()
            if proceed != 'y':
                return {"cancel": True}
        
        return {"completed": True, "context_updates": {"safety_checks_passed": all_good}}
    
    def _step_use_case(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine user's specific use case"""
        print("What would you like to create today?")
        print()
        
        use_cases = [
            ("social_media", "Social media content (Instagram, TikTok, etc.)"),
            ("marketing", "Marketing or promotional video"),
            ("personal", "Personal creative project"),
            ("presentation", "Business presentation or demo"),
            ("art", "Artistic or experimental video"),
            ("other", "Something else")
        ]
        
        for i, (key, desc) in enumerate(use_cases, 1):
            print(f"  {i}. {desc}")
        
        while True:
            try:
                choice = input(f"\n{Fore.YELLOW}Select your use case (1-{len(use_cases)}): {Style.RESET_ALL}").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(use_cases):
                    selected_use_case = use_cases[idx][0]
                    break
                else:
                    print(f"{Fore.RED}Please enter a number between 1 and {len(use_cases)}{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Please enter a valid number{Style.RESET_ALL}")
        
        # Provide use case specific tips
        tips = {
            "social_media": "📱 For social media, consider vertical (9:16) aspect ratio and shorter durations (5s) for better engagement.",
            "marketing": "🎯 Marketing videos benefit from clear, professional visuals. Consider horizontal (16:9) format.",
            "personal": "🎨 Personal projects are great for experimenting! Try different styles and models.",
            "presentation": "📊 Business presentations work well with horizontal format and subtle, professional animations.",
            "art": "🎭 Artistic projects are perfect for trying premium models and creative prompts.",
            "other": "💡 Feel free to experiment with different settings to find what works best for your project."
        }
        
        print(f"\n{Fore.GREEN}💡 Tip:{Style.RESET_ALL} {tips.get(selected_use_case, tips['other'])}")
        
        return {"completed": True, "context_updates": {"use_case": selected_use_case}}
    
    def _step_model_recommendation(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend appropriate model based on use case"""
        use_case = context.get("use_case", "personal")
        
        print("Based on your use case, here are my recommendations:")
        print()
        
        # Model recommendations by use case
        recommendations = {
            "social_media": [
                ("kling_21_standard", "Best value for social media content", "⭐⭐⭐"),
                ("haiper_20", "Budget-friendly option for high volume", "💰"),
                ("kling_21_pro", "Higher quality for important posts", "✨")
            ],
            "marketing": [
                ("kling_21_pro", "Professional quality for marketing", "⭐⭐⭐"),
                ("kling_21_standard", "Good quality, cost-effective", "💰"),
                ("kling_21_master", "Premium quality for key campaigns", "👑")
            ],
            "personal": [
                ("kling_21_standard", "Great starting point", "⭐⭐⭐"),
                ("kling_21_pro", "Step up in quality", "✨"),
                ("haiper_20", "Budget-friendly experimentation", "💰")
            ],
            "presentation": [
                ("kling_21_pro", "Professional and reliable", "⭐⭐⭐"),
                ("kling_21_standard", "Good quality for internal use", "💰"),
                ("kling_21_master", "Premium for important presentations", "👑")
            ],
            "art": [
                ("kling_21_master", "Highest quality for artistic work", "⭐⭐⭐"),
                ("kling_21_pro", "Great quality with good value", "✨"),
                ("luma_dream", "Alternative engine for different styles", "🎨")
            ]
        }
        
        recs = recommendations.get(use_case, recommendations["personal"])
        
        for i, (model, desc, icon) in enumerate(recs, 1):
            print(f"  {i}. {icon} {model.replace('_', ' ').title()}")
            print(f"     {desc}")
        
        print(f"  {len(recs) + 1}. 🔍 See all models and compare")
        
        while True:
            try:
                choice = input(f"\n{Fore.YELLOW}Select model (1-{len(recs) + 1}): {Style.RESET_ALL}").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(recs):
                    selected_model = recs[idx][0]
                    break
                elif idx == len(recs):
                    return {"skip_remaining": True, "context_updates": {"show_model_comparison": True}}
                else:
                    print(f"{Fore.RED}Please enter a number between 1 and {len(recs) + 1}{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Please enter a valid number{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}✅ Selected: {selected_model.replace('_', ' ').title()}{Style.RESET_ALL}")
        
        return {"completed": True, "context_updates": {"selected_model": selected_model}}
    
    def _step_generic(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generic step handler for unimplemented steps"""
        step_type = step.get("type", "unknown")
        print(f"This step ({step_type}) is under development.")
        print("Skipping to next step...")
        
        return {"completed": True, "placeholder": True}
    
    # Placeholder implementations for other steps
    def _step_image_selection(self, step, context): return self._step_generic(step, context)
    def _step_prompt_guidance(self, step, context): return self._step_generic(step, context)
    def _step_parameter_simple(self, step, context): return self._step_generic(step, context)
    def _step_cost_review(self, step, context): return self._step_generic(step, context)
    def _step_generation(self, step, context): return self._step_generic(step, context)
    def _step_result_explanation(self, step, context): return self._step_generic(step, context)
    def _step_content_type(self, step, context): return self._step_generic(step, context)
    def _step_platform_optimization(self, step, context): return self._step_generic(step, context)
    def _step_batch_planning(self, step, context): return self._step_generic(step, context)
    def _step_brand_consistency(self, step, context): return self._step_generic(step, context)
    def _step_quick_generation(self, step, context): return self._step_generic(step, context)
    def _step_project_brief(self, step, context): return self._step_generic(step, context)
    def _step_quality_standards(self, step, context): return self._step_generic(step, context)
    def _step_model_comparison(self, step, context): return self._step_generic(step, context)
    def _step_advanced_parameters(self, step, context): return self._step_generic(step, context)
    def _step_batch_optimization(self, step, context): return self._step_generic(step, context)
    def _step_quality_assurance(self, step, context): return self._step_generic(step, context)
    def _step_technical_requirements(self, step, context): return self._step_generic(step, context)
    def _step_model_analysis(self, step, context): return self._step_generic(step, context)
    def _step_parameter_customization(self, step, context): return self._step_generic(step, context)
    def _step_automation_setup(self, step, context): return self._step_generic(step, context)
    def _step_monitoring_setup(self, step, context): return self._step_generic(step, context)
    def _step_experiment_design(self, step, context): return self._step_generic(step, context)
    def _step_model_matrix(self, step, context): return self._step_generic(step, context)
    def _step_controlled_testing(self, step, context): return self._step_generic(step, context)
    def _step_result_analysis(self, step, context): return self._step_generic(step, context)
    def _step_documentation(self, step, context): return self._step_generic(step, context)
    
    def get_quick_workflow(self, user_type: str) -> str:
        """Get the recommended workflow for a user type"""
        return self.user_types.get(user_type, {}).get("workflow", "beginner_guided")
    
    def run_user_type_workflow(self, user_type: str = None) -> Dict[str, Any]:
        """Run workflow for a specific user type"""
        if not user_type:
            user_type = self.detect_user_type()
        
        workflow_name = self.get_quick_workflow(user_type)
        
        print(f"\n{Fore.GREEN}🎯 Running {self.user_types[user_type]['name']} workflow{Style.RESET_ALL}")
        
        return self.run_workflow(workflow_name, {"user_type": user_type})

# Convenience functions
def detect_user_type() -> str:
    """Quick user type detection"""
    menu_system = MenuSystem()
    return menu_system.detect_user_type()

def run_beginner_workflow() -> Dict[str, Any]:
    """Quick beginner workflow"""
    menu_system = MenuSystem()
    return menu_system.run_user_type_workflow("beginner")

def run_workflow_for_user_type(user_type: str) -> Dict[str, Any]:
    """Run workflow for specific user type"""
    menu_system = MenuSystem()
    return menu_system.run_user_type_workflow(user_type)

# Test function
if __name__ == "__main__":
    print("Testing Menu System...")
    
    menu_system = MenuSystem()
    
    # Test user type detection
    print("Testing user type detection...")
    # user_type = menu_system.detect_user_type()
    # print(f"Detected user type: {user_type}")
    
    # Test workflow execution
    print("Testing beginner workflow...")
    # result = menu_system.run_user_type_workflow("beginner")
    # print(f"Workflow result: {result}")
    
    print("Menu System test completed.")