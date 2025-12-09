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
            "show_cost": True,
            "show_package": True,
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
        env_user_id = os.getenv('CSMINDAI_API_USER_ID')
        if env_user_id:
            self.config.api_user_id = env_user_id
            return

        # Try separate config file
        config_path = Path.home() / '.llm_balance' / 'csmindai_config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    csmindai_config = yaml.safe_load(f) or {}
                    if 'api_user_id' in csmindai_config:
                        self.config.api_user_id = csmindai_config['api_user_id']
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

        # Get api_user_id from config (loaded from env var or separate config file)
        api_user_id = getattr(self.config, 'api_user_id', None)
        if not api_user_id:
            raise ValueError(
                "CSMindAI requires api_user_id to be configured. Please set it using:\n"
                "1. Environment variable: export CSMINDAI_API_USER_ID=YOUR_USER_ID\n"
                "2. Separate config file: ~/.llm_balance/csmindai_config.yaml\n"
                "   api_user_id: YOUR_USER_ID"
            )

        # Set required headers
        headers['new-api-user'] = str(api_user_id)

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

        # Get api_user_id from config (loaded from env var or separate config file)
        api_user_id = getattr(self.config, 'api_user_id', None)
        if not api_user_id:
            raise ValueError(
                "CSMindAI requires api_user_id to be configured. Please set it using:\n"
                "1. Environment variable: export CSMINDAI_API_USER_ID=YOUR_USER_ID\n"
                "2. Separate config file: ~/.llm_balance/csmindai_config.yaml\n"
                "   api_user_id: YOUR_USER_ID"
            )

        # Set required headers
        headers['new-api-user'] = str(api_user_id)

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

        API Schema:
            - data.quota: Remaining tokens (not total!)
            - data.used_quota: Tokens that have been used/consumed
            - Total tokens = used_quota + quota

        This method correctly handles the API where 'quota' represents
        the remaining amount, not the total allocation.
        """
        data = response if isinstance(response, dict) else {}
        user_data = data.get('data', {}) if isinstance(data.get('data'), dict) else {}

        if not isinstance(user_data, dict):
            user_data = {}

        results: List[ModelTokenInfo] = []
        default_model_name = "claude,codex"

        # Extract quota information
        # quota = remaining amount, used_quota = consumed amount
        remaining = user_data.get('quota', 0)
        used = user_data.get('used_quota', 0)

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
        used_tokens = _num(used)
        remaining_tokens = _num(remaining)
        # Total is the sum of used + remaining
        total_tokens = max(0.0, used_tokens + remaining_tokens)

        # Ensure non-negative values
        used_tokens = max(0.0, used_tokens)
        remaining_tokens = max(0.0, remaining_tokens)

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