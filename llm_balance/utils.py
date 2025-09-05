"""
Utility functions for balance checking
"""

import json
from typing import Dict, Any, List, Union
from pathlib import Path
import os

def get_nested_value(data: Dict[str, Any], path: List[str]) -> Any:
    """Get nested value from dictionary using path"""
    current = data
    for key in path:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current

def get_exchange_rates() -> Dict[str, float]:
    """Get exchange rates with simple default values"""
    # Default exchange rates (to CNY)
    default_rates = {
        'CNY': 1.0,
        'USD': 7.2,
        'EUR': 7.8,
        'GBP': 9.1,
        'JPY': 0.048,
        'KRW': 0.0054,
        'Points': 0.01  # for platform-specific points
    }
    
    # Allow override via environment variable
    rates_env = os.getenv('LLM_BALANCE_RATES')
    if rates_env:
        try:
            custom_rates = json.loads(rates_env)
            default_rates.update(custom_rates)
        except:
            pass  # Use default if parsing fails
    
    return default_rates

def convert_currency(amount: float, from_currency: str, to_currency: str = 'CNY') -> float:
    """Convert amount from one currency to another using exchange rates"""
    if from_currency == to_currency:
        return amount
    
    rates = get_exchange_rates()
    
    # Convert to CNY first, then to target currency
    from_rate = rates.get(from_currency, 1.0)
    to_rate = rates.get(to_currency, 1.0)
    
    # Convert: amount * (from_currency / CNY) * (CNY / to_currency)
    return amount * (from_rate / to_rate)

def get_available_currencies() -> List[str]:
    """Get list of available currencies"""
    rates = get_exchange_rates()
    return sorted(rates.keys())

