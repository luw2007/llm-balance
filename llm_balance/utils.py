"""
Utility functions for balance checking
"""

import json
from typing import Dict, Any, List, Union, Optional
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
        'CAD': 5.3,
        'AUD': 4.7,
        'CHF': 8.1,
        'HKD': 0.92,
        'SGD': 5.4,
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

def get_proxy_config() -> Optional[Dict[str, str]]:
    """Get proxy configuration from environment variables"""
    proxy_config = {}
    
    # Check for various proxy environment variables
    http_proxy = os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
    https_proxy = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')
    
    if http_proxy:
        proxy_config['http'] = http_proxy
    if https_proxy:
        proxy_config['https'] = https_proxy
    
    return proxy_config if proxy_config else None

def format_proxy_usage() -> str:
    """Format proxy usage instructions"""
    return """
Proxy Configuration:
Set the following environment variables to use proxy:
- HTTP_PROXY / http_proxy: Proxy for HTTP requests
- HTTPS_PROXY / https_proxy: Proxy for HTTPS requests

Example:
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="http://proxy.example.com:8080"

Or use SOCKS proxy:
export HTTP_PROXY="socks5://127.0.0.1:1080"
export HTTPS_PROXY="socks5://127.0.0.1:1080"
"""

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
            row_has_spent = False
        else:
            amount = balance.get('balance', 0)
            currency = balance['currency']
            spent = balance.get('spent', 0)
            row_has_spent = 'spent' in balance
        
        # Ensure amount is a number and prepare display
        amount_is_dash = (amount == '-')
        amount_is_numeric = True
        try:
            amount_float = float(amount) if not amount_is_dash and amount is not None else 0.0
        except (ValueError, TypeError):
            amount_float = 0.0
            amount_is_numeric = False
        # If not numeric (e.g., None or non-number), display '-'
        if amount_is_dash or not amount_is_numeric:
            amount_display = '-'
        else:
            amount_display = f"{amount_float:.2f}"
            
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
        elif row_has_spent:
            lines.append(f"{platform:<20} {amount_display:<15} {spent_display:<15} {currency:<10}")
        else:
            lines.append(f"{platform:<20} {amount_display:<15} {currency:<10}")
        
        # Convert to target currency for total
        if not amount_is_dash and amount_is_numeric:  # Add to total if we have valid numeric data (including negative)
            total += convert_currency(amount_float, currency, target_currency)
        
        # Add spent to total spent
        if row_has_spent and spent_float > 0:
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
            
            # Prepare display strings
            amount_is_dash = (amount == '-')
            amount_is_numeric = True
            try:
                amount_float = float(amount) if not amount_is_dash and amount is not None else 0.0
            except (ValueError, TypeError):
                amount_float = 0.0
                amount_is_numeric = False
            amount_display = '-' if (amount_is_dash or not amount_is_numeric) else f"{amount_float:.2f}"

            spent_display = "-" if spent == "-" else f"{float(spent):.2f}" if isinstance(spent, (int, float)) else "-"
            
            if has_spent:
                lines.append(f"| {platform} | {amount_display} | {spent_display} | {currency} |")
            else:
                lines.append(f"| {platform} | {amount_display} | {currency} |")
    
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
            
            # Only include numeric amounts in totals (including negative)
            if isinstance(amount, (int, float)) and amount != 0:
                total += convert_currency(float(amount), currency, target_currency)
            
            if has_spent and isinstance(spent, (int, float)):
                total_spent += convert_currency(float(spent), currency, target_currency)
    
    if is_tokens:
        return f"Total tokens: {total:.2f} {target_currency}"
    elif has_spent:
        return f"Total balance: {total:.2f} {target_currency}, Total spent: {total_spent:.2f} {target_currency}"
    else:
        return f"Total cost: {total:.2f} {target_currency}"

def format_platform_info(platform_info: Dict[str, Any], format_type: str = 'table', target_currency: str = 'CNY') -> str:
    """
    Format combined platform info (cost + package + plan) in different formats
    
    Args:
        platform_info: Dict with 'cost_info' (CostInfo), 'package_info' (PlatformTokenInfo or None), 
                      and 'plan_info' (CodingPlanInfo or None)
        format_type: Output format - 'table', 'json', or 'markdown'
        target_currency: Target currency for cost conversion
        
    Returns:
        Formatted string representation of platform info
    """
    cost_info = platform_info.get('cost_info')
    package_info = platform_info.get('package_info')
    plan_info = platform_info.get('plan_info')
    
    if format_type == 'json':
        return _format_platform_info_json(cost_info, package_info, plan_info)
    elif format_type == 'markdown':
        return _format_platform_info_markdown(cost_info, package_info, plan_info, target_currency)
    else:
        return _format_platform_info_table(cost_info, package_info, plan_info, target_currency)

