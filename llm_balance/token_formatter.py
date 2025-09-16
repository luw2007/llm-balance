"""
Token formatting utilities for model-level token statistics
"""

import json
from typing import Dict, Any, List, Optional

def _clean_for_json(data):
    """Clean data to make it JSON serializable"""
    if isinstance(data, dict):
        return {k: _clean_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_clean_for_json(item) for item in data]
    elif hasattr(data, '__dict__'):
        # Convert object to dict, skipping Configuration objects
        obj_name = data.__class__.__name__
        if obj_name == 'Configuration':
            return f"<{obj_name} object>"
        return {k: _clean_for_json(v) for k, v in data.__dict__.items()}
    else:
        try:
            # Test if the value is JSON serializable
            json.dumps(data)
            return data
        except (TypeError, ValueError):
            return f"<{data.__class__.__name__} object>"

def format_model_tokens(platform_tokens: List[Dict[str, Any]], format_type: str = 'table', target_currency: str = 'CNY', model: Optional[str] = None) -> str:
    """Format model-level token information"""
    if not platform_tokens:
        return "No token data available"
    
    # Filter by model if provided
    if model:
        platform_tokens = _filter_tokens_by_model(platform_tokens, model)
    
    if format_type == 'json':
        return _format_model_json(platform_tokens)
    elif format_type == 'markdown':
        return _format_model_markdown(platform_tokens)
    elif format_type == 'total':
        return _format_model_total(platform_tokens, target_currency)
    else:  # table format
        return _format_model_table(platform_tokens, target_currency)

def _format_model_table(platform_tokens: List[Dict[str, Any]], target_currency: str = 'CNY') -> str:
    """Format model tokens as detailed table"""
    lines = []
    lines.append("=" * 100)
    lines.append(f"{'Platform':<15} {'Model':<30} {'Total':<12} {'Used':<12} {'Remaining':<12} {'Package':<20}")
    lines.append("-" * 100)
    
    total_all_tokens = 0
    total_used_tokens = 0
    total_remaining_tokens = 0
    
    for platform_data in platform_tokens:
        platform = platform_data['platform']
        models = platform_data.get('models', [])
        
        if not models:
            lines.append(f"{platform:<15} {'No data':<30} {'-':<12} {'-':<12} {'-':<12} {'-':<20}")
            continue
        
        for model_info in models:
            model = str(model_info.get('model', ''))[:30]

            # Normalize package for display; if dict, prefer human-readable name
            raw_package = model_info.get('package', model)
            if isinstance(raw_package, dict):
                pkg_name = (
                    raw_package.get('name')
                    or raw_package.get('title')
                    or raw_package.get('plan_name')
                    or raw_package.get('plan')
                    or raw_package.get('id')
                    or 'Subscription'
                )
                package = str(pkg_name)
            else:
                package = str(raw_package)

            # Take numbers from model_info, but allow override from package dict for FoxCode-like schemas
            def _num(v) -> float:
                try:
                    if v is None:
                        return 0.0
                    if isinstance(v, (int, float)):
                        return float(v)
                    s = str(v).strip().replace(',', '')
                    return float(s)
                except Exception:
                    return 0.0

            total = _num(model_info.get('total_tokens'))
            used = _num(model_info.get('used_tokens'))
            remaining = _num(model_info.get('remaining_tokens'))

            # If package dict has quotaLimit/duration, map: Total=quotaLimit, Remaining=duration, Used=Total-Remaining
            if isinstance(raw_package, dict):
                pkg_total = _num(raw_package.get('quotaLimit'))
                pkg_remaining = _num(raw_package.get('duration'))
                if pkg_total or pkg_remaining:
                    total = pkg_total or total
                    remaining = pkg_remaining or remaining
                    if total and remaining and used == 0.0:
                        used = max(0.0, total - remaining)
                    elif total and used and not remaining:
                        remaining = max(0.0, total - used)
                    elif used and remaining and not total:
                        total = used + remaining

            lines.append(f"{platform:<15} {model:<30} {total:<12.0f} {used:<12.0f} {remaining:<12.0f} {package:<20}")

            total_all_tokens += total
            total_used_tokens += used
            total_remaining_tokens += remaining
    
    lines.append("-" * 100)
    lines.append(f"{'Total Tokens':<45} {total_all_tokens:<12.0f} {total_used_tokens:<12.0f} {total_remaining_tokens:<12.0f}")
    lines.append("=" * 100)
    
    return '\n'.join(lines)

def _format_model_json(platform_tokens: List[Dict[str, Any]]) -> str:
    """Format model tokens as JSON"""
    # Clean the data to make it JSON serializable
    cleaned_tokens = _clean_for_json(platform_tokens)
    return json.dumps(cleaned_tokens, indent=2, ensure_ascii=False)

def _format_model_markdown(platform_tokens: List[Dict[str, Any]]) -> str:
    """Format model tokens as markdown table"""
    lines = ["# LLM Model Token Statistics\n"]
    
    for platform_data in platform_tokens:
        platform = platform_data['platform']
        models = platform_data.get('models', [])
        
        if models:
            lines.append(f"## {platform}\n")
            lines.append("| Platform | Model | Total | Used | Remaining | Package |")
            lines.append("|----------|-------|-------|------|-----------|---------|")
            
            for model_info in models:
                model = model_info['model']
                package = model_info.get('package', model)
                total = model_info['total_tokens']
                used = model_info['used_tokens']
                remaining = model_info['remaining_tokens']
                
                lines.append(f"| {platform} | {model} | {total:.0f} | {used:.0f} | {remaining:.0f} | {package} |")
            
            lines.append("")
    
    return '\n'.join(lines)

def _format_model_total(platform_tokens: List[Dict[str, Any]], target_currency: str = 'CNY') -> str:
    """Format total tokens across all models"""
    total_tokens = 0
    
    for platform_data in platform_tokens:
        models = platform_data.get('models', [])
        for model_info in models:
            total_tokens += model_info['remaining_tokens']
    
    return f"Total available tokens across all models: {total_tokens:.0f} tokens"

def _filter_tokens_by_model(platform_tokens: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
    """Filter tokens by model name"""
    filtered_tokens = []
    
    for platform_data in platform_tokens:
        platform = platform_data['platform']
        models = platform_data.get('models', [])
        
        # Filter models by model name
        filtered_models = []
        for model_info in models:
            # Check model name for matching
            model_name = model_info.get('model', '').lower()
            target_model = model.lower()
            
            # Match if model name contains target model
            if target_model in model_name:
                filtered_models.append(model_info)
        
        if filtered_models:  # Only include platforms with matching models
            filtered_tokens.append({
                'platform': platform,
                'models': filtered_models,
                'raw_data': platform_data.get('raw_data', {})
            })
    
    return filtered_tokens
