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

def format_model_tokens(
    platform_tokens: List[Dict[str, Any]],
    format_type: str = 'table',
    target_currency: str = 'CNY',
    model: Optional[str] = None,
    show_all: bool = False,
    show_expiry: bool = False,
    show_reset: bool = False,
    show_reset_time: bool = False,
) -> str:
    """Format model-level token information"""
    if not platform_tokens:
        return "No token data available"

    tokens_to_format = platform_tokens

    # Filter by model if provided
    if model:
        tokens_to_format = _filter_tokens_by_model(tokens_to_format, model)

    if not show_all:
        tokens_to_format = _filter_out_inactive(tokens_to_format)

    if not tokens_to_format:
        return "No token data available"

    if format_type == 'json':
        return _format_model_json(tokens_to_format)
    elif format_type == 'markdown':
        return _format_model_markdown(tokens_to_format, show_expiry, show_reset, show_reset_time)
    elif format_type == 'total':
        return _format_model_total(tokens_to_format, target_currency)
    else:  # table format
        return _format_model_table(tokens_to_format, target_currency, show_expiry, show_reset, show_reset_time)

def _format_model_table(platform_tokens: List[Dict[str, Any]], target_currency: str = 'CNY', show_expiry: bool = False, show_reset: bool = False, show_reset_time: bool = False) -> str:
    """Format model tokens as detailed table"""
    lines = []

    # Calculate column widths based on what we're showing
    base_width = 125
    extra_width = 0
    if show_expiry:
        extra_width += 12
    if show_reset:
        extra_width += 10
    if show_reset_time:
        extra_width += 16

    total_width = base_width + extra_width

    lines.append("=" * total_width)

    # Build header dynamically - Expiry, Resets, ResetTime before Package
    header = f"{'Platform':<15} {'Model':<30} {'Total':<12} {'Used':<12} {'Remaining':<12} {'Progress %':<11} {'Status':<8}"
    if show_expiry:
        header += f" {'Expiry':<11}"
    if show_reset:
        header += f" {'Resets':<9}"
    if show_reset_time:
        header += f" {'ResetTime':<15}"
    header += f" {'Package':<15}"

    lines.append(header)
    lines.append("-" * total_width)
    
    total_all_tokens = 0
    total_used_tokens = 0
    total_remaining_tokens = 0
    
    for platform_data in platform_tokens:
        platform = platform_data['platform']
        models = platform_data.get('models', [])
        
        if not models:
            lines.append(f"{platform:<15} {'No data':<30} {'-':<12} {'-':<12} {'-':<12} {'-':<11} {'-':<8} {'-':<15}")
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

            # Calculate progress percentage or display "-"
            if total > 0:
                progress_value = used / total * 100
                # Remove .0 if it's an integer
                if progress_value.is_integer():
                    if progress_value == 100:
                        progress_display = " - "
                    elif progress_value == 0:
                        progress_display = "0        "
                    else:
                        progress_display = f"{int(progress_value):<9}"
                else:
                    progress_display = f"{progress_value:<9.1f}"
            else:
                progress_display = " - "

            # Get status with default fallback
            status = str(model_info.get('status', 'active'))[:8]

            row = f"{platform:<15} {model:<30} {total:<12.0f} {used:<12.0f} {remaining:<12.0f} {progress_display:<11} {status:<8}"
            if show_expiry:
                expiry = model_info.get('expiry_date')
                expiry_display = str(expiry) if expiry else '-'
                row += f" {expiry_display:<11}"
            if show_reset:
                reset = model_info.get('reset_count')
                reset_display = str(reset) if reset is not None else '-'
                row += f" {reset_display:<9}"
            if show_reset_time:
                reset_time = model_info.get('reset_time')
                reset_time_display = str(reset_time) if reset_time else '-'
                # Truncate long reset_time values for display
                if len(reset_time_display) > 15:
                    reset_time_display = reset_time_display[:12] + '...'
                row += f" {reset_time_display:<15}"
            row += f" {package:<15}"
            lines.append(row)

            total_all_tokens += total
            total_used_tokens += used
            total_remaining_tokens += remaining

    lines.append("-" * total_width)
    footer = f"{'Total Tokens':<53} {total_all_tokens:<12.0f} {total_used_tokens:<12.0f} {total_remaining_tokens:<12.0f} {'-':<11} {'-':<8}"
    if show_expiry:
        footer += f" {'-':<11}"
    if show_reset:
        footer += f" {'-':<9}"
    if show_reset_time:
        footer += f" {'-':<15}"
    footer += f" {'-':<15}"
    lines.append(footer)
    lines.append("=" * total_width)
    
    return '\n'.join(lines)