def _format_platform_info_json(cost_info, package_info, plan_info) -> str:
    """Format platform info as JSON"""
    result = {
        'cost': None,
        'package': None,
        'plan': None
    }
    
    if cost_info:
        result['cost'] = {
            'platform': cost_info.platform,
            'balance': cost_info.balance,
            'currency': cost_info.currency,
            'spent': cost_info.spent,
            'spent_currency': cost_info.spent_currency,
            'raw_data': cost_info.raw_data
        }
    
    if package_info:
        result['package'] = {
            'platform': package_info.platform,
            'models': [
                {
                    'model': m.model,
                    'package': m.package,
                    'remaining_tokens': m.remaining_tokens,
                    'used_tokens': m.used_tokens,
                    'total_tokens': m.total_tokens,
                    'status': m.status,
                    'expiry_date': m.expiry_date,
                    'reset_count': m.reset_count,
                    'reset_time': m.reset_time
                }
                for m in package_info.models
            ],
            'raw_data': package_info.raw_data
        }
    else:
        result['package'] = {'message': '该平台不支持 token 监控'}
    
    if plan_info:
        result['plan'] = {
            'platform': plan_info.platform,
            'status': plan_info.status,
            'quotas': [
                {
                    'level': q.level,
                    'percent': q.percent,
                    'reset_timestamp': q.reset_timestamp,
                    'reset_time': q.reset_time
                }
                for q in plan_info.quotas
            ],
            'update_time': plan_info.update_time,
            'raw_data': plan_info.raw_data
        }
    else:
        result['plan'] = {'message': '该平台不支持编码计划监控'}
    
    clean_result = _clean_for_json(result)
    return json.dumps(clean_result, indent=2, ensure_ascii=False)

def _format_platform_info_markdown(cost_info, package_info, plan_info, target_currency: str) -> str:
    """Format platform info as markdown"""
    lines = []
    
    if cost_info:
        platform_name = cost_info.platform
        lines.append(f"# {platform_name} 平台信息\n")
        
        lines.append("## 费用信息\n")
        lines.append("| 项目 | 数值 | 货币 |")
        lines.append("|------|------|------|")
        
        balance_display = f"{cost_info.balance:.2f}" if isinstance(cost_info.balance, (int, float)) else "-"
        lines.append(f"| 余额 | {balance_display} | {cost_info.currency} |")
        
        if cost_info.spent != "-" and cost_info.spent is not None:
            spent_display = f"{cost_info.spent:.2f}" if isinstance(cost_info.spent, (int, float)) else "-"
            spent_currency = cost_info.spent_currency or cost_info.currency
            lines.append(f"| 已消费 | {spent_display} | {spent_currency} |")
        
        if target_currency != cost_info.currency:
            converted_balance = convert_currency(cost_info.balance, cost_info.currency, target_currency)
            lines.append(f"| 余额({target_currency}) | {converted_balance:.2f} | {target_currency} |")
    
    if package_info:
        lines.append("\n## Token 使用情况\n")
        lines.append("| 模型 | 套餐 | 剩余 Token | 已用 Token | 总 Token | 状态 |")
        lines.append("|------|------|------------|------------|----------|------|")
        
        for model in package_info.models:
            lines.append(
                f"| {model.model} | {model.package} | "
                f"{model.remaining_tokens:,.0f} | {model.used_tokens:,.0f} | "
                f"{model.total_tokens:,.0f} | {model.status} |"
            )
            
            if model.expiry_date:
                lines.append(f"| | 到期时间: {model.expiry_date} | | | | |")
            if model.reset_time:
                lines.append(f"| | 重置时间: {model.reset_time} | | | | |")
    else:
        lines.append("\n## Token 使用情况\n")
        lines.append("该平台不支持 token 监控")
    
    if plan_info:
        lines.append("\n## 编码计划使用情况\n")
        lines.append(f"状态: {plan_info.status}")
        if plan_info.update_time:
            lines.append(f"更新时间: {plan_info.update_time}\n")
        
        lines.append("| 类型 | 已用百分比 | 重置时间 |")
        lines.append("|------|-----------|---------|")
        
        for quota in plan_info.quotas:
            reset_time_display = quota.reset_time if quota.reset_time else "-"
            lines.append(f"| {quota.level.capitalize()} | {quota.percent:.1f}% | {reset_time_display} |")
    else:
        lines.append("\n## 编码计划使用情况\n")
        lines.append("该平台不支持编码计划监控")
    
    return '\n'.join(lines)

def _format_platform_info_table(cost_info, package_info, plan_info, target_currency: str) -> str:
    """Format platform info as text table"""
    lines = []
    
    if cost_info:
        platform_name = cost_info.platform
        lines.append("=" * 80)
        lines.append(f" {platform_name} 平台信息")
        lines.append("=" * 80)
        
        lines.append("\n【费用信息】")
        lines.append("-" * 80)
        
        balance_display = f"{cost_info.balance:.2f}" if isinstance(cost_info.balance, (int, float)) else "-"
        lines.append(f"  余额:     {balance_display} {cost_info.currency}")
        
        if cost_info.spent != "-" and cost_info.spent is not None:
            spent_display = f"{cost_info.spent:.2f}" if isinstance(cost_info.spent, (int, float)) else "-"
            spent_currency = cost_info.spent_currency or cost_info.currency
            lines.append(f"  已消费:   {spent_display} {spent_currency}")
        
        if target_currency != cost_info.currency and isinstance(cost_info.balance, (int, float)):
            converted_balance = convert_currency(cost_info.balance, cost_info.currency, target_currency)
            lines.append(f"  余额({target_currency}): {converted_balance:.2f} {target_currency}")
    
    if package_info:
        lines.append("\n【Token 使用情况】")
        lines.append("-" * 80)
        lines.append(f"{'模型':<20} {'套餐':<15} {'剩余Token':<15} {'已用Token':<15} {'总Token':<15} {'状态':<10}")
        lines.append("-" * 80)
        
        for model in package_info.models:
            lines.append(
                f"{model.model:<20} {model.package:<15} "
                f"{model.remaining_tokens:<15,.0f} {model.used_tokens:<15,.0f} "
                f"{model.total_tokens:<15,.0f} {model.status:<10}"
            )
            
            if model.expiry_date:
                lines.append(f"  ↳ 到期时间: {model.expiry_date}")
            if model.reset_time:
                lines.append(f"  ↳ 重置时间: {model.reset_time}")
    else:
        lines.append("\n【Token 使用情况】")
        lines.append("-" * 80)
        lines.append("  该平台不支持 token 监控")
    
    if plan_info:
        from datetime import datetime
        
        lines.append("\n【编码计划使用情况】")
        lines.append("-" * 80)
        
        status_icon = '●' if plan_info.status == 'Running' else '○'
        status_text = 'Active' if plan_info.status == 'Running' else 'Inactive' if plan_info.status == 'Stopped' else plan_info.status
        lines.append(f"  状态: {status_icon} {status_text}")
        
        if plan_info.update_time:
            update_short = plan_info.update_time[5:16] if len(plan_info.update_time) > 16 else plan_info.update_time
            lines.append(f"  更新时间: {update_short}")
        
        lines.append("")
        lines.append(f"  {'类型':<12} {'已用':<8} {'进度':<30} {'重置时间':<15}")
        lines.append("  " + "-" * 76)
        
        level_names = {
            'session': 'Session',
            'hourly': 'Hourly',
            'daily': 'Daily',
            'weekly': 'Weekly',
            'monthly': 'Monthly',
            'total': 'Total'
        }
        
        for quota in plan_info.quotas:
            level_display = level_names.get(quota.level, quota.level.capitalize())
            percent_str = f"{quota.percent:>5.1f}%"
            
            bar_width = 25
            filled = int(bar_width * min(quota.percent, 100) / 100)
            
            if quota.percent >= 90:
                bar_char = '▓'
                warn_suffix = ' !'
            elif quota.percent >= 70:
                bar_char = '▒'
                warn_suffix = ''
            else:
                bar_char = '░'
                warn_suffix = ''
            
            bar = bar_char * filled + '░' * (bar_width - filled)
            
            if quota.reset_time:
                try:
                    reset_dt = datetime.strptime(quota.reset_time, '%Y-%m-%d %H:%M:%S')
                    now = datetime.now()
                    delta = reset_dt - now
                    if delta.days > 0:
                        reset_display = f"{delta.days}d {delta.seconds // 3600}h"
                    elif delta.seconds > 3600:
                        reset_display = f"{delta.seconds // 3600}h {(delta.seconds % 3600) // 60}m"
                    else:
                        reset_display = f"{delta.seconds // 60}m"
                except:
                    reset_display = quota.reset_time[:10]
            else:
                reset_display = "—"
            
            lines.append(f"  {level_display:<12} {percent_str:>6}{warn_suffix:<2} {bar}  {reset_display:>12}")
    else:
        lines.append("\n【编码计划使用情况】")
        lines.append("-" * 80)
        lines.append("  该平台不支持编码计划监控")
    
    lines.append("=" * 80)
    return '\n'.join(lines)

def ensure_config_dir():
    """Ensure configuration directory exists"""
    home = Path.home()
    config_dir = home / '.llm_balance'
    config_dir.mkdir(exist_ok=True)
