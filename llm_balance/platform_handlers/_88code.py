"""
88Code third-party relay handler (balance query only)
"""

import os
from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, PlatformTokenInfo, ModelTokenInfo, CostInfo
from ..config import PlatformConfig


class Handler88Code(BasePlatformHandler):
    """88Code relay platform handler (only balance query is implemented)."""

    @classmethod
    def get_default_config(cls) -> dict:
        """Default configuration for 88Code balance query via console_token auth."""
        return {
            "display_name": "88Code",
            "handler_class": "Handler88Code",
            "description": "88Code relay (balance only)",
            "api_url": "https://www.88code.org/admin-api/cc-admin/system/subscription/my",
            "method": "GET",
            "auth_type": "console_token",
            "env_var": None,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Cache-Control": "no-cache",
                "DNT": "1",
                "Pragma": "no-cache",
                "Priority": "u=1, i",
                "Referer": "https://www.88code.org/my-subscription",
                "Sec-Ch-Ua": '"Not=A?Brand";v="24", "Chromium";v="140"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            },
            "params": {},
            "data": {},
            # Keep disabled by default to avoid affecting default cost runs
            "enabled": False,
            # Note: console_token is now loaded from environment variables or separate config
        }

    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
        # Load platform-specific configuration from environment variables
        self._load_env_config()

    def _load_env_config(self):
        """Load configuration from environment variables or separate config file."""
        # Try environment variable first
        env_console_token = os.getenv('CODE88_CONSOLE_TOKEN')
        if env_console_token:
            self.config.console_token = env_console_token
            return

        # Try separate config file
        import yaml
        from pathlib import Path
        config_path = Path.home() / '.llm_balance' / '88code_config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    code88_config = yaml.safe_load(f) or {}
                    if 'console_token' in code88_config:
                        self.config.console_token = code88_config['console_token']
            except Exception:
                pass

    def get_platform_name(self) -> str:
        return "88Code"

    def get_balance(self) -> CostInfo:
        """Return cost info using subscription cost data from API.

        Logic:
        - For each subscription:
          - If remainingDays <= 0 (expired) OR isActive=false (disabled): entire cost goes to spent
          - If remainingDays > 0 AND isActive=true:
            * PAY_PER_USE plans: balance = cost × (remainingCredits / creditLimit)
            * MONTHLY/YEARLY plans: balance = cost × (remainingDays / totalDays)
        - Balance = sum of remaining value of all active and non-expired subscriptions
        - Spent = sum of all costs - balance

        Plan type based calculation:
        - PAY_PER_USE (按量付费，如PAYGO):
          * Uses credit-based calculation: remaining credits / total credit limit
          * Balance represents unused credits value
          * Spent represents consumed credits value

        - MONTHLY/YEARLY (订阅制，如PLUS、FREE):
          * Uses time-based calculation: remaining days / total days
          * totalDays calculated from (endDate - startDate), or from billingCycle
          * Balance represents unused time value
          * Spent represents time-elapsed value

        This ensures that:
        1. Expired subscriptions are fully counted in spent
        2. Disabled subscriptions (even if not expired) are fully counted in spent
        3. PAY_PER_USE subscriptions depreciate based on credit usage
        4. MONTHLY/YEARLY subscriptions depreciate based on time elapsed
        """
        if not getattr(self.config, 'api_url', None):
            raise ValueError("No API URL configured for 88Code")

        headers = (self.config.headers or {}).copy()

        # Get console_token from config (loaded from env var or separate config file)
        console_token = getattr(self.config, 'console_token', None)
        if not console_token:
            raise ValueError(
                "88Code requires console_token to be configured. Please set it using:\n"
                "1. Environment variable: export CODE88_CONSOLE_TOKEN=YOUR_TOKEN\n"
                "2. Separate config file: ~/.llm_balance/88code_config.yaml\n"
                "   console_token: YOUR_TOKEN"
            )

        # Set required headers
        headers['Authorization'] = f'Bearer {console_token}'

        # Make the API request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers
        )

        if not response:
            raise ValueError("No response from 88Code subscription API")

        # Check API response status
        if isinstance(response, dict):
            ok = response.get('ok', False)
            code = response.get('code', 0)
            msg = response.get('msg', '')

            # Check for error responses
            if not ok or code != 0:
                raise ValueError(f"88Code API error (code={code}): {msg}")

        # Extract balance and spent from subscription data
        total_cost = 0.0
        balance = 0.0

        try:
            data = response.get('data', []) if isinstance(response, dict) else []
            if isinstance(data, list):
                # Process each subscription
                for item in data:
                    if not isinstance(item, dict):
                        continue

                    # Get cost
                    cost = item.get('cost', 0)
                    if cost is None or cost == 0:
                        continue

                    item_cost = float(str(cost).replace(',', '').strip())
                    total_cost += item_cost

                    # Check if subscription is expired or inactive
                    remaining_days = item.get('remainingDays', 0)
                    try:
                        remaining_days = int(remaining_days) if remaining_days is not None else 0
                    except (ValueError, TypeError):
                        remaining_days = 0

                    is_active = item.get('isActive', False)

                    # If expired (remainingDays <= 0) or inactive (isActive=false),
                    # entire cost goes to spent (balance = 0 for this item)
                    if remaining_days <= 0 or not is_active:
                        continue  # Don't add to balance

                    # Get plan type to determine calculation method
                    subscription_plan = item.get('subscriptionPlan', {}) if isinstance(item.get('subscriptionPlan'), dict) else {}
                    plan_type = subscription_plan.get('planType', '').upper()

                    # Calculate balance based on plan type
                    if plan_type == 'PAY_PER_USE':
                        # For PAY_PER_USE: calculate based on credit usage
                        current_credits = item.get('currentCredits', 0)
                        credit_limit = subscription_plan.get('creditLimit', 0)

                        if credit_limit > 0:
                            try:
                                usage_ratio = float(current_credits) / float(credit_limit)
                                balance += item_cost * usage_ratio
                            except (ValueError, TypeError, ZeroDivisionError):
                                # If calculation fails, assume full balance remains
                                balance += item_cost
                        else:
                            # No credit limit, assume full balance
                            balance += item_cost

                    else:
                        # For MONTHLY/YEARLY subscriptions: calculate based on time (remaining days)
                        # Try to calculate total days from startDate and endDate
                        start_date_str = item.get('startDate')
                        end_date_str = item.get('endDate')
                        total_days = None

                        if start_date_str and end_date_str:
                            try:
                                from datetime import datetime
                                start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
                                end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')
                                total_days = (end_date - start_date).days
                            except Exception:
                                total_days = None

                        # If we couldn't calculate from dates, use billing cycle as fallback
                        if total_days is None or total_days <= 0:
                            billing_cycle = item.get('billingCycle', '').lower()
                            if billing_cycle == 'monthly':
                                total_days = 30
                            elif billing_cycle == 'yearly':
                                total_days = 365
                            else:
                                # Default fallback
                                total_days = 30

                        # Calculate balance based on remaining days ratio
                        if total_days > 0 and remaining_days >= 0:
                            try:
                                remaining_ratio = float(remaining_days) / float(total_days)
                                # Cap the ratio at 1.0 to handle edge cases
                                remaining_ratio = min(1.0, remaining_ratio)
                                balance += item_cost * remaining_ratio
                            except (ValueError, TypeError, ZeroDivisionError):
                                # If calculation fails, assume full balance remains
                                balance += item_cost
                        else:
                            # Fallback: assume full balance remains
                            balance += item_cost

                # Calculate spent
                spent = max(0.0, total_cost - balance)
        except Exception as e:
            # Log the error but don't silently reset to 0
            import traceback
            print(f"Error calculating 88Code balance: {e}")
            traceback.print_exc()
            balance = 0.0
            spent = 0.0

        # Validate final balance and spent
        balance = self._validate_balance(balance, "balance")
        spent = self._validate_balance(spent, "spent")

        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance,
            currency='CNY',
            spent=spent,
            spent_currency='CNY',
            raw_data=response
        )

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Query 88Code subscription data and create usage package from subscription info.

        Authentication:
            - Use console_token from environment variables or config file
            - Set header: Authorization: Bearer <console_token>

        Data source:
            - GET https://www.88code.org/admin-api/cc-admin/system/subscription/my
            - Use data from the response (subscription plans)

        Models:
            - Generic model name: "claude,gpt-5,gpt-5-codex"
            - Package name: from subscriptionPlanName or "88Code Subscription"
        """
        if not getattr(self.config, 'api_url', None):
            raise ValueError("No API URL configured for 88Code")

        headers = (self.config.headers or {}).copy()

        # Get console_token from config (loaded from env var or separate config file)
        console_token = getattr(self.config, 'console_token', None)
        if not console_token:
            raise ValueError(
                "88Code requires console_token to be configured. Please set it using:\n"
                "1. Environment variable: export CODE88_CONSOLE_TOKEN=YOUR_TOKEN\n"
                "2. Separate config file: ~/.llm_balance/88code_config.yaml\n"
                "   console_token: YOUR_TOKEN"
            )

        # Set required headers
        headers['Authorization'] = f'Bearer {console_token}'

        # Make the API request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers
        )

        if not response:
            raise ValueError("No response from 88Code subscription API")

        # Check API response status
        if isinstance(response, dict):
            ok = response.get('ok', False)
            code = response.get('code', 0)
            msg = response.get('msg', '')

            # Check for error responses
            if not ok or code != 0:
                raise ValueError(f"88Code API error (code={code}): {msg}")

        # Extract subscription information
        models = self._extract_models_from_subscription(response)

        return PlatformTokenInfo(
            platform=self.get_platform_name(),
            models=models,
            raw_data=response
        )

    def _extract_models_from_subscription(self, response: Dict[str, Any]) -> List[ModelTokenInfo]:
        """Extract ModelTokenInfo list from subscription response.

        The schema:
            - Look for list at response.data
            - For each item, extract subscription plan information based on planType

        Plan type based calculation:
        - PAY_PER_USE (按量付费):
          * Total = creditLimit (from subscriptionPlan)
          * Remaining = currentCredits (actual remaining credits)
          * Used = creditLimit - currentCredits (actual used credits)
          * No reset_count or reset_time (set to None)

        - MONTHLY/YEARLY (订阅制):
          * Total = creditLimit (from subscriptionPlan)
          * Remaining = creditLimit × (remainingDays / totalDays) (time-based)
          * Used = creditLimit × (elapsedDays / totalDays) (time-based)
          * Include reset_count and reset_time
        """
        data = response if isinstance(response, dict) else {}
        subscriptions = data.get('data', []) if isinstance(data.get('data'), list) else []

        if not isinstance(subscriptions, list):
            subscriptions = []

        results: List[ModelTokenInfo] = []
        default_model_name = "claude,codex"

        for item in subscriptions:
            if not isinstance(item, dict):
                continue

            # Get subscription plan details
            subscription_plan = item.get('subscriptionPlan', {}) if isinstance(item.get('subscriptionPlan'), dict) else {}

            # Package name from features (subscriptionPlan.features)
            raw_package_name = str(
                subscription_plan.get('features')
                or item.get('subscriptionPlanName')
                or subscription_plan.get('subscriptionName')
                or '88Code Subscription'
            )

            # Clean up package name - remove internal newlines and extra whitespace
            package_name = ' '.join(raw_package_name.split())

            # Truncate long package names for better display
            if len(package_name) > 50:
                package_name = package_name[:47] + '...'

            # Get plan type to determine calculation method
            plan_type = subscription_plan.get('planType', '').upper()

            # Extract credit information
            current_credits = item.get('currentCredits', 0)
            credit_limit = subscription_plan.get('creditLimit', 0)

            # Calculate used credits and remaining credits based on plan type
            if plan_type == 'PAY_PER_USE':
                # For PAY_PER_USE: use actual credit usage
                remaining_credits = current_credits
                used_credits = max(0.0, credit_limit - current_credits)
            else:
                # For MONTHLY/YEARLY: calculate based on time (remaining days)
                remaining_days = item.get('remainingDays', 0)
                try:
                    remaining_days = int(remaining_days) if remaining_days is not None else 0
                except (ValueError, TypeError):
                    remaining_days = 0

                # Calculate total days from startDate and endDate
                start_date_str = item.get('startDate')
                end_date_str = item.get('endDate')
                total_days = None

                if start_date_str and end_date_str:
                    try:
                        from datetime import datetime
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')
                        total_days = (end_date - start_date).days
                    except Exception:
                        total_days = None

                # If we couldn't calculate from dates, use billing cycle as fallback
                if total_days is None or total_days <= 0:
                    billing_cycle = item.get('billingCycle', '').lower()
                    if billing_cycle == 'monthly':
                        total_days = 30
                    elif billing_cycle == 'yearly':
                        total_days = 365
                    else:
                        total_days = 30

                # Calculate remaining and used credits based on time ratio
                if total_days > 0 and remaining_days >= 0:
                    remaining_ratio = min(1.0, float(remaining_days) / float(total_days))
                    elapsed_ratio = 1.0 - remaining_ratio
                    remaining_credits = credit_limit * remaining_ratio
                    used_credits = credit_limit * elapsed_ratio
                else:
                    # Fallback to actual credits
                    remaining_credits = current_credits
                    used_credits = max(0.0, credit_limit - current_credits)

            # Heuristics to extract numeric fields
            def _num(v) -> float:
                try:
                    if v is None:
                        return 0.0
                    if isinstance(v, (int, float)):
                        return float(v)
                    # Handle strings like "123", "123.45"
                    s = str(v).strip()
                    # Remove common separators
                    s = s.replace(',', '')
                    return float(s)
                except Exception:
                    return 0.0

            # Convert to numeric values
            total_tokens = _num(credit_limit)
            remaining_tokens = _num(current_credits)
            used_tokens = _num(used_credits)

            # Ensure non-negative values
            total_tokens = max(0.0, total_tokens)
            remaining_tokens = max(0.0, remaining_tokens)
            used_tokens = max(0.0, used_tokens)

            # Determine status based on isActive flag
            is_active = item.get('isActive', True)
            status = "active" if is_active else "inactive"

            # Extract expiry date (从 remainingDays 计算或直接使用 expireTime)
            expiry_date = None

            # 先尝试从 remainingDays 计算
            remaining_days = item.get('remainingDays') or subscription_plan.get('remainingDays')
            if remaining_days is not None:
                try:
                    from datetime import datetime, timedelta
                    days = int(remaining_days)
                    expiry_date = (datetime.utcnow() + timedelta(days=days)).strftime('%Y-%m-%d')
                except Exception:
                    expiry_date = None

            # 如果没有从 remainingDays 获取，尝试从 expireTime 获取
            if not expiry_date:
                expiry_timestamp = item.get('expireTime') or item.get('expiryDate') or subscription_plan.get('expireTime') or subscription_plan.get('expiryDate')
                if expiry_timestamp:
                    try:
                        # Handle Unix timestamp (seconds or milliseconds)
                        if isinstance(expiry_timestamp, (int, float)):
                            timestamp = expiry_timestamp
                            # If it looks like milliseconds (too large for seconds), convert
                            if timestamp > 1e11:
                                timestamp = timestamp / 1000
                            from datetime import datetime
                            expiry_date = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
                        else:
                            # Already a string, try to parse/normalize it
                            expiry_date = str(expiry_timestamp)
                    except Exception:
                        expiry_date = None

            # Extract reset count and reset time (only for MONTHLY/YEARLY, not for PAY_PER_USE)
            reset_count = None
            reset_time = None

            if plan_type != 'PAY_PER_USE':
                # Extract reset count (subscription resets/cycles) - 使用 resetTimes
                raw_reset_count = item.get('resetTimes') or item.get('resetCount') or item.get('renewCount') or subscription_plan.get('resetTimes') or subscription_plan.get('resetCount') or subscription_plan.get('renewCount')
                if raw_reset_count is not None:
                    try:
                        reset_count = int(raw_reset_count)
                    except (ValueError, TypeError):
                        reset_count = None

                # Extract reset time (next reset time) - 尝试从多个字段获取
                raw_reset_time = (item.get('resetTime') or item.get('nextResetTime') or
                                item.get('renewTime') or item.get('nextRenewTime') or
                                subscription_plan.get('resetTime') or subscription_plan.get('nextResetTime') or
                                subscription_plan.get('renewTime') or subscription_plan.get('nextRenewTime'))
                if raw_reset_time is not None:
                    try:
                        # Handle different time formats
                        if isinstance(raw_reset_time, (int, float)):
                            # Unix timestamp (seconds or milliseconds)
                            timestamp = raw_reset_time
                            # If it looks like milliseconds (too large for seconds), convert
                            if timestamp > 1e11:
                                timestamp = timestamp / 1000
                            from datetime import datetime
                            reset_time = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
                        else:
                            # String format, try to normalize it
                            reset_time = str(raw_reset_time)
                    except Exception:
                        reset_time = str(raw_reset_time) if raw_reset_time else None

            results.append(ModelTokenInfo(
                model=default_model_name,
                package=package_name,
                remaining_tokens=remaining_tokens,
                used_tokens=used_tokens,
                total_tokens=total_tokens,
                status=status,
                expiry_date=expiry_date,
                reset_count=reset_count,
                reset_time=reset_time
            ))

        # Sort by remaining tokens descending for readability
        results.sort(key=lambda x: x.remaining_tokens, reverse=True)
        return results
