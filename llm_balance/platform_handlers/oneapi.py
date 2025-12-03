"""
One-API platform handler
One-API is an open-source API management system
"""

import os
from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig

class OneAPIHandler(BasePlatformHandler):
    """One-API platform cost handler"""

    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for One-API platform"""
        return {
            "api_url": "http://localhost:3000/api/user/self",
            "statistics_url": "http://localhost:3000/api/user/statistics",
            "method": "GET",
            "auth_type": "bearer_token",
            "env_var": "ONEAPI_API_KEY",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            "params": {},
            "data": {},
            "enabled": False
        }

    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
        # Load platform-specific configuration from environment variables or separate config file
        self._load_env_config()

    def _load_env_config(self):
        """Load configuration from environment variables or separate config file."""
        # Try environment variable first
        env_base_url = os.getenv('ONEAPI_BASE_URL')
        if env_base_url:
            # Update API URLs with custom base URL
            if not env_base_url.endswith('/'):
                env_base_url += '/'
            self.config.api_url = env_base_url + "api/user/self"
            self.config.statistics_url = env_base_url + "api/user/statistics"
            return

        # Try separate config file
        import yaml
        from pathlib import Path
        config_path = Path.home() / '.llm_balance' / 'oneapi_config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    oneapi_config = yaml.safe_load(f) or {}
                    if 'base_url' in oneapi_config:
                        base_url = oneapi_config['base_url']
                        if not base_url.endswith('/'):
                            base_url += '/'
                        self.config.api_url = base_url + "api/user/self"
                        self.config.statistics_url = base_url + "api/user/statistics"
                    if 'api_key' in oneapi_config:
                        # Store in config for fallback
                        self.config.api_key = oneapi_config['api_key']
            except Exception as e:
                pass

    def get_balance(self) -> CostInfo:
        """Get cost information from One-API"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for One-API")

        # Prepare authentication
        headers = self.config.headers.copy() if self.config.headers else {}

        # Get API key from environment variable or config
        api_key = os.getenv(self.config.env_var or 'ONEAPI_API_KEY')
        if not api_key and hasattr(self.config, 'api_key'):
            api_key = getattr(self.config, 'api_key', None)

        if not api_key:
            raise ValueError("One-API API key required. Set ONEAPI_API_KEY environment variable or configure in oneapi_config.yaml")

        headers['Authorization'] = f'Bearer {api_key}'

        # Make API request for user info
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers
        )

        if not response:
            raise ValueError("No response from One-API API")

        # Extract balance and currency from response
        balance = self._extract_balance(response)
        currency = self._extract_currency(response)

        # Try to get spent information
        spent = self._get_spent_information(api_key)

        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance or 0.0,
            currency=currency or 'USD',
            spent=spent,
            spent_currency='USD' if spent > 0 else '-',
            raw_data=response
        )

    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from One-API API response"""
        # One-API typically returns balance in the 'data' field
        data = response.get('data', response)

        # Try different possible balance field names
        balance_fields = ['balance', 'quota', 'remaining_quota', 'credit', 'amount']

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
        """Extract currency from One-API API response"""
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

        # Default to USD for One-API
        return 'USD'

    def _get_spent_information(self, api_key: str) -> float:
        """Get spent information from statistics API"""
        try:
            # Check if statistics URL is configured
            statistics_url = getattr(self.config, 'statistics_url', None)
            if not statistics_url:
                return 0.0

            headers = self.config.headers.copy() if self.config.headers else {}
            headers['Authorization'] = f'Bearer {api_key}'

            # Make request to statistics API
            response = self._make_request(
                url=statistics_url,
                method='GET',
                headers=headers
            )

            if not response:
                return 0.0

            # Extract spent information from response
            data = response.get('data', response)

            # Try different spent field names
            spent_fields = ['used_quota', 'spent', 'consumed', 'usage', 'total_usage']

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
            print(f"Warning: Failed to get spent information for One-API: {e}")
            return 0.0

    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "One-API"

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get model-level token information from One-API"""
        try:
            # Get API key
            api_key = os.getenv(self.config.env_var or 'ONEAPI_API_KEY')
            if not api_key and hasattr(self.config, 'api_key'):
                api_key = getattr(self.config, 'api_key', None)

            if not api_key:
                raise ValueError("One-API API key required")

            # Try to get model usage statistics
            # One-API may have different endpoints for model usage
            base_url = getattr(self.config, 'statistics_url', '').replace('/user/statistics', '')
            if base_url:
                usage_url = base_url + '/api/user/usage'
            else:
                return PlatformTokenInfo(
                    platform=self.get_platform_name(),
                    models=[],
                    raw_data={'error': 'No usage endpoint configured'}
                )

            headers = self.config.headers.copy() if self.config.headers else {}
            headers['Authorization'] = f'Bearer {api_key}'

            # Make request to usage API
            response = self._make_request(
                url=usage_url,
                method='GET',
                headers=headers
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

            # One-API might return usage in different formats
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
                else:
                    # Try to parse as single model usage
                    model_info = self._parse_model_usage(data)
                    if model_info:
                        models.append(model_info)

            return PlatformTokenInfo(
                platform=self.get_platform_name(),
                models=models,
                raw_data=response
            )

        except Exception as e:
            print(f"Warning: Failed to get model token information for One-API: {e}")
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
                package=model_name,  # One-API might not have package concept
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
