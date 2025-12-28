"""
Base class for relay platforms (e.g. DuckCoding, PackyCode, etc.)
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo

class RelayPlatformHandler(BasePlatformHandler):
    """
    Common logic for relay platforms that use cookies and api_user_id.
    """
    
    def __init__(self, config, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
        self._load_env_config()

    def _load_env_config(self):
        """Load api_user_id from environment or yaml config"""
        # Derived classes should define self.platform_id (e.g. 'DUCKCODING')
        platform_id = getattr(self, 'platform_id', self.get_platform_name().upper())
        env_var = f"{platform_id}_API_USER_ID"
        
        # Try environment variable
        env_user_id = os.getenv(env_var)
        if env_user_id:
            self.config.api_user_id = env_user_id
            return

        # Try separate config file
        config_filename = f"{self.get_platform_name().lower()}_config.yaml"
        config_path = Path.home() / '.llm_balance' / config_filename
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    plat_config = yaml.safe_load(f) or {}
                    if 'api_user_id' in plat_config:
                        self.config.api_user_id = plat_config['api_user_id']
            except Exception:
                pass

    def get_balance(self) -> CostInfo:
        """Standard relay balance retrieval"""
        response = self._make_relay_request()
        
        # Default scaling: 500,000 tokens = 1 CNY
        scaling = getattr(self, 'quota_scaling', 500000.0)
        
        balance = 0.0
        spent = 0.0
        try:
            data = response.get('data', {})
            quota = float(data.get('quota', 0))
            bonus_quota = float(data.get('bonus_quota', 0))
            used_quota = float(data.get('used_quota', 0))
            
            balance = (quota + bonus_quota) / scaling
            spent = used_quota / scaling
        except Exception:
            pass

        return CostInfo(
            platform=self.get_platform_name(),
            balance=self._validate_balance(balance),
            currency='CNY',
            spent=self._validate_balance(spent),
            spent_currency='CNY',
            raw_data=response
        )

    def _make_relay_request(self) -> Dict[str, Any]:
        """Make request with api_user_id header (if configured) and cookies"""
        if not self.config.api_url:
            raise ValueError(f"No API URL configured for {self.get_platform_name()}")

        headers = (self.config.headers or {}).copy()
        
        # Add user id header if configured
        api_user_id = getattr(self.config, 'api_user_id', None)
        if api_user_id:
            user_header = getattr(self, 'user_id_header', 'new-api-user')
            headers[user_header] = str(api_user_id)
        elif hasattr(self, 'user_id_header') and self.user_id_header:
             # If header is required but missing
             raise ValueError(
                f"{self.get_platform_name()} requires api_user_id. "
                f"Set {getattr(self, 'platform_id', self.get_platform_name().upper())}_API_USER_ID env var."
            )

        # Try multiple domain variations for cookies
        domain = self.config.cookie_domain
        domains_to_try = [domain]
        if domain:
            if not domain.startswith('.'):
                domains_to_try.append('.' + domain)
            if not domain.startswith('www.'):
                domains_to_try.append('www.' + domain)
        
        cookies = {}
        for d in domains_to_try:
            try:
                domain_cookies = self._get_cookies(d)
                if domain_cookies:
                    cookies.update(domain_cookies)
                    break
            except Exception:
                continue

        if not cookies:
            raise ValueError(f"No cookies found for {domain}. Please login in browser.")

        response = self._make_request(
            url=self.config.api_url,
            method='GET',
            headers=headers,
            cookies=cookies
        )
        
        if not response:
            raise ValueError(f"No response from {self.get_platform_name()} API")
            
        return response
