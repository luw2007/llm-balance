"""
CSMindAI third-party relay handler (balance query only)
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml
from .base import BasePlatformHandler, PlatformTokenInfo, ModelTokenInfo, CostInfo
from ..config import PlatformConfig


class CSMindAIHandler(BasePlatformHandler):
    """CSMindAI relay platform handler (only balance query is implemented)."""

    @classmethod
    def get_default_config(cls) -> dict:
        """Default configuration for CSMindAI balance query via cookie auth."""
        return {
            "display_name": "CSMindAI",
            "handler_class": "CSMindAIHandler",
            "description": "CSMindAI relay (balance only)",
            "api_url": "https://api.csmindai.com/api/user/self",
            "method": "GET",
            "auth_type": "cookie",
            "env_var": None,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Cache-Control": "no-store",
                "DNT": "1",
                "Pragma": "no-cache",
                "Priority": "u=1, i",
                "Referer": "https://api.csmindai.com/console",
                "Sec-Ch-Ua": '"Not=A?Brand";v="24", "Chromium";v="140"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            },
            "params": {},
            "data": {},
            "enabled": False,
            "cookie_domain": "api.csmindai.com"
        }

    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
        # Load platform-specific configuration from environment variables
        self._load_env_config()

    def _load_env_config(self):
        """Load configuration from environment variables or separate config file."""
        # Try environment variable first
        env_new_api_user = os.getenv('CSMINDDAI_NEW_API_USER')
        if env_new_api_user:
            self.config.new_api_user = env_new_api_user
            return

        # Try separate config file
        config_path = Path.home() / '.llm_balance' / 'csmindai_config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    csmindai_config = yaml.safe_load(f) or {}
                    if 'new_api_user' in csmindai_config:
                        self.config.new_api_user = csmindai_config['new_api_user']
            except Exception:
                pass

    def get_platform_name(self) -> str:
        return "CSMindAI"

    def get_balance(self) -> CostInfo:
        """Return cost info using quota data from API.

        - Balance = quota (remaining tokens)
        - Spent = used_quota (consumed tokens)
        """
        if not getattr(self.config, 'api_url', None):
            raise ValueError("No API URL configured for CSMindAI")

        headers = (self.config.headers or {}).copy()

        # Get new_api_user from config (loaded from env var or separate config file)
        new_api_user = getattr(self.config, 'new_api_user', None)
        if not new_api_user:
            raise ValueError(
                "CSMindAI requires new_api_user to be configured. Please set it using:\n"
                "1. Environment variable: export CSMINDDAI_NEW_API_USER=YOUR_USER_ID\n"
                "2. Separate config file: ~/.llm_balance/csmindai_config.yaml\n"
                "   new_api_user: YOUR_USER_ID"
            )

        # Set required headers
        headers['new-api-user'] = str(new_api_user)

        # Get cookies from browser
        cookies = self._get_cookies(self.config.cookie_domain)
        if not cookies:
            raise ValueError(f"No cookies found for {self.config.cookie_domain}. Please login in browser first.")

        # Make the API request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers,
            cookies=cookies
        )

        if not response:
            raise ValueError("No response from CSMindAI user API")

        # Extract balance and spent from quota data
        balance = 0.0
        spent = 0.0

        try:
            data = response.get('data', {}) if isinstance(response, dict) else {}

            # Extract quota information
            quota = data.get('quota', 0)
            used_quota = data.get('used_quota', 0)

            # Convert to float
            balance = float(quota) if quota is not None else 0.0
            spent = float(used_quota) if used_quota is not None else 0.0
            if quota is not None:
                balance = float(quota) / 500000.0
            if used_quota is not None:
                spent = float(used_quota) / 500000.0

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
        """Query CSMindAI user data and create usage package from quota info.

        Authentication:
            - Use session cookie from browser
            - Set header: new-api-user: <user_id>

        Data source:
            - GET https://api.csmindai.com/api/user/self
            - Use quota and used_quota from response data

        Models:
            - Generic model name: "gpt-4,gpt-3.5-turbo,claude"
            - Package name: "CSMindAI Quota Package"
        """
        if not getattr(self.config, 'api_url', None):
            raise ValueError("No API URL configured for CSMindAI")

        headers = (self.config.headers or {}).copy()

        # Get new_api_user from config (loaded from env var or separate config file)
        new_api_user = getattr(self.config, 'new_api_user', None)
        if not new_api_user:
            raise ValueError(
                "CSMindAI requires new_api_user to be configured. Please set it using:\n"
                "1. Environment variable: export CSMINDDAI_NEW_API_USER=YOUR_USER_ID\n"
                "2. Separate config file: ~/.llm_balance/csmindai_config.yaml\n"
                "   new_api_user: YOUR_USER_ID"
            )

        # Set required headers
        headers['new-api-user'] = str(new_api_user)

        # Get cookies from browser
        cookies = self._get_cookies(self.config.cookie_domain)
        if not cookies:
            raise ValueError(f"No cookies found for {self.config.cookie_domain}. Please login in browser first.")

        # Make the API request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers,
            cookies=cookies
        )

        if not response:
            raise ValueError("No response from CSMindAI user API")

        # Extract quota information
        models = self._extract_models_from_quota(response)

        return PlatformTokenInfo(
            platform=self.get_platform_name(),
            models=models,
            raw_data=response
        )

    def _extract_models_from_quota(self, response: Dict[str, Any]) -> List[ModelTokenInfo]:
        """Extract ModelTokenInfo list from user response.

        The schema:
            - Look for data.quota and data.used_quota
            - Create model info based on quota usage
            - Package name based on user info
        """
        data = response if isinstance(response, dict) else {}
        user_data = data.get('data', {}) if isinstance(data.get('data'), dict) else {}

        if not isinstance(user_data, dict):
            user_data = {}

        results: List[ModelTokenInfo] = []
        default_model_name = "gpt-4,gpt-3.5-turbo,claude"

        # Extract quota information
        quota = user_data.get('quota', 0)
        used_quota = user_data.get('used_quota', 0)

        # Create package name based on user info
        display_name = user_data.get('display_name', 'User')
        username = user_data.get('username', 'user')
        group = user_data.get('group', 'default')

        package_name = f"CSMindAI {group.title()} Package"

        # Convert to numeric values
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
        total_tokens = _num(quota)
        used_tokens = _num(used_quota)
        remaining_tokens = max(0.0, total_tokens - used_tokens)

        # Ensure non-negative values
        total_tokens = max(0.0, total_tokens)
        remaining_tokens = max(0.0, remaining_tokens)
        used_tokens = max(0.0, used_tokens)

        # Determine status based on user status
        user_status = user_data.get('status', 1)
        status = "active" if user_status == 1 else "inactive"

        results.append(ModelTokenInfo(
            model=default_model_name,
            package=package_name,
            remaining_tokens=remaining_tokens,
            used_tokens=used_tokens,
            total_tokens=total_tokens,
            status=status
        ))

        return results