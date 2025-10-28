"""
MiniMax platform handler
MiniMax is a Chinese AI platform providing API services
"""

import os
from typing import Optional
from .base import BasePlatformHandler, CostInfo, PlatformTokenInfo
from ..config import PlatformConfig

class MiniMaxHandler(BasePlatformHandler):
    """MiniMax platform cost handler"""

    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for MiniMax platform"""
        return {
            "balance_url": "https://www.minimaxi.com/account/query_balance",
            "method": "GET",
            "auth_type": "bearer",
            "env_var": "MINIMAX_AUTHORIZATION",
            "group_id": None,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Origin": "https://platform.minimaxi.com",
                "Referer": "https://platform.minimaxi.com/",
            },
            "params": {},
            "data": {},
            "enabled": True
        }

    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
        self.group_id: Optional[str] = None
        self.bearer_token: Optional[str] = None
        # Load platform-specific configuration (token + group id)
        self._load_env_config()

        # Fall back to platform configuration if group_id was provided there
        if not self.group_id:
            group_id = getattr(config, 'group_id', None)
            if not group_id and config.params:
                group_id = config.params.get('group_id')
            if group_id:
                self.group_id = str(group_id)

    def _load_env_config(self):
        """Load bearer token and group_id from environment variables or separate config file."""
        # Try environment variable for bearer token first
        bearer_token = os.getenv('MINIMAX_AUTHORIZATION')
        if bearer_token:
            # Remove 'Bearer ' prefix if present
            if bearer_token.startswith('Bearer '):
                bearer_token = bearer_token[7:]
            self.bearer_token = bearer_token
            return

        # Try to extract from cookies
        try:
            import yaml
            from pathlib import Path
            
            config_path = Path.home() / '.llm_balance' / 'minimax_config.yaml'
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    minimax_config = yaml.safe_load(f) or {}
                    if 'authorization' in minimax_config:
                        token = minimax_config['authorization']
                        if token.startswith('Bearer '):
                            token = token[7:]
                        self.bearer_token = token
                    if not self.group_id and 'group_id' in minimax_config:
                        group = minimax_config['group_id']
                        if group:
                            self.group_id = str(group)
        except Exception as e:
            pass

    def get_balance(self) -> CostInfo:
        """Get cost information from MiniMax"""
        # Check if bearer token is available
        if not self.bearer_token:
            raise ValueError(
                "MiniMax authorization token not found.\n"
                "Please set MINIMAX_AUTHORIZATION environment variable with your Bearer token, or\n"
                "Create ~/.llm_balance/minimax_config.yaml with:\n"
                "  authorization: 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...'\n"
                "\nTo get the token, follow these steps:\n"
                "1. Login to https://platform.minimaxi.com\n"
                "2. Open browser DevTools (F12) and go to Network tab\n"
                "3. Visit https://www.minimaxi.com/backend/account\n"
                "4. Find the response and copy the 'authorization' field"
            )

        if not self.group_id:
            raise ValueError(
                "MiniMax group_id not found.\n"
                "Add `group_id` to ~/.llm_balance/minimax_config.yaml under the key `group_id`."
            )

        # Get balance using the group_id and bearer token
        balance = self._get_balance_amount()

        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance or 0.0,
            spent="-",  # MiniMax doesn't support spent tracking
            currency="CNY",
            raw_data={
                "group_id": self.group_id,
                "note": "MiniMax balance is in RMB (CNY), spent tracking not supported"
            }
        )

    def _get_balance_amount(self) -> Optional[float]:
        """Get balance amount from MiniMax balance endpoint"""
        try:
            headers = self.config.headers.copy() if self.config.headers else {}
            headers['Authorization'] = f'Bearer {self.bearer_token}'

            # Add query parameter for group_id
            url = f"{self.config.balance_url}?GroupId={self.group_id}"

            # Make request to get balance
            response = self._make_request(
                url=url,
                method="GET",
                headers=headers
            )

            if not response:
                return 0.0

            # Extract balance from response
            data = response.get('data', response)

            if isinstance(data, dict):
                # Try different field names for balance
                balance_fields = ['available_amount', 'balance', 'available', 'amount']
                for field in balance_fields:
                    if field in data:
                        try:
                            balance_value = float(data[field])
                            return self._validate_balance(balance_value, field)
                        except (ValueError, TypeError):
                            continue

            return 0.0

        except Exception as e:
            print(f"Warning: Failed to get balance amount from MiniMax: {e}")
            return 0.0

    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "MiniMax"

    def get_model_tokens(self) -> PlatformTokenInfo:
        """MiniMax does not support token usage tracking"""
        return PlatformTokenInfo(
            platform=self.get_platform_name(),
            models=[],
            raw_data={'error': 'MiniMax does not support package/token tracking'}
        )
