"""
Moonshot platform handler
"""

import os
from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig

class MoonshotHandler(BasePlatformHandler):
    """Moonshot platform cost handler"""
    
    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for Moonshot platform"""
        return {
            "api_url": "https://api.moonshot.cn/v1/users/me/balance",
            "method": "GET",
            "auth_type": "bearer_token",
            "env_var": "MOONSHOT_API_KEY",
            "console_token": None,  # Will be set from localStorage token
            "org_id": None,  # Organization ID for multi-org accounts
            "ingress_cookie": None,  # HttpOnly INGRESSCOOKIE for authentication
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json"
            },
            "params": {},
            "data": {},
            "enabled": True
        }
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
        # Load platform-specific configuration from environment variables or separate config file
        self._load_env_config()

    def _load_env_config(self):
        """Load configuration from environment variables or separate config file."""
        # Try environment variables first
        env_console_token = os.getenv('MOONSHOT_CONSOLE_TOKEN')
        env_org_id = os.getenv('MOONSHOT_ORG_ID')
        env_ingress_cookie = os.getenv('MOONSHOT_INGRESS_COOKIE')

        if env_console_token:
            self.config.console_token = env_console_token

        if env_org_id:
            self.config.org_id = env_org_id

        if env_ingress_cookie:
            self.config.ingress_cookie = env_ingress_cookie

        if env_console_token or env_org_id or env_ingress_cookie:
            return

        # Try separate config file
        import yaml
        from pathlib import Path
        config_path = Path.home() / '.llm_balance' / 'moonshot_config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    moon_config = yaml.safe_load(f) or {}
                    if 'console_token' in moon_config:
                        self.config.console_token = moon_config['console_token']
                    if 'org_id' in moon_config:
                        self.config.org_id = moon_config['org_id']
                    if 'ingress_cookie' in moon_config:
                        self.config.ingress_cookie = moon_config['ingress_cookie']
            except Exception as e:
                pass

    def get_balance(self) -> CostInfo:
        """Get cost information from Moonshot"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for Moonshot")

        # Check if we have console token and org_id for organization account
        console_token = getattr(self.config, 'console_token', None)
        org_id = getattr(self.config, 'org_id', None)


        if console_token and org_id:
            try:
                # Try organization account API first
                return self._get_balance_with_org_account(console_token, org_id)
            except Exception as e:
                # Fall back to traditional API key method
                api_key = os.getenv('MOONSHOT_API_KEY')
                if not api_key:
                    raise ValueError("Moonshot API key required. Set MOONSHOT_API_KEY environment variable.")
                return self._get_balance_with_api_key(api_key)
        else:
            # Use traditional API key method
            api_key = os.getenv('MOONSHOT_API_KEY')
            if not api_key:
                raise ValueError("Moonshot API key required. Set MOONSHOT_API_KEY environment variable.")
            return self._get_balance_with_api_key(api_key)
    
    def _get_balance_with_api_key(self, api_key: str) -> CostInfo:
        """Get balance using API key authentication"""
        headers = {
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }

        # Get organization ID if configured
        org_id = getattr(self.config, 'org_id', None)
        params = {}
        if org_id:
            params['org_id'] = org_id

        response = self._make_request(
            url=self.config.api_url,
            headers=headers,
            params=params
        )

        if not response:
            raise ValueError("No response from Moonshot API")

        # Extract balance from response
        data = response.get('data', {})

        available_balance = self._validate_balance(data.get('available_balance', 0.0), "available_balance")
        voucher_balance = self._validate_balance(data.get('voucher_balance', 0.0), "voucher_balance")
        cash_balance = self._validate_balance(data.get('cash_balance', 0.0), "cash_balance")


        # Use cash_balance as the primary balance since it represents actual money
        # available_balance includes voucher_balance which may not be real money
        balance = cash_balance if cash_balance > 0 else available_balance

        # Try to get spent information using console token
        # Note: For traditional API key method, spent info is not available
        # Spent info is only available through organization account API
        spent = self._get_spent_with_console_token()

        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance,
            currency='CNY',  # Moonshot uses CNY
            spent=spent,
            spent_currency='CNY' if spent > 0 else '-',
            raw_data={
                'available_balance': available_balance,
                'voucher_balance': voucher_balance,
                'cash_balance': cash_balance,
                'display_balance': balance,
                'full_response': response
            }
        )
    
    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "Moonshot"
    
    def _get_balance_with_org_account(self, console_token: str, org_id: str) -> CostInfo:
        """Get balance and spent using organization account API with token + cookie authentication"""
        try:

            # Build organization account API URL
            org_url = f"https://platform.moonshot.cn/api?endpoint=organizationAccountInfo&oid={org_id}"

            headers = {
                'Authorization': f'Bearer {console_token}',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Referer': 'https://platform.moonshot.cn/console/account'
            }


            # Get cookies for additional authentication
            cookies = {}

            # Try configured ingress_cookie first
            ingress_cookie = getattr(self.config, 'ingress_cookie', None)
            if ingress_cookie:
                cookies['INGRESSCOOKIE'] = ingress_cookie

            # If no ingress_cookie, try to get from browser
            try:
                # Try multiple Moonshot domains
                for domain in ['.moonshot.cn', 'moonshot.cn', 'platform.moonshot.cn']:
                    domain_cookies = self._get_cookies(domain)
                    if domain_cookies:
                        cookies.update(domain_cookies)
                        break
                # Show authentication-related cookies
                for key, value in cookies.items():
                    if any(word in key.lower() for word in ['token', 'auth', 'session', 'user', 'ingress']):
                        pass
            except Exception as e:
                pass

            # Make request with both headers and cookies
            response = self._make_request(url=org_url, headers=headers, cookies=cookies)

            if not response:
                raise ValueError("No response from Moonshot organization API")

            # Extract data from response
            data = response.get('data', {})

            # Moonshot returns amounts in a custom unit, convert to "yuan"
            balance_raw = data.get('cur', 0.0)  # Current balance in raw unit
            spent_raw = data.get('use', 0.0)     # Spent amount in raw unit

            # Convert from raw unit to yuan (divide by 100000)
            balance = balance_raw / 100000.0 if balance_raw else 0.0
            spent = spent_raw / 100000.0 if spent_raw else 0.0

            # Validate balance and spent (now in yuan)
            balance = self._validate_balance(balance, "cur")
            spent = self._validate_balance(spent, "use")

            return CostInfo(
                platform=self.get_platform_name(),
                balance=balance,
                currency='CNY',  # Moonshot uses CNY
                spent=spent,
                spent_currency='CNY' if spent > 0 else '-',
                raw_data={
                    'cur': data.get('cur'),
                    'voucher_cur': data.get('voucher_cur'),
                    'acc': data.get('acc'),
                    'voucher_acc': data.get('voucher_acc'),
                    'voucher_expired': data.get('voucher_expired'),
                    'recharge_bonus_percent': data.get('recharge_bonus_percent'),
                    'use': data.get('use'),
                    'full_response': response
                }
            )

        except Exception as e:
            raise ValueError(f"Failed to get organization account info for Moonshot: {e}")

    def _get_spent_with_console_token(self) -> float:
        """Get spent amount using console token from localStorage (legacy method)"""
        try:
            # Check if we have a console token configured
            console_token = getattr(self.config, 'console_token', None)
            if not console_token:
                return 0.0

            # Get organization ID if configured
            org_id = getattr(self.config, 'org_id', None)

            # If we have both console token and org_id, spent info is already included in the org API response
            # No need for separate billing API call since Moonshot doesn't have this endpoint
            return 0.0

        except Exception as e:
            return 0.0

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get model-level token information from Moonshot"""
        raise NotImplementedError(f"Model token checking not implemented for {self.get_platform_name()}")
