"""
Generic platform handler that works with configuration
"""

from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig
from ..utils import get_nested_value

class GenericHandler(BasePlatformHandler):
    """Generic handler that uses configuration to make API calls"""
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information using configured API"""
        if not self.config.api_url:
            raise ValueError(f"No API URL configured for {self.config.name}")
        
        # Prepare authentication
        headers = self.config.headers.copy()
        cookies = {}
        
        if self.config.auth_type == 'cookie':
            # Get cookies from browser
            if self.config.cookie_domain:
                cookies = self._get_cookies(self.config.cookie_domain)
                # Add CSRF token if available
                csrf_token = cookies.get('csrfToken')
                if csrf_token:
                    headers['X-CSRF-Token'] = csrf_token
        elif self.config.auth_type == 'bearer_token':
            # Use Bearer token from environment variable
            api_key = self._get_api_key()
            headers['Authorization'] = f'Bearer {api_key}'
        elif self.config.auth_type == 'api_key':
            # Use API key from environment variable
            api_key = self._get_api_key()
            headers['X-API-Key'] = api_key
        
        # Make API request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers,
            cookies=cookies,
            data=self.config.data if self.config.method.upper() == 'POST' else None
        )
        
        if not response:
            raise ValueError(f"No response from {self.config.api_url}")
        
        # Extract balance and currency from response
        balance = self._extract_balance(response)
        currency = self._extract_currency(response)
        
        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance or 0.0,
            currency=currency or 'Unknown',
            raw_data=response
        )
    
    def get_platform_name(self) -> str:
        """Get platform display name"""
        return self.config.name
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from API response"""
        if not self.config.balance_path:
            return None
        
        balance_value = get_nested_value(response, self.config.balance_path)
        if balance_value is not None:
            try:
                return float(balance_value)
            except (ValueError, TypeError):
                return None
        return None
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from API response"""
        if not self.config.currency_path:
            return None
        
        currency_value = get_nested_value(response, self.config.currency_path)
        if currency_value is not None:
            return str(currency_value)
        return None
    
    def _get_api_key(self) -> str:
        """Get API key from environment variable"""
        if not self.config.env_var:
            raise ValueError(f"No environment variable configured for {self.config.name}")
        
        import os
        api_key = os.getenv(self.config.env_var)
        if not api_key:
            raise ValueError(f"Environment variable {self.config.env_var} not set for {self.config.name}")
        
        return api_key