#!/usr/bin/env python3
"""
Cost Calculator Module - Real-time FAL.AI pricing and budget management
Provides cost estimation, budget tracking, and spending alerts
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from colorama import Fore, Style

class CostCalculator:
    """Real-time cost calculation and budget management"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.budget_file = self.data_dir / "budget_tracking.json"
        
        # Create data directory if needed
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Model pricing database (updated with latest FAL.AI pricing)
        self.model_pricing = {
            "kling_21_standard": {
                "name": "Kling 2.1 Standard",
                "cost_5s": 0.25,
                "cost_10s": 0.50,
                "cost_per_second": 0.05,
                "max_duration": 10,
                "tier": "Standard",
                "quality": "High",
                "efficiency_score": 9.5  # Quality/Cost ratio
            },
            "kling_21_pro": {
                "name": "Kling 2.1 Pro",
                "cost_5s": 0.45,
                "cost_10s": 0.90,
                "cost_per_second": 0.09,
                "max_duration": 10,
                "tier": "Professional",
                "quality": "Premium",
                "efficiency_score": 8.8
            },
            "kling_21_master": {
                "name": "Kling 2.1 Master",
                "cost_5s": 0.70,
                "cost_10s": 1.40,
                "cost_per_second": 0.14,
                "max_duration": 10,
                "tier": "Premium",
                "quality": "Ultra",
                "efficiency_score": 7.5
            },
            "kling_20_master": {
                "name": "Kling 2.0 Master",
                "cost_5s": 1.40,
                "cost_10s": 2.80,
                "cost_per_second": 0.28,
                "max_duration": 10,
                "tier": "Legacy Premium",
                "quality": "Premium",
                "efficiency_score": 6.0
            },
            "kling_16_pro": {
                "name": "Kling 1.6 Pro",
                "cost_5s": 0.475,
                "cost_10s": 0.95,
                "cost_per_second": 0.095,
                "max_duration": 10,
                "tier": "Legacy",
                "quality": "Good",
                "efficiency_score": 7.2
            },
            "luma_dream": {
                "name": "Luma Dream Machine",
                "cost_5s": 0.50,
                "cost_10s": 0.90,
                "cost_per_second": 0.10,
                "max_duration": 9,
                "tier": "Alternative",
                "quality": "High",
                "efficiency_score": 8.0
            },
            "haiper_20": {
                "name": "Haiper 2.0",
                "cost_5s": 0.20,
                "cost_10s": 0.40,
                "cost_per_second": 0.04,
                "max_duration": 10,
                "tier": "Budget",
                "quality": "Good",
                "efficiency_score": 9.8
            }
        }
        
        # Load budget tracking data
        self.budget_data = self._load_budget_data()
    
    def _load_budget_data(self) -> Dict[str, Any]:
        """Load budget tracking data"""
        try:
            if self.budget_file.exists():
                with open(self.budget_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Could not load budget data: {e}{Style.RESET_ALL}")
        
        return {
            "monthly_budget": 0.0,
            "current_month_spending": 0.0,
            "total_spending": 0.0,
            "spending_history": [],
            "budget_alerts": True,
            "cost_warnings": True,
            "last_reset": datetime.now().strftime("%Y-%m")
        }
    
    def _save_budget_data(self):
        """Save budget tracking data"""
        try:
            with open(self.budget_file, 'w') as f:
                json.dump(self.budget_data, f, indent=2)
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Could not save budget data: {e}{Style.RESET_ALL}")
    
    def calculate_cost(self, model: str, duration: int = 5) -> Dict[str, Any]:
        """Calculate cost for a specific model and duration"""
        if model not in self.model_pricing:
            return {
                "error": f"Unknown model: {model}",
                "cost": 0.0,
                "model": model,
                "duration": duration
            }
        
        model_info = self.model_pricing[model]
        cost_per_second = model_info["cost_per_second"]
        
        # Ensure duration doesn't exceed model limits
        max_duration = model_info["max_duration"]
        actual_duration = min(duration, max_duration)
        
        if duration > max_duration:
            duration_warning = f"Duration capped at {max_duration}s (model limit)"
        else:
            duration_warning = None
        
        total_cost = cost_per_second * actual_duration
        
        return {
            "model": model,
            "model_name": model_info["name"],
            "duration": actual_duration,
            "cost_per_second": cost_per_second,
            "total_cost": total_cost,
            "tier": model_info["tier"],
            "quality": model_info["quality"],
            "efficiency_score": model_info["efficiency_score"],
            "duration_warning": duration_warning,
            "cost_breakdown": {
                "base_cost": total_cost,
                "duration_cost": f"${cost_per_second:.3f} × {actual_duration}s",
                "formatted_cost": f"${total_cost:.3f}"
            }
        }
    
    def calculate_batch_cost(self, model: str, file_count: int, duration: int = 5) -> Dict[str, Any]:
        """Calculate cost for batch processing multiple files"""
        single_cost = self.calculate_cost(model, duration)
        
        if "error" in single_cost:
            return single_cost
        
        total_cost = single_cost["total_cost"] * file_count
        
        # Apply batch discounts (hypothetical - FAL.AI doesn't offer these yet)
        discount_rate = 0.0
        if file_count >= 10:
            discount_rate = 0.05  # 5% for 10+ files
        elif file_count >= 5:
            discount_rate = 0.02  # 2% for 5+ files
        
        discount_amount = total_cost * discount_rate
        final_cost = total_cost - discount_amount
        
        return {
            **single_cost,
            "file_count": file_count,
            "single_file_cost": single_cost["total_cost"],
            "subtotal": total_cost,
            "discount_rate": discount_rate,
            "discount_amount": discount_amount,
            "total_batch_cost": final_cost,
            "average_per_file": final_cost / file_count,
            "savings": discount_amount,
            "cost_breakdown": {
                "per_file": f"${single_cost['total_cost']:.3f}",
                "subtotal": f"${total_cost:.3f}",
                "discount": f"-${discount_amount:.3f}" if discount_amount > 0 else None,
                "total": f"${final_cost:.3f}"
            }
        }
    
    def compare_models(self, duration: int = 5) -> List[Dict[str, Any]]:
        """Compare costs across all models"""
        comparisons = []
        
        for model_key in self.model_pricing.keys():
            cost_info = self.calculate_cost(model_key, duration)
            if "error" not in cost_info:
                comparisons.append(cost_info)
        
        # Sort by cost (cheapest first)
        comparisons.sort(key=lambda x: x["total_cost"])
        
        # Add value rankings
        for i, comparison in enumerate(comparisons):
            comparison["cost_rank"] = i + 1
            comparison["value_score"] = comparison["efficiency_score"]
            
            # Calculate cost per quality point
            quality_scores = {"Good": 7, "High": 8, "Premium": 9, "Ultra": 10}
            quality_score = quality_scores.get(comparison["quality"], 7)
            comparison["cost_per_quality"] = comparison["total_cost"] / quality_score
        
        return comparisons
    
    def get_model_recommendations(self, duration: int = 5, budget_limit: Optional[float] = None,
                                quality_preference: str = "balanced") -> List[Dict[str, Any]]:
        """Get model recommendations based on preferences"""
        comparisons = self.compare_models(duration)
        
        # Filter by budget if specified
        if budget_limit:
            comparisons = [c for c in comparisons if c["total_cost"] <= budget_limit]
        
        recommendations = []
        
        if quality_preference == "budget":
            # Sort by lowest cost
            recommendations = sorted(comparisons, key=lambda x: x["total_cost"])[:3]
            recommendation_reason = "Lowest cost options"
            
        elif quality_preference == "premium":
            # Sort by quality, then by cost
            quality_order = {"Ultra": 4, "Premium": 3, "High": 2, "Good": 1}
            recommendations = sorted(comparisons, 
                                   key=lambda x: (quality_order.get(x["quality"], 0), -x["total_cost"]), 
                                   reverse=True)[:3]
            recommendation_reason = "Highest quality options"
            
        else:  # balanced
            # Sort by efficiency score (quality/cost ratio)
            recommendations = sorted(comparisons, key=lambda x: x["efficiency_score"], reverse=True)[:3]
            recommendation_reason = "Best value for money"
        
        return {
            "recommendations": recommendations,
            "reason": recommendation_reason,
            "total_options": len(comparisons),
            "budget_limit": budget_limit,
            "quality_preference": quality_preference
        }
    
    def track_spending(self, model: str, cost: float, description: str = ""):
        """Track spending and update budget"""
        current_month = datetime.now().strftime("%Y-%m")
        
        # Reset monthly spending if new month
        if self.budget_data["last_reset"] != current_month:
            self.budget_data["current_month_spending"] = 0.0
            self.budget_data["last_reset"] = current_month
        
        # Add to spending
        self.budget_data["current_month_spending"] += cost
        self.budget_data["total_spending"] += cost
        
        # Add to history
        spending_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "cost": cost,
            "description": description,
            "month": current_month
        }
        
        self.budget_data["spending_history"].append(spending_entry)
        
        # Keep only last 100 entries
        self.budget_data["spending_history"] = self.budget_data["spending_history"][-100:]
        
        self._save_budget_data()
        
        # Check for budget alerts
        self._check_budget_alerts(cost)
    
    def _check_budget_alerts(self, new_cost: float):
        """Check if spending triggers any alerts"""
        if not self.budget_data["budget_alerts"]:
            return
        
        monthly_budget = self.budget_data["monthly_budget"]
        current_spending = self.budget_data["current_month_spending"]
        
        if monthly_budget > 0:
            usage_percentage = (current_spending / monthly_budget) * 100
            
            if usage_percentage >= 100:
                print(f"{Fore.RED}🚨 BUDGET ALERT: You've exceeded your monthly budget!{Style.RESET_ALL}")
                print(f"   Spent: ${current_spending:.2f} / Budget: ${monthly_budget:.2f}")
            elif usage_percentage >= 90:
                print(f"{Fore.YELLOW}⚠️ BUDGET WARNING: 90% of monthly budget used{Style.RESET_ALL}")
                print(f"   Spent: ${current_spending:.2f} / Budget: ${monthly_budget:.2f}")
            elif usage_percentage >= 75:
                print(f"{Fore.YELLOW}💡 Budget Notice: 75% of monthly budget used{Style.RESET_ALL}")
    
    def set_monthly_budget(self, budget: float):
        """Set monthly spending budget"""
        self.budget_data["monthly_budget"] = budget
        self._save_budget_data()
        print(f"{Fore.GREEN}✅ Monthly budget set to ${budget:.2f}{Style.RESET_ALL}")
    
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status"""
        current_month = datetime.now().strftime("%Y-%m")
        monthly_budget = self.budget_data["monthly_budget"]
        current_spending = self.budget_data["current_month_spending"]
        
        # Calculate this month's spending if needed
        if self.budget_data["last_reset"] != current_month:
            current_spending = 0.0
        
        remaining_budget = max(0, monthly_budget - current_spending) if monthly_budget > 0 else None
        usage_percentage = (current_spending / monthly_budget * 100) if monthly_budget > 0 else 0
        
        # Get spending by model this month
        this_month_history = [
            entry for entry in self.budget_data["spending_history"]
            if entry.get("month") == current_month
        ]
        
        model_spending = {}
        for entry in this_month_history:
            model = entry["model"]
            model_spending[model] = model_spending.get(model, 0) + entry["cost"]
        
        return {
            "current_month": current_month,
            "monthly_budget": monthly_budget,
            "current_spending": current_spending,
            "remaining_budget": remaining_budget,
            "usage_percentage": usage_percentage,
            "total_lifetime_spending": self.budget_data["total_spending"],
            "model_spending": dict(sorted(model_spending.items(), key=lambda x: x[1], reverse=True)),
            "spending_entries_this_month": len(this_month_history),
            "budget_status": self._get_budget_status_message(usage_percentage)
        }
    
    def _get_budget_status_message(self, usage_percentage: float) -> Dict[str, str]:
        """Get budget status message with color coding"""
        if usage_percentage >= 100:
            return {"message": "Over Budget", "color": "red", "icon": "🚨"}
        elif usage_percentage >= 90:
            return {"message": "Budget Warning", "color": "yellow", "icon": "⚠️"}
        elif usage_percentage >= 75:
            return {"message": "Budget Caution", "color": "yellow", "icon": "💡"}
        elif usage_percentage >= 50:
            return {"message": "On Track", "color": "green", "icon": "✅"}
        else:
            return {"message": "Well Under Budget", "color": "green", "icon": "💰"}
    
    def estimate_monthly_cost(self, generations_per_day: int, model: str, duration: int = 5) -> Dict[str, Any]:
        """Estimate monthly cost based on usage patterns"""
        daily_cost = self.calculate_cost(model, duration)["total_cost"] * generations_per_day
        weekly_cost = daily_cost * 7
        monthly_cost = daily_cost * 30
        
        return {
            "model": model,
            "generations_per_day": generations_per_day,
            "duration": duration,
            "daily_cost": daily_cost,
            "weekly_cost": weekly_cost,
            "monthly_cost": monthly_cost,
            "cost_breakdown": {
                "per_generation": f"${self.calculate_cost(model, duration)['total_cost']:.3f}",
                "daily": f"${daily_cost:.2f}",
                "weekly": f"${weekly_cost:.2f}",
                "monthly": f"${monthly_cost:.2f}"
            }
        }
    
    def show_cost_comparison_table(self, duration: int = 5):
        """Display a formatted cost comparison table"""
        comparisons = self.compare_models(duration)
        
        print(f"\n{Fore.CYAN}💰 Cost Comparison Table ({duration}s duration):{Style.RESET_ALL}")
        print(f"{'Model':<25} {'Tier':<12} {'Quality':<8} {'Cost':<8} {'Value':<6} {'Rank'}")
        print(f"{'-' * 25} {'-' * 12} {'-' * 8} {'-' * 8} {'-' * 6} {'-' * 4}")
        
        for comparison in comparisons:
            name = comparison["model_name"][:24]
            tier = comparison["tier"][:11]
            quality = comparison["quality"][:7]
            cost = f"${comparison['total_cost']:.3f}"
            value = f"{comparison['efficiency_score']:.1f}"
            rank = str(comparison["cost_rank"])
            
            # Color coding by cost rank
            if comparison["cost_rank"] <= 2:
                color = Fore.GREEN  # Cheapest
            elif comparison["cost_rank"] <= 4:
                color = Fore.YELLOW  # Medium
            else:
                color = Fore.RED  # Most expensive
            
            print(f"{color}{name:<25} {tier:<12} {quality:<8} {cost:<8} {value:<6} {rank}{Style.RESET_ALL}")
        
        print()
    
    def get_spending_insights(self, days: int = 30) -> Dict[str, Any]:
        """Get spending insights and patterns"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_spending = [
            entry for entry in self.budget_data["spending_history"]
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
        ]
        
        if not recent_spending:
            return {"message": "No spending data available for the specified period"}
        
        total_spent = sum(entry["cost"] for entry in recent_spending)
        avg_per_generation = total_spent / len(recent_spending)
        
        # Most used models
        model_usage = {}
        for entry in recent_spending:
            model = entry["model"]
            model_usage[model] = model_usage.get(model, {"count": 0, "cost": 0.0})
            model_usage[model]["count"] += 1
            model_usage[model]["cost"] += entry["cost"]
        
        most_used = sorted(model_usage.items(), key=lambda x: x[1]["count"], reverse=True)
        most_expensive = sorted(model_usage.items(), key=lambda x: x[1]["cost"], reverse=True)
        
        # Spending trend
        daily_spending = {}
        for entry in recent_spending:
            date = entry["timestamp"][:10]  # YYYY-MM-DD
            daily_spending[date] = daily_spending.get(date, 0) + entry["cost"]
        
        avg_daily_spending = sum(daily_spending.values()) / len(daily_spending) if daily_spending else 0
        
        return {
            "period_days": days,
            "total_generations": len(recent_spending),
            "total_spent": total_spent,
            "average_per_generation": avg_per_generation,
            "average_daily_spending": avg_daily_spending,
            "most_used_models": most_used[:3],
            "most_expensive_models": most_expensive[:3],
            "daily_spending_data": daily_spending,
            "spending_trend": "increasing" if len(daily_spending) > 1 and 
                           list(daily_spending.values())[-1] > list(daily_spending.values())[0] else "stable"
        }

