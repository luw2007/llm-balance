"""
DeepSeek platform handler
"""

import os
from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig

class DeepSeekHandler(BasePlatformHandler):
    """DeepSeek platform cost handler"""
    
    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for DeepSeek platform"""
        return {
            "api_url": "https://api.deepseek.com/v1/user/balance",
            "method": "GET",
            "auth_type": "bearer_token",
            "env_var": "DEEPSEEK_API_KEY",
            "console_token": None,  # Will be set from localStorage userToken
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
        # Try environment variable first
        env_console_token = os.getenv('DEEPSEEK_CONSOLE_TOKEN')
        if env_console_token:
            self.config.console_token = env_console_token
            return

        # Try separate config file
        import yaml
        from pathlib import Path
        config_path = Path.home() / '.llm_balance' / 'deepseek_config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    deep_config = yaml.safe_load(f) or {}
                    if 'console_token' in deep_config:
                        self.config.console_token = deep_config['console_token']
            except Exception as e:
                pass

    def get_balance(self) -> CostInfo:
        """Get cost information from DeepSeek"""
        # Check if we have console token for enhanced spent calculation
        console_token = getattr(self.config, 'console_token', None)

        if console_token:
            # Use enhanced method with spent calculation from invoices
            return self._get_balance_with_enhanced_spent(console_token)
        else:
            # Use traditional method
            return self._get_balance_with_api_key()
    
    def _get_balance_with_api_key(self) -> CostInfo:
        """Get balance using API key authentication"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for DeepSeek")
        
        # Prepare authentication
        headers = self.config.headers.copy() if self.config.headers else {}
        
        # Get API key from environment variable
        api_key = os.getenv(self.config.env_var or 'DEEPSEEK_API_KEY')
        
        if not api_key:
            raise ValueError("DeepSeek API key required. Set DEEPSEEK_API_KEY environment variable.")
        
        headers['Authorization'] = f'Bearer {api_key}'
        
        # Make API request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers
        )
        
        if not response:
            raise ValueError("No response from DeepSeek API")
        
        # Extract balance and currency from response
        balance = self._extract_balance(response)
        currency = self._extract_currency(response)
        
        # Try to get spent information using console token
        spent = self._get_spent_with_console_token()
        
        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance or 0.0,
            currency=currency or 'CNY',
            spent=spent,
            spent_currency='CNY' if spent > 0 else '-',
            raw_data=response
        )
    
    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "DeepSeek"
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from DeepSeek API response"""
        balance_infos = response.get('balance_infos', [])
        if balance_infos:
            total_balance = balance_infos[0].get('total_balance', '0')
            try:
                balance_float = float(total_balance)
                return self._validate_balance(balance_float, "total_balance")
            except (ValueError, TypeError):
                return None
        return 0.0
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from DeepSeek API response"""
        balance_infos = response.get('balance_infos', [])
        if balance_infos:
            return balance_infos[0].get('currency', 'CNY')
        return 'CNY'

    def _get_balance_with_enhanced_spent(self, console_token: str) -> CostInfo:
        """Get balance using API key and enhanced spent calculation from invoices"""
        try:

            # Get balance using traditional API key method
            api_key = os.getenv(self.config.env_var or 'DEEPSEEK_API_KEY')
            if not api_key:
                raise ValueError("DeepSeek API key required. Set DEEPSEEK_API_KEY environment variable.")

            # Get balance from traditional API
            balance_info = self._get_balance_from_api_key(api_key)
            balance = balance_info.balance
            currency = balance_info.currency

            # Calculate spent from invoices

            spent = self._calculate_spent_from_invoices(console_token)

            result = CostInfo(
                platform=self.get_platform_name(),
                balance=balance,
                currency=currency,
                spent=spent,
                spent_currency='CNY' if spent > 0 else '-',
                raw_data={
                    'balance': balance,
                    'currency': currency,
                    'spent': spent,
                    'spent_calculation_method': 'invoices',
                    'full_balance_response': balance_info.raw_data
                }
            )

            return result

        except Exception as e:

            print(f"Warning: Enhanced spent calculation failed, falling back to traditional method: {e}")
            return self._get_balance_with_api_key()

    def _get_balance_from_api_key(self, api_key: str) -> CostInfo:
        """Get balance using API key authentication (extracted from original method)"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for DeepSeek")

        # Prepare authentication
        headers = self.config.headers.copy() if self.config.headers else {}
        headers['Authorization'] = f'Bearer {api_key}'

        # Make API request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers
        )

        if not response:
            raise ValueError("No response from DeepSeek API")

        # Extract balance and currency from response
        balance = self._extract_balance(response)
        currency = self._extract_currency(response)

        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance,
            currency=currency,
            spent=0.0,  # Will be calculated separately
            spent_currency='-',
            raw_data=response
        )

    def _calculate_spent_from_invoices(self, console_token: str) -> float:
        """Calculate spent amount from successful payment invoices"""
        try:

            # Make request to get all invoices
            invoice_url = "https://platform.deepseek.com/auth-api/v0/users/get_all_invoice"
            headers = {
                'Authorization': f'Bearer {console_token}',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Referer': 'https://platform.deepseek.com/transactions',
                'X-App-Version': '20240425.0'
            }

            response = self._make_request(url=invoice_url, headers=headers)

            if not response:
                return 0.0

            # Extract payment orders from response
            data = response.get('data', {})
            biz_data = data.get('biz_data', {})
            invoices = biz_data.get('invoices', {})
            payment_orders = invoices.get('payment_orders', [])

            # Sum successful payment amounts to get total recharge
            total_recharge = 0.0
            successful_orders = []
            for order in payment_orders:
                order_status = order.get('payment_order_status')
                amount = order.get('amount', '0')

                if order_status == 'SUCCESS':
                    try:
                        amount_float = float(amount)
                        total_recharge += amount_float
                        successful_orders.append(order)
                    except (ValueError, TypeError):
            
                        continue


            # Get current balance from API
            api_key = os.getenv(self.config.env_var or 'DEEPSEEK_API_KEY')

            if not api_key:
                return 0.0

            balance_info = self._get_balance_from_api_key(api_key)
            current_balance = balance_info.balance

            # Calculate spent as: total_recharge - current_balance
            spent = max(0.0, total_recharge - current_balance)

            return spent

        except Exception as e:
            print(f"Warning: Failed to calculate spent from invoices: {e}")
            return 0.0

    def _get_spent_with_console_token(self) -> float:
        """Get spent amount using console token from localStorage userToken (legacy method)"""
        try:
            # Check if we have a console token configured
            console_token = getattr(self.config, 'console_token', None)
            if not console_token:
                return 0.0

            # Make request to get billing information
            spent_url = "https://api.deepseek.com/v1/user/billing/usage"
            headers = {
                'Authorization': f'Bearer {console_token}',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json'
            }

            response = self._make_request(url=spent_url, headers=headers)
            if not response:
                return 0.0

            # Extract spent amount from response
            # DeepSeek API response structure may vary, adapt as needed
            total_usage = response.get('total_usage', 0.0)
            if not total_usage:
                # Try alternative field names
                total_usage = response.get('amount', {}).get('value', 0.0)
                if not total_usage:
                    total_usage = response.get('data', {}).get('total_usage', 0.0)

            try:
                return float(total_usage)
            except (ValueError, TypeError):
                return 0.0

        except Exception as e:
            print(f"Warning: Failed to get spent amount for DeepSeek: {e}")
            return 0.0

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get model-level token information from DeepSeek"""
        raise NotImplementedError(f"Model token checking not implemented for {self.get_platform_name()}")
