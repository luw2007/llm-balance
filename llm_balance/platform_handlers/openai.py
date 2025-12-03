"""
OpenAI platform handler
"""

import os
from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig
from ..utils import get_proxy_config

class OpenAIHandler(BasePlatformHandler):
    """OpenAI platform cost handler"""
    
    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for OpenAI platform"""
        return {
            "api_url": "https://api.openai.com/v1/organization/costs",
            "method": "GET",
            "auth_type": "bearer_token",
            "env_var": "OPENAI_ADMIN_KEY",  # Use Admin Key for organization-level access
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "OpenAI-Beta": "assistants=v2"  # Required for some endpoints
            },
            "params": {
                "start_time": 1730419200,  # November 1, 2024
                "limit": 1
            },
            "data": {},
            "enabled": False
        }
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from OpenAI"""
        return self._get_balance_with_api_key()
    
    def _get_balance_with_api_key(self) -> CostInfo:
        """Get balance using API key authentication"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for OpenAI")
        
        # Prepare authentication
        headers = self.config.headers.copy() if self.config.headers else {}
        
        # Get API key from environment variable
        api_key = os.getenv(self.config.env_var or 'OPENAI_ADMIN_KEY')
        
        if not api_key:
            raise ValueError("OpenAI Admin API key required. Set OPENAI_ADMIN_KEY environment variable.")
        
        headers['Authorization'] = f'Bearer {api_key}'
        
        # Get proxy configuration
        proxies = get_proxy_config()
        
        # Make API request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers,
            params=self.config.params,
            proxies=proxies
        )
        
        if not response:
            raise ValueError("No response from OpenAI API")
        
        # Extract balance and currency from response
        balance = self._extract_balance(response)
        currency = self._extract_currency(response)
        spent = self._extract_spent(response)
        
        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance or 0.0,
            currency=currency or 'USD',
            spent=spent or 0.0,
            spent_currency=currency or 'USD',
            raw_data=response
        )
    
    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "OpenAI"
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from OpenAI API response"""
        # OpenAI API returns costs data, we need to calculate balance from usage
        # For now, we'll extract the most recent usage and calculate remaining balance
        data = response.get('data', [])
        if data:
            latest_cost = data[0]
            # Extract total usage from the results
            results = latest_cost.get('results', [])
            if results:
                total_usage = results[0].get('amount', {}).get('value', 0)
                # For OpenAI, we need to calculate balance differently
                # This is a simplified approach - in practice, you'd need to track total deposits
                return float(total_usage)
        return None
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from OpenAI API response"""
        data = response.get('data', [])
        if data:
            latest_cost = data[0]
            results = latest_cost.get('results', [])
            if results:
                currency = results[0].get('amount', {}).get('currency', 'USD')
                return currency
        return 'USD'
    
    def _extract_spent(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract spent amount from OpenAI API response"""
        data = response.get('data', [])
        if data:
            latest_cost = data[0]
            results = latest_cost.get('results', [])
            if results:
                spent = results[0].get('amount', {}).get('value', 0)
                return float(spent)
        return None
    
    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get model-level token information from OpenAI"""
        raise NotImplementedError(f"Model token checking not implemented for {self.get_platform_name()}")