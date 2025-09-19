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

        - Total cost = sum([item.cost for item in data])  # All subscriptions (active + inactive)
        - Balance = sum([item.cost * remaining/total for item in data if item.isActive])  # Only active
        - Spent = Total cost - Balance
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

        # Extract balance and spent from subscription data
        total_cost = 0.0
        balance = 0.0
        spent = 0.0

        try:
            data = response.get('data', []) if isinstance(response, dict) else []
            if isinstance(data, list):
                # Calculate total cost from ALL subscriptions (both active and inactive)
                for item in data:
                    if isinstance(item, dict):
                        cost = item.get('cost', 0)
                        if cost is not None:
                            total_cost += float(str(cost).replace(',', '').strip())

                # Calculate balance based on usage ratio (only active subscriptions)
                for item in data:
                    if isinstance(item, dict) and item.get('isActive'):
                        subscription_plan = item.get('subscriptionPlan', {}) if isinstance(item.get('subscriptionPlan'), dict) else {}
                        current_credits = item.get('currentCredits', 0)
                        credit_limit = subscription_plan.get('creditLimit', 0)
                        cost = item.get('cost', 0)

                        if cost is not None and credit_limit > 0:
                            usage_ratio = float(current_credits) / float(credit_limit)
                            item_cost = float(str(cost).replace(',', '').strip())
                            balance += item_cost * usage_ratio

                # Calculate spent
                spent = total_cost - balance
        except Exception:
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
            - For each item, extract subscription plan information
            - Package name = features (from subscriptionPlan)
            - Total = creditLimit (from subscriptionPlan)
            - Remaining = currentCredits (from data item)
        """
        data = response if isinstance(response, dict) else {}
        subscriptions = data.get('data', []) if isinstance(data.get('data'), list) else []

        if not isinstance(subscriptions, list):
            subscriptions = []

        results: List[ModelTokenInfo] = []
        default_model_name = "claude,gpt-5,gpt-5-codex"

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

            # Extract credit information
            current_credits = item.get('currentCredits', 0)
            credit_limit = subscription_plan.get('creditLimit', 0)

            # Calculate used credits
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

            results.append(ModelTokenInfo(
                model=default_model_name,
                package=package_name,
                remaining_tokens=remaining_tokens,
                used_tokens=used_tokens,
                total_tokens=total_tokens,
                status=status
            ))

        # Sort by remaining tokens descending for readability
        results.sort(key=lambda x: x.remaining_tokens, reverse=True)
        return results