"""
Main coding plan checker functionality
"""

import json
import threading
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from .config import ConfigManager
from .platform_configs import PlatformConfig
from .platform_handlers.base import BasePlatformHandler, CodingPlanInfo
from .platform_handlers import create_handler

class PlanChecker:
    """Main coding plan checker class"""
    
    def __init__(self, config_file: str = None, browser: str = None):
        self.config_manager = ConfigManager(config_file)
        # Use provided browser or fall back to global configuration
        self.browser = browser or self.config_manager.get_global_browser()
        self.handlers = {}
        # Thread pool size for concurrent platform checking
        self.max_workers = 5
        # Thread lock for handler cache
        self._handler_lock = threading.Lock()

    def _check_single_plan(self, platform_config: PlatformConfig) -> Optional[Dict[str, Any]]:
        """Check coding plan for a single platform (thread-safe helper method)"""
        try:
            handler = self._get_handler(platform_config)
            try:
                plan_info = handler.get_coding_plan()
                return {
                    'platform': plan_info.platform,
                    'status': plan_info.status,
                    'quotas': [
                        {
                            'level': quota.level,
                            'percent': quota.percent,
                            'reset_timestamp': quota.reset_timestamp,
                            'reset_time': quota.reset_time
                        }
                        for quota in plan_info.quotas
                    ],
                    'update_time': plan_info.update_time,
                    'raw_data': plan_info.raw_data
                }
            except (NotImplementedError, ValueError):
                return None
        except Exception:
            return None

    def check_all_plans(self, sort: str = 'name') -> List[Dict[str, Any]]:
        """Check coding plans for all enabled platforms"""
        plans = []
        platforms = self.config_manager.get_enabled_platforms()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_platform = {
                executor.submit(self._check_single_plan, config): config
                for config in platforms
            }

            for future in as_completed(future_to_platform):
                try:
                    result = future.result()
                    if result:
                        plans.append(result)
                except Exception:
                    pass

        if sort == 'name':
            plans.sort(key=lambda x: x['platform'].lower())
        
        return plans
    
    def check_platform_plan(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """Check coding plan for a specific platform"""
        platform_config = self.config_manager.get_platform(platform_name)
        if not platform_config:
            print(f"Platform {platform_name} not found in configuration")
            return None

        try:
            handler = self._get_handler(platform_config)
            plan_info = handler.get_coding_plan()
            return {
                'platform': plan_info.platform,
                'status': plan_info.status,
                'quotas': [
                    {
                        'level': quota.level,
                        'percent': quota.percent,
                        'reset_timestamp': quota.reset_timestamp,
                        'reset_time': quota.reset_time
                    }
                    for quota in plan_info.quotas
                ],
                'update_time': plan_info.update_time,
                'raw_data': plan_info.raw_data
            }
        except Exception as e:
            print(f"Error checking coding plan for {platform_name}: {e}")
            return None
    
    def _get_handler(self, config: PlatformConfig) -> BasePlatformHandler:
        """Get handler instance for platform configuration (thread-safe)"""
        if config.name not in self.handlers:
            with self._handler_lock:
                if config.name not in self.handlers:
                    self.handlers[config.name] = create_handler(config, self.browser)
        return self.handlers[config.name]

    def format_plans(self, plans: List[Dict[str, Any]], format_type: str = 'table') -> str:
        """Format coding plan information with unified style"""
        if format_type == 'json':
            return json.dumps(plans, indent=2, ensure_ascii=False)
        
        if not plans:
            return "No coding plan information available."

        level_names = {
            'session': 'Session',
            'hourly': 'Hourly',
            'daily': 'Daily',
            'weekly': 'Weekly',
            'monthly': 'Monthly',
            'total': 'Total'
        }
        
        level_order = ['session', 'hourly', 'daily', 'weekly', 'monthly', 'total']

        from datetime import datetime
        
        width = 72
        inner_width = width - 2
        
        lines = []
        lines.append("")
        lines.append("╔" + "═" * inner_width + "╗")
        title = "CODING PLAN USAGE"
        padding = (inner_width - len(title)) // 2
        lines.append("║" + " " * padding + title + " " * (inner_width - padding - len(title)) + "║")
        lines.append("╚" + "═" * inner_width + "╝")
        
        for i, plan in enumerate(plans):
            platform = plan['platform']
            status = plan.get('status', 'Unknown')
            update_time = plan.get('update_time', '')
            quotas = plan.get('quotas', [])
            
            status_icon = '●' if status == 'Running' else '○' if status == 'Stopped' else '◌'
            status_text = 'Active' if status == 'Running' else 'Inactive' if status == 'Stopped' else status
            
            lines.append("")
            header_text = f" {platform} "
            header_padding = inner_width - len(header_text) - 1
            lines.append("┌─" + header_text + "─" * header_padding + "┐")
            
            status_info = f"Status: {status_icon} {status_text}"
            if update_time:
                update_short = update_time[5:16] if len(update_time) > 16 else update_time
                status_info += f"    Updated: {update_short}"
            lines.append("│  " + status_info.ljust(inner_width - 2) + "│")
            
            if not quotas:
                lines.append("│  " + "No quota data available".ljust(inner_width - 2) + "│")
                lines.append("└" + "─" * inner_width + "┘")
                continue
            
            lines.append("├" + "─" * inner_width + "┤")
            
            header = f"  {'Type':<10} {'Used':>7}  {'Progress':<27} {'Reset':>12}  "
            lines.append("│" + header.ljust(inner_width) + "│")
            lines.append("├" + "─" * inner_width + "┤")
            
            sorted_quotas = sorted(quotas, key=lambda x: level_order.index(x.get('level', 'total')) if x.get('level', 'total') in level_order else 99)
            
            for quota in sorted_quotas:
                level = quota.get('level', 'unknown')
                percent = quota.get('percent', 0)
                reset_time = quota.get('reset_time', '')
                
                level_display = level_names.get(level, level.capitalize())
                
                bar_width = 25
                filled = int(bar_width * min(percent, 100) / 100)
                
                if percent >= 90:
                    bar_char = '▓'
                    warn_suffix = ' !'
                elif percent >= 70:
                    bar_char = '▒'
                    warn_suffix = ''
                else:
                    bar_char = '█'
                    warn_suffix = ''
                
                bar = bar_char * filled + '░' * (bar_width - filled)
                percent_str = f"{percent:>5.1f}%"
                
                if reset_time:
                    try:
                        reset_dt = datetime.strptime(reset_time, '%Y-%m-%d %H:%M:%S')
                        now = datetime.now()
                        delta = reset_dt - now
                        if delta.days > 0:
                            reset_display = f"{delta.days}d {delta.seconds // 3600}h"
                        elif delta.seconds > 3600:
                            reset_display = f"{delta.seconds // 3600}h {(delta.seconds % 3600) // 60}m"
                        else:
                            reset_display = f"{delta.seconds // 60}m"
                    except:
                        reset_display = reset_time[:10]
                else:
                    reset_display = "—"
                
                row = f"  {level_display:<10} {percent_str:>6}{warn_suffix:<2} {bar}  {reset_display:>10}  "
                lines.append("│" + row.ljust(inner_width) + "│")
            
            lines.append("└" + "─" * inner_width + "┘")
        
        lines.append("")
        
        return "\n".join(lines)