def _clean_for_json(obj):
    """Clean object for JSON serialization"""
    if isinstance(obj, dict):
        return {k: _clean_for_json(v) for k, v in obj.items() if not k.startswith('_')}
    elif isinstance(obj, list):
        return [_clean_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Convert object to dict, skipping private attributes
        return {k: _clean_for_json(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
    elif isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    else:
        # For other objects, convert to string
        return str(obj)

def format_output(balances: List[Dict[str, Any]], format_type: str = 'table', target_currency: str = 'CNY') -> str:
    """Format balance output in different formats"""
    if not balances:
        return "No balance data available"
    
    if format_type == 'json':
        # Clean data for JSON serialization
        clean_balances = _clean_for_json(balances)
        return json.dumps(clean_balances, indent=2, ensure_ascii=False)
    
    elif format_type == 'markdown':
        return _format_markdown(balances)
    
    elif format_type == 'total':
        return _format_total(balances, target_currency)
    
    else:  # table format
        return _format_table(balances, target_currency)

def _format_table(balances: List[Dict[str, Any]], target_currency: str = 'CNY') -> str:
    """Format as text table"""
    lines = []
    lines.append("=" * 80)
    
    # Check if this is token data or balance data
    is_tokens = any('tokens' in balance for balance in balances)
    has_spent = any('spent' in balance for balance in balances)
    
    if is_tokens:
        lines.append(f"{'Platform':<20} {'Tokens':<15} {'Currency':<10}")
    elif has_spent:
        lines.append(f"{'Platform':<20} {'Balance':<15} {'Spent':<15} {'Currency':<10}")
    else:
        lines.append(f"{'Platform':<20} {'Balance':<15} {'Currency':<10}")
    
    lines.append("-" * 80)
    
    total = 0
    total_spent = 0
    for balance in balances:
        platform = balance['platform']
        
        # Handle both balance and token data
        if 'tokens' in balance:
            amount = balance['tokens']
            currency = balance['currency']
            has_spent = False
        else:
            amount = balance.get('balance', 0)
            currency = balance['currency']
            spent = balance.get('spent', 0)
            has_spent = 'spent' in balance
        
        # Ensure amount is a number
        try:
            amount_float = float(amount) if amount is not None else 0.0
        except (ValueError, TypeError):
            amount_float = 0.0
            
        # Ensure spent is a number or handle "-" string
        if spent == "-" or spent is None:
            spent_display = "-"
            spent_float = 0.0
        else:
            try:
                spent_float = float(spent)
                spent_display = f"{spent_float:.2f}"
            except (ValueError, TypeError):
                spent_display = "-"
                spent_float = 0.0
        
        if is_tokens:
            lines.append(f"{platform:<20} {amount_float:<15.2f} {currency:<10}")
        elif has_spent:
            lines.append(f"{platform:<20} {amount_float:<15.2f} {spent_display:<15} {currency:<10}")
        else:
            lines.append(f"{platform:<20} {amount_float:<15.2f} {currency:<10}")
        
        # Convert to target currency for total
        if amount_float > 0:  # Only add to total if we have valid data
            total += convert_currency(amount_float, currency, target_currency)
        
        # Add spent to total spent
        if has_spent and spent_float > 0:
            total_spent += convert_currency(spent_float, currency, target_currency)
    
    lines.append("-" * 80)
    
    if has_spent:
        lines.append(f"{'Total (' + target_currency + ')':<20} {total:<15.2f} {total_spent:<15.2f} {target_currency:<10}")
    else:
        lines.append(f"{'Total (' + target_currency + ')':<20} {total:<15.2f} {target_currency:<10}")
    
    lines.append("=" * 80)
    
    return '\n'.join(lines)

def _format_markdown(balances: List[Dict[str, Any]]) -> str:
    """Format as markdown table"""
    # Check if this is token data or balance data
    is_tokens = any('tokens' in balance for balance in balances)
    has_spent = any('spent' in balance for balance in balances)
    
    if is_tokens:
        lines = ["# LLM Platform Tokens\n"]
        lines.append("| Platform | Tokens | Currency |")
        lines.append("|----------|---------|----------|")
    elif has_spent:
        lines = ["# LLM Platform Costs\n"]
        lines.append("| Platform | Balance | Spent | Currency |")
        lines.append("|----------|---------|-------|----------|")
    else:
        lines = ["# LLM Platform Costs\n"]
        lines.append("| Platform | Balance | Currency |")
        lines.append("|----------|---------|----------|")
    
    for balance in balances:
        platform = balance['platform']
        
        # Handle both balance and token data
        if 'tokens' in balance:
            amount = balance['tokens']
            currency = balance['currency']
            lines.append(f"| {platform} | {amount:.2f} | {currency} |")
        else:
            amount = balance.get('balance', 0)
            spent = balance.get('spent', 0)
            currency = balance['currency']
            
            if has_spent:
                spent_display = "-" if spent == "-" else f"{spent:.2f}"
                lines.append(f"| {platform} | {amount:.2f} | {spent_display} | {currency} |")
            else:
                lines.append(f"| {platform} | {amount:.2f} | {currency} |")
    
    return '\n'.join(lines)

def _format_total(balances: List[Dict[str, Any]], target_currency: str = 'CNY') -> str:
    """Format as total only"""
    total = 0.0
    total_spent = 0.0
    
    # Check if this is token data or balance data
    is_tokens = any('tokens' in balance for balance in balances)
    has_spent = any('spent' in balance for balance in balances)
    
    for balance in balances:
        # Handle both balance and token data
        if 'tokens' in balance:
            amount = balance['tokens']
            currency = balance['currency']
            total += convert_currency(amount, currency, target_currency)
        else:
            amount = balance.get('balance', 0)
            spent = balance.get('spent', 0)
            currency = balance['currency']
            
            total += convert_currency(amount, currency, target_currency)
            
            if has_spent and isinstance(spent, (int, float)):
                total_spent += convert_currency(spent, currency, target_currency)
    
    if is_tokens:
        return f"Total tokens: {total:.2f} {target_currency}"
    elif has_spent:
        return f"Total balance: {total:.2f} {target_currency}, Total spent: {total_spent:.2f} {target_currency}"
    else:
        return f"Total cost: {total:.2f} {target_currency}"

def ensure_config_dir():
    """Ensure configuration directory exists"""
    home = Path.home()
    config_dir = home / '.llm_balance'
    config_dir.mkdir(exist_ok=True)