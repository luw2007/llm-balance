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

def format_output(balances: List[Dict[str, Any]], format_type: str = 'table', target_currency: str = 'CNY') -> str:
    """Format balance output in different formats"""
    if not balances:
        return "No balance data available"
    
    if format_type == 'json':
        return json.dumps(balances, indent=2, ensure_ascii=False)
    
    elif format_type == 'markdown':
        return _format_markdown(balances)
    
    elif format_type == 'total':
        return _format_total(balances, target_currency)
    
    else:  # table format
        return _format_table(balances, target_currency)

def _format_table(balances: List[Dict[str, Any]], target_currency: str = 'CNY') -> str:
    """Format as text table"""
    lines = []
    lines.append("=" * 60)
    lines.append(f"{'Platform':<20} {'Balance':<15} {'Currency':<10}")
    lines.append("-" * 60)
    
    total = 0
    for balance in balances:
        platform = balance['platform']
        amount = balance['balance']
        currency = balance['currency']
        
        # Ensure amount is a number
        try:
            amount_float = float(amount) if amount is not None else 0.0
        except (ValueError, TypeError):
            amount_float = 0.0
            
        lines.append(f"{platform:<20} {amount_float:<15.2f} {currency:<10}")
        
        # Convert to target currency for total
        total += convert_currency(amount_float, currency, target_currency)
    
    lines.append("-" * 60)
    lines.append(f"{'Total (' + target_currency + ')':<20} {total:<15.2f} {target_currency:<10}")
    lines.append("=" * 60)
    
    return '\n'.join(lines)

def _format_markdown(balances: List[Dict[str, Any]]) -> str:
    """Format as markdown table"""
    lines = ["# LLM Platform Costs\n"]
    lines.append("| Platform | Balance | Currency |")
    lines.append("|----------|---------|----------|")
    
    for balance in balances:
        platform = balance['platform']
        amount = balance['balance']
        currency = balance['currency']
        lines.append(f"| {platform} | {amount:.2f} | {currency} |")
    
    return '\n'.join(lines)

def _format_total(balances: List[Dict[str, Any]], target_currency: str = 'CNY') -> str:
    """Format as total only"""
    total = 0
    for balance in balances:
        amount = balance['balance']
        currency = balance['currency']
        total += convert_currency(amount, currency, target_currency)
    
    return f"Total cost: {total:.2f} {target_currency}"

def ensure_config_dir():
    """Ensure configuration directory exists"""
    home = Path.home()
    config_dir = home / '.llm_balance'
    config_dir.mkdir(exist_ok=True)