"""
YesCode third-party relay handler
"""

import os
from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, PlatformTokenInfo, ModelTokenInfo, CostInfo
from ..config import PlatformConfig


class YesCodeHandler(BasePlatformHandler):
    """YesCode relay platform handler."""

    @classmethod
    def get_default_config(cls) -> dict:
        """Default configuration for YesCode balance query via console_token auth."""
        return {
            "display_name": "YesCode",
            "handler_class": "YesCodeHandler",
            "description": "YesCode API relay (co.yes.vg)",
            "api_url": "https://co.yes.vg/api/v1/user/balance",
            "method": "GET",
            "auth_type": "console_token",
            "env_var": None,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Cache-Control": "no-cache",
                "DNT": "1",
                "Pragma": "no-cache",
                "Priority": "u=1, i",
                "Referer": "https://co.yes.vg/dashboard",
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
        env_console_token = os.getenv('YESCODE_CONSOLE_TOKEN')
        if env_console_token:
            self.config.console_token = env_console_token
            return

        # Try separate config file
        import yaml
        from pathlib import Path
        config_path = Path.home() / '.llm_balance' / 'yescode_config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    yescode_config = yaml.safe_load(f) or {}
                    if 'console_token' in yescode_config:
                        self.config.console_token = yescode_config['console_token']
            except Exception:
                pass

    def get_platform_name(self) -> str:
        return "YesCode"

    def get_balance(self) -> CostInfo:
        """Return cost info using balance and payment history data from API.

        Balance API returns:
        {
            "balance": 50,
            "pay_as_you_go_balance": 50,
            "subscription_balance": 0,
            "total_balance": 50
        }

        Payment History API returns:
        {
            "history": [
                {
                    "type": "payment",
                    "subscription_plan": {
                        "initial_balance": 50
                    }
                }
            ]
        }

        - Balance = balance (current balance)
        - Total = sum of initial_balance from all successful payments
        - Spent = Total - balance
        """
        if not getattr(self.config, 'api_url', None):
            raise ValueError("No API URL configured for YesCode")

        headers = (self.config.headers or {}).copy()

        # Get console_token from config (loaded from env var or separate config file)
        console_token = getattr(self.config, 'console_token', None)
        if not console_token:
            raise ValueError(
                "YesCode requires console_token to be configured. Please set it using:\n"
                "1. Environment variable: export YESCODE_CONSOLE_TOKEN=YOUR_TOKEN\n"
                "2. Separate config file: ~/.llm_balance/yescode_config.yaml\n"
                "   console_token: YOUR_TOKEN"
            )

        # Set required headers
        headers['Authorization'] = f'Bearer {console_token}'

        # Make the API request for balance
        balance_response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers
        )

        if not balance_response:
            raise ValueError("No response from YesCode balance API")

        # Make API request for payment history to calculate total
        history_url = "https://co.yes.vg/api/v1/user/payment/history?page=1&limit=20"
        history_response = self._make_request(
            url=history_url,
            method="GET",
            headers=headers
        )

        # Extract balance and calculate spent
        balance = 0.0
        total_paid = 0.0
        spent = 0.0

        try:
            if isinstance(balance_response, dict):
                # Get current balance from response
                balance = float(balance_response.get('balance', 0))

            # Calculate total from payment history
            if isinstance(history_response, dict):
                history = history_response.get('history', [])
                if isinstance(history, list):
                    for payment in history:
                        if isinstance(payment, dict) and payment.get('status') == 'TRADE_SUCCESS':
                            # Get initial_balance from subscription_plan nested in details
                            details = payment.get('details', {})
                            if isinstance(details, dict):
                                subscription_plan = details.get('subscription_plan', {})
                                if isinstance(subscription_plan, dict):
                                    initial_balance = subscription_plan.get('initial_balance', 0)
                                    if initial_balance is not None:
                                        total_paid += float(initial_balance)

            # Calculate spent as total paid - current balance
            spent = max(0.0, total_paid - balance)
        except Exception:
            balance = 0.0
            spent = 0.0
            total_paid = 0.0

        # Combine responses for raw data
        combined_raw_data = {
            'balance': balance_response,
            'payment_history': history_response,
            'calculated_total_paid': total_paid,
            'calculated_spent': spent
        }

        # Validate final balance and spent
        balance = self._validate_balance(balance, "balance")
        spent = self._validate_balance(spent, "spent")

        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance,
            currency='CNY',
            spent=spent,
            spent_currency='CNY',
            raw_data=combined_raw_data
        )

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Query YesCode usage data and create usage package from usage summary.

        Authentication:
            - Use console_token from environment variables or config file
            - Set header: Authorization: Bearer <console_token>

        Data sources:
            - GET https://co.yes.vg/api/v1/user/balance (for balance info)
            - GET https://co.yes.vg/api/v1/user/usage/summary (for token usage)

        Calculation:
            - Total tokens = (Total paid * Used tokens) / Spent amount
            - Used tokens = total_input_tokens + total_output_tokens
            - Remaining tokens = Total tokens - Used tokens

        Models:
            - Generic model name: "All Models"
            - Package name: "YesCode Account"
        """
        if not getattr(self.config, 'api_url', None):
            raise ValueError("No API URL configured for YesCode")

        headers = (self.config.headers or {}).copy()

        # Get console_token from config (loaded from env var or separate config file)
        console_token = getattr(self.config, 'console_token', None)
        if not console_token:
            raise ValueError(
                "YesCode requires console_token to be configured. Please set it using:\n"
                "1. Environment variable: export YESCODE_CONSOLE_TOKEN=YOUR_TOKEN\n"
                "2. Separate config file: ~/.llm_balance/yescode_config.yaml\n"
                "   console_token: YOUR_TOKEN"
            )

        # Set required headers
        headers['Authorization'] = f'Bearer {console_token}'

        # Make API requests for both balance and usage data
        balance_response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers
        )

        usage_url = "https://co.yes.vg/api/v1/user/usage/summary"
        usage_response = self._make_request(
            url=usage_url,
            method="GET",
            headers=headers
        )

        if not balance_response:
            raise ValueError("No response from YesCode balance API")
        if not usage_response:
            raise ValueError("No response from YesCode usage API")

        # Extract token information and create models
        models = self._extract_models_from_usage(balance_response, usage_response)

        # Combine responses for raw data
        combined_raw_data = {
            'balance': balance_response,
            'usage_summary': usage_response
        }

        return PlatformTokenInfo(
            platform=self.get_platform_name(),
            models=models,
            raw_data=combined_raw_data
        )

    def _extract_models_from_usage(self, balance_response: Dict[str, Any], usage_response: Dict[str, Any]) -> List[ModelTokenInfo]:
        """Extract ModelTokenInfo list from balance and usage responses.

        Balance response contains:
        - balance: current balance
        - pay_as_you_go_balance: pay-as-you-go balance
        - subscription_balance: subscription balance

        Usage response contains:
        - total_input_tokens: total input tokens used
        - total_output_tokens: total output tokens used
        """
        results: List[ModelTokenInfo] = []

        # Helper function to convert to numeric value
        def _num(v) -> float:
            try:
                if v is None:
                    return 0.0
                if isinstance(v, (int, float)):
                    return float(v)
                s = str(v).strip()
                s = s.replace(',', '')
                return float(s)
            except Exception:
                return 0.0

        # Get current balance from balance response
        current_balance = _num(balance_response.get('balance', 0))

        # Get token usage from usage response
        total_input_tokens = _num(usage_response.get('total_input_tokens', 0))
        total_output_tokens = _num(usage_response.get('total_output_tokens', 0))
        used_tokens = total_input_tokens + total_output_tokens

        # Get payment history to calculate total paid
        payment_history_url = "https://co.yes.vg/api/v1/user/payment/history?page=1&limit=20"
        headers = (self.config.headers or {}).copy()
        headers['Authorization'] = f'Bearer {getattr(self.config, "console_token", "")}'
        history_response = self._make_request(
            url=payment_history_url,
            method="GET",
            headers=headers
        )

        # Calculate total paid from payment history
        total_paid = 0.0
        if isinstance(history_response, dict):
            history = history_response.get('history', [])
            if isinstance(history, list):
                for payment in history:
                    if isinstance(payment, dict) and payment.get('status') == 'TRADE_SUCCESS':
                        details = payment.get('details', {})
                        if isinstance(details, dict):
                            subscription_plan = details.get('subscription_plan', {})
                            if isinstance(subscription_plan, dict):
                                initial_balance = subscription_plan.get('initial_balance', 0)
                                if initial_balance is not None:
                                    total_paid += float(initial_balance)

        # Calculate spent amount
        spent = max(0.0, total_paid - current_balance)

        # Calculate total tokens based on usage rate
        # Total = (Total paid * Used tokens) / Spent amount
        if spent > 0 and used_tokens > 0:
            total_tokens = (total_paid * used_tokens) / spent
            remaining_tokens = max(0.0, total_tokens - used_tokens)
        else:
            # If no usage or no spent, estimate based on current balance
            # Assume remaining = current balance * 1000 tokens per CNY
            remaining_tokens = current_balance * 1000
            # Total = used + remaining
            total_tokens = used_tokens + remaining_tokens

        # Create model info
        results.append(ModelTokenInfo(
            model="claude,codex",
            package="YesCode Account",
            remaining_tokens=remaining_tokens,
            used_tokens=used_tokens,
            total_tokens=total_tokens,
            status="active" if current_balance > 0 else "inactive"
        ))

        # Sort by remaining tokens descending for readability
        results.sort(key=lambda x: x.remaining_tokens, reverse=True)
        return results