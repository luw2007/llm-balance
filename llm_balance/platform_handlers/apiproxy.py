"""
API-Proxy platform handler
API-Proxy.me is a free public API relay service
"""

import os
from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig

class APIProxyHandler(BasePlatformHandler):
    """API-Proxy platform cost handler"""

    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for API-Proxy platform"""
        return {
            "api_url": "https://api-proxy.me/api/user/balance",
            "usage_url": "https://api-proxy.me/api/user/usage", 
            "method": "GET",
            "auth_type": "api_key",
            "env_var": "APIPROXY_API_KEY",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Content-Type": "application/json"
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
        api_key = os.getenv('APIPROXY_API_KEY')
        if api_key:
            self.config.headers['Authorization'] = f'Bearer {api_key}'
            return

        # Try separate config file
        import yaml
        from pathlib import Path
        config_path = Path.home() / '.llm_balance' / 'apiproxy_config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    apiproxy_config = yaml.safe_load(f) or {}
                    if 'api_key' in apiproxy_config:
                        self.config.headers['Authorization'] = f'Bearer {apiproxy_config["api_key"]}'
                    if 'base_url' in apiproxy_config:
                        base_url = apiproxy_config['base_url']
                        if not base_url.endswith('/'):
                            base_url += '/'
                        self.config.api_url = base_url + "api/user/balance"
                        self.config.usage_url = base_url + "api/user/usage"
            except Exception as e:
                pass

    def get_balance(self) -> CostInfo:
        """Get cost information from API-Proxy"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for API-Proxy")

        # Check if API key is configured
        if 'Authorization' not in self.config.headers:
            raise ValueError("API-Proxy API key required. Set APIPROXY_API_KEY environment variable or configure in apiproxy_config.yaml")

        # Make API request for balance
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=self.config.headers
        )

        if not response:
            raise ValueError("No response from API-Proxy API")

        # Extract balance and currency from response
        balance = self._extract_balance(response)
        currency = self._extract_currency(response)

        # Try to get spent information
        spent = self._get_spent_information()

        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance or 0.0,
            currency=currency or 'USD',
            spent=spent,
            spent_currency='USD' if spent > 0 else '-',
            raw_data=response
        )

    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from API-Proxy API response"""
        data = response.get('data', response)

        # Try different possible balance field names
        balance_fields = ['balance', 'quota', 'remaining_quota', 'credit', 'amount', 'remaining_balance']

        for field in balance_fields:
            if field in data:
                try:
                    balance_value = float(data[field])
                    return self._validate_balance(balance_value, field)
                except (ValueError, TypeError):
                    continue

        # Try nested fields
        if 'user' in data:
            user_data = data['user']
            for field in balance_fields:
                if field in user_data:
                    try:
                        balance_value = float(user_data[field])
                        return self._validate_balance(balance_value, f"user.{field}")
                    except (ValueError, TypeError):
                        continue

        return 0.0

    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from API-Proxy API response"""
        data = response.get('data', response)

        # Try to find currency information
        currency_fields = ['currency', 'unit', 'currency_code']

        for field in currency_fields:
            if field in data:
                return str(data[field]).upper()

        # Try nested fields
        if 'user' in data:
            user_data = data['user']
            for field in currency_fields:
                if field in user_data:
                    return str(user_data[field]).upper()

        # Default to USD for API-Proxy
        return 'USD'

    def _get_spent_information(self) -> float:
        """Get spent information from usage API"""
        try:
            # Check if usage URL is configured
            usage_url = getattr(self.config, 'usage_url', None)
            if not usage_url:
                return 0.0

            # Make request to usage API
            response = self._make_request(
                url=usage_url,
                method='GET',
                headers=self.config.headers
            )

            if not response:
                return 0.0

            # Extract spent information from response
            data = response.get('data', response)

            # Try different spent field names
            spent_fields = ['used_quota', 'spent', 'consumed', 'usage', 'total_usage', 'cost']

            for field in spent_fields:
                if field in data:
                    try:
                        spent_value = float(data[field])
                        return self._validate_balance(spent_value, field)
                    except (ValueError, TypeError):
                        continue

            # Try nested fields
            if 'statistics' in data:
                stats_data = data['statistics']
                for field in spent_fields:
                    if field in stats_data:
                        try:
                            spent_value = float(stats_data[field])
                            return self._validate_balance(spent_value, f"statistics.{field}")
                        except (ValueError, TypeError):
                            continue

            return 0.0

        except Exception as e:
            print(f"Warning: Failed to get spent information for API-Proxy: {e}")
            return 0.0

    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "API-Proxy"

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get model-level token information from API-Proxy"""
        try:
            # Check if usage URL is configured
            usage_url = getattr(self.config, 'usage_url', None)
            if not usage_url:
                return PlatformTokenInfo(
                    platform=self.get_platform_name(),
                    models=[],
                    raw_data={'error': 'No usage endpoint configured'}
                )

            # Make request to usage API
            response = self._make_request(
                url=usage_url,
                method='GET',
                headers=self.config.headers
            )

            if not response:
                return PlatformTokenInfo(
                    platform=self.get_platform_name(),
                    models=[],
                    raw_data={'error': 'No response from usage API'}
                )

            # Parse model usage data
            models = []
            data = response.get('data', response)

            # API-Proxy might return usage in different formats
            if isinstance(data, list):
                # Array of model usage entries
                for item in data:
                    if isinstance(item, dict):
                        model_info = self._parse_model_usage(item)
                        if model_info:
                            models.append(model_info)
            elif isinstance(data, dict):
                # Single object with model usage data
                if 'models' in data:
                    for model_name, model_data in data['models'].items():
                        if isinstance(model_data, dict):
                            model_info = self._parse_model_usage({
                                'model': model_name,
                                **model_data
                            })
                            if model_info:
                                models.append(model_info)
                elif 'usage' in data:
                    # Parse usage data
                    usage_data = data['usage']
                    if isinstance(usage_data, dict):
                        for model_name, model_data in usage_data.items():
                            if isinstance(model_data, dict):
                                model_info = self._parse_model_usage({
                                    'model': model_name,
                                    **model_data
                                })
                                if model_info:
                                    models.append(model_info)

            return PlatformTokenInfo(
                platform=self.get_platform_name(),
                models=models,
                raw_data=response
            )

        except Exception as e:
            print(f"Warning: Failed to get model token information for API-Proxy: {e}")
            return PlatformTokenInfo(
                platform=self.get_platform_name(),
                models=[],
                raw_data={'error': str(e)}
            )

    def _parse_model_usage(self, model_data: Dict[str, Any]) -> Optional[ModelTokenInfo]:
        """Parse model usage data into ModelTokenInfo"""
        try:
            model_name = model_data.get('model', model_data.get('name', 'Unknown'))

            # Try different field names for token usage
            used_tokens = self._extract_token_value(model_data, ['used_tokens', 'usage', 'consumed', 'input_tokens', 'prompt_tokens'])
            total_tokens = self._extract_token_value(model_data, ['total_tokens', 'quota', 'limit', 'total_quota'])
            remaining_tokens = self._extract_token_value(model_data, ['remaining_tokens', 'remaining', 'left', 'remaining_quota'])

            # Calculate missing values if possible
            if total_tokens > 0 and used_tokens >= 0 and remaining_tokens == 0:
                remaining_tokens = total_tokens - used_tokens
            elif total_tokens > 0 and remaining_tokens >= 0 and used_tokens == 0:
                used_tokens = total_tokens - remaining_tokens

            return ModelTokenInfo(
                model=model_name,
                package=model_name,  # API-Proxy might not have package concept
                remaining_tokens=remaining_tokens,
                used_tokens=used_tokens,
                total_tokens=total_tokens,
                status="active"
            )

        except Exception as e:
            print(f"Warning: Failed to parse model usage data: {e}")
            return None

    def _extract_token_value(self, data: Dict[str, Any], field_names: List[str]) -> float:
        """Extract token value from data using multiple possible field names"""
        for field in field_names:
            if field in data:
                try:
                    value = float(data[field])
                    return max(0.0, value)  # Ensure non-negative
                except (ValueError, TypeError):
                    continue
        return 0.0