def _format_model_json(platform_tokens: List[Dict[str, Any]]) -> str:
    """Format model tokens as JSON"""
    # Clean the data to make it JSON serializable
    cleaned_tokens = _clean_for_json(platform_tokens)
    return json.dumps(cleaned_tokens, indent=2, ensure_ascii=False)

def _format_model_markdown(platform_tokens: List[Dict[str, Any]], show_expiry: bool = False, show_reset: bool = False, show_reset_time: bool = False) -> str:
    """Format model tokens as markdown table"""
    lines = ["# LLM Model Token Statistics\n"]

    for platform_data in platform_tokens:
        platform = platform_data['platform']
        models = platform_data.get('models', [])

        if models:
            lines.append(f"## {platform}\n")

            # Build header dynamically - Expiry, Resets, ResetTime before Package
            header = "| Platform | Model | Total | Used | Remaining | Progress % | Status |"
            if show_expiry:
                header += " Expiry |"
            if show_reset:
                header += " Resets |"
            if show_reset_time:
                header += " ResetTime |"
            header += " Package |"
            lines.append(header)

            # Build separator dynamically
            separator = "|----------|-------|-------|------|-----------|------------|--------|"
            if show_expiry:
                separator += "---------|"
            if show_reset:
                separator += "--------|"
            if show_reset_time:
                separator += "-------------|"
            separator += "---------|"
            lines.append(separator)

            for model_info in models:
                model = model_info['model']
                package = model_info.get('package', model)
                total = model_info['total_tokens']
                used = model_info['used_tokens']
                remaining = model_info['remaining_tokens']

                # Calculate progress percentage or display "-"
                if total > 0:
                    progress_value = used / total * 100
                    # Remove .0 if it's an integer
                    if progress_value.is_integer():
                        if progress_value == 100:
                            progress_pct = "-"
                        elif progress_value == 0:
                            progress_pct = "0"
                        else:
                            progress_pct = f"{int(progress_value)}"
                    else:
                        progress_pct = f"{progress_value:.1f}"
                else:
                    progress_pct = "-"

                # Get status with default fallback
                status = model_info.get('status', 'active')
                row = f"| {platform} | {model} | {total:.0f} | {used:.0f} | {remaining:.0f} | {progress_pct} | {status} |"
                if show_expiry:
                    expiry = model_info.get('expiry_date')
                    expiry_display = expiry if expiry else '-'
                    row += f" {expiry_display} |"
                if show_reset:
                    reset = model_info.get('reset_count')
                    reset_display = str(reset) if reset is not None else '-'
                    row += f" {reset_display} |"
                if show_reset_time:
                    reset_time = model_info.get('reset_time')
                    reset_time_display = str(reset_time) if reset_time else '-'
                    row += f" {reset_time_display} |"
                row += f" {package} |"
                lines.append(row)

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


def _filter_out_inactive(platform_tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove models marked as inactive from the token list"""
    filtered_tokens: List[Dict[str, Any]] = []

    for platform_data in platform_tokens:
        models = platform_data.get('models', [])
        active_models = []

        for model_info in models:
            status = str(model_info.get('status', 'active')).lower()
            if status != 'inactive':
                active_models.append(model_info)

        if active_models:
            filtered_tokens.append({
                'platform': platform_data.get('platform'),
                'models': active_models,
                'raw_data': platform_data.get('raw_data', {})
            })

    return filtered_tokens