# Convenience functions
def calculate_cost(model: str, duration: int = 5) -> Dict[str, Any]:
    """Quick cost calculation"""
    calculator = CostCalculator()
    return calculator.calculate_cost(model, duration)

def compare_models(duration: int = 5) -> List[Dict[str, Any]]:
    """Quick model comparison"""
    calculator = CostCalculator()
    return calculator.compare_models(duration)

def get_recommendations(duration: int = 5, budget_limit: Optional[float] = None,
                       quality_preference: str = "balanced") -> List[Dict[str, Any]]:
    """Quick recommendations"""
    calculator = CostCalculator()
    return calculator.get_model_recommendations(duration, budget_limit, quality_preference)

# Test function
if __name__ == "__main__":
    print("Testing Cost Calculator...")
    
    calculator = CostCalculator()
    
    # Test single cost calculation
    cost_info = calculator.calculate_cost("kling_21_pro", 5)
    print(f"Kling 2.1 Pro (5s): ${cost_info['total_cost']:.3f}")
    
    # Test batch cost calculation
    batch_info = calculator.calculate_batch_cost("kling_21_standard", 10, 5)
    print(f"Batch 10 files: ${batch_info['total_batch_cost']:.2f}")
    
    # Test model comparison
    print("\nModel Comparison:")
    calculator.show_cost_comparison_table(5)
    
    # Test recommendations
    recommendations = calculator.get_model_recommendations(5, budget_limit=1.0)
    print(f"Recommendations under $1.00: {len(recommendations['recommendations'])} options")
    
    print("Cost Calculator test completed.")