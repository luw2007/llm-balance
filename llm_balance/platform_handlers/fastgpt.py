"""
FastGPT platform handler
FastGPT is an open-source application building platform
"""

import os
from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig

class FastGPTHandler(BasePlatformHandler):
    """FastGPT platform cost handler"""

    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for FastGPT platform"""
        return {
            "api_url": "https://fastgpt.in/api/v1/user/balance",
            "packages_url": "https://fastgpt.in/api/v1/user/packages",
            "usage_url": "https://fastgpt.in/api/v1/user/usage",
            "method": "GET",
            "auth_type": "api_key",
            "env_var": "FASTGPT_API_KEY",
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
        api_key = os.getenv('FASTGPT_API_KEY')
        if api_key:
            self.config.headers['Authorization'] = f'Bearer {api_key}'
            return

        # Try separate config file
        import yaml
        from pathlib import Path
        config_path = Path.home() / '.llm_balance' / 'fastgpt_config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    fastgpt_config = yaml.safe_load(f) or {}
                    if 'api_key' in fastgpt_config:
                        self.config.headers['Authorization'] = f'Bearer {fastgpt_config["api_key"]}'
                    if 'base_url' in fastgpt_config:
                        base_url = fastgpt_config['base_url']
                        if not base_url.endswith('/'):
                            base_url += '/'
                        self.config.api_url = base_url + "api/v1/user/balance"
                        self.config.packages_url = base_url + "api/v1/user/packages"
                        self.config.usage_url = base_url + "api/v1/user/usage"
            except Exception as e:
                pass

    def get_balance(self) -> CostInfo:
        """Get cost information from FastGPT"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for FastGPT")

        # Check if API key is configured
        if 'Authorization' not in self.config.headers:
            raise ValueError("FastGPT API key required. Set FASTGPT_API_KEY environment variable or configure in fastgpt_config.yaml")

        # Make API request for balance
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=self.config.headers
        )

        if not response:
            raise ValueError("No response from FastGPT API")

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
        """Extract balance from FastGPT API response"""
        data = response.get('data', response)

        # Try different possible balance field names
        balance_fields = ['balance', 'quota', 'remaining_quota', 'credit', 'amount', 'remaining_balance', 'points']

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
        """Extract currency from FastGPT API response"""
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

        # Default to USD for FastGPT
        return 'USD'

    def _get_spent_information(self) -> float:
        """Get spent information from usage or packages API"""
        try:
            # Try usage API first
            usage_url = getattr(self.config, 'usage_url', None)
            if usage_url:
                spent = self._get_spent_from_url(usage_url)
                if spent > 0:
                    return spent

            # Try packages API
            packages_url = getattr(self.config, 'packages_url', None)
            if packages_url:
                spent = self._get_spent_from_url(packages_url)
                if spent > 0:
                    return spent

            return 0.0

        except Exception as e:
            print(f"Warning: Failed to get spent information for FastGPT: {e}")
            return 0.0

    def _get_spent_from_url(self, url: str) -> float:
        """Get spent information from a specific URL"""
        try:
            response = self._make_request(
                url=url,
                method='GET',
                headers=self.config.headers
            )

            if not response:
                return 0.0

            # Extract spent information from response
            data = response.get('data', response)

            # Try different spent field names
            spent_fields = ['used_quota', 'spent', 'consumed', 'usage', 'total_usage', 'cost', 'used_points']

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

            # Try in package usage data
            if 'packages' in data:
                total_spent = 0.0
                packages = data['packages']
                if isinstance(packages, list):
                    for package in packages:
                        if isinstance(package, dict):
                            used = package.get('used', package.get('consumed', 0))
                            try:
                                total_spent += float(used)
                            except (ValueError, TypeError):
                                continue
                return total_spent

            return 0.0

        except Exception as e:
            return 0.0

    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "FastGPT"

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get model-level token information from FastGPT"""
        try:
            # Try packages URL first (most likely to have model-specific data)
            packages_url = getattr(self.config, 'packages_url', None)
            if packages_url:
                token_info = self._get_model_tokens_from_url(packages_url)
                if token_info and token_info.models:
                    return token_info

            # Try usage URL
            usage_url = getattr(self.config, 'usage_url', None)
            if usage_url:
                token_info = self._get_model_tokens_from_url(usage_url)
                if token_info and token_info.models:
                    return token_info

            return PlatformTokenInfo(
                platform=self.get_platform_name(),
                models=[],
                raw_data={'error': 'No model token data available'}
            )

        except Exception as e:
            print(f"Warning: Failed to get model token information for FastGPT: {e}")
            return PlatformTokenInfo(
                platform=self.get_platform_name(),
                models=[],
                raw_data={'error': str(e)}
            )

    def _get_model_tokens_from_url(self, url: str) -> Optional[PlatformTokenInfo]:
        """Get model token information from a specific URL"""
        try:
            response = self._make_request(
                url=url,
                method='GET',
                headers=self.config.headers
            )

            if not response:
                return None

            # Parse model usage data
            models = []
            data = response.get('data', response)

            # FastGPT might return usage in different formats
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
                elif 'packages' in data:
                    # Parse package data for model usage
                    packages = data['packages']
                    if isinstance(packages, list):
                        for package in packages:
                            if isinstance(package, dict):
                                model_info = self._parse_model_usage(package)
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
            return None

    def _parse_model_usage(self, model_data: Dict[str, Any]) -> Optional[ModelTokenInfo]:
        """Parse model usage data into ModelTokenInfo"""
        try:
            # Try different field names for model name
            model_name = model_data.get('model', model_data.get('name', model_data.get('model_name', 'Unknown')))

            # Try different field names for package name
            package_name = model_data.get('package', model_name)

            # Try different field names for token usage
            used_tokens = self._extract_token_value(model_data, ['used_tokens', 'usage', 'consumed', 'input_tokens', 'prompt_tokens', 'used'])
            total_tokens = self._extract_token_value(model_data, ['total_tokens', 'quota', 'limit', 'total_quota', 'total'])
            remaining_tokens = self._extract_token_value(model_data, ['remaining_tokens', 'remaining', 'left', 'remaining_quota', 'balance'])

            # Calculate missing values if possible
            if total_tokens > 0 and used_tokens >= 0 and remaining_tokens == 0:
                remaining_tokens = total_tokens - used_tokens
            elif total_tokens > 0 and remaining_tokens >= 0 and used_tokens == 0:
                used_tokens = total_tokens - remaining_tokens

            return ModelTokenInfo(
                model=model_name,
                package=package_name,
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
