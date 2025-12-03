"""
Anthropic platform handler
"""

import os
from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig
from ..utils import get_proxy_config

class AnthropicHandler(BasePlatformHandler):
    """Anthropic platform cost handler"""
    
    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for Anthropic platform"""
        return {
            "api_url": "https://api.anthropic.com/v1/messages",
            "method": "GET",
            "auth_type": "bearer_token",
            "env_var": "ANTHROPIC_API_KEY",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "x-api-version": "2023-06-01",
                "anthropic-version": "2023-06-01"
            },
            "params": {},
            "data": {},
            "enabled": False
        }
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from Anthropic"""
        return self._get_balance_with_api_key()
    
    def _get_balance_with_api_key(self) -> CostInfo:
        """Get balance using API key authentication"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for Anthropic")
        
        # Prepare authentication
        headers = self.config.headers.copy() if self.config.headers else {}
        
        # Get API key from environment variable
        api_key = os.getenv(self.config.env_var or 'ANTHROPIC_API_KEY')
        
        if not api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable.")
        
        headers['x-api-key'] = api_key
        
        # Note: Anthropic's API doesn't have a direct balance endpoint
        # We'll need to use a different approach or work with usage statistics
        # For now, let's try to get usage information
        try:
            # Get proxy configuration
            proxies = get_proxy_config()
            
            response = self._make_request(
                url="https://api.anthropic.com/v1/messages",
                method="POST",
                headers=headers,
                data={"max_tokens": 1, "model": "claude-3-haiku-20240307", "messages": [{"role": "user", "content": "test"}]},
                proxies=proxies
            )
            
            # If we get here, the API key is valid, but we can't get balance
            # Return a placeholder indicating balance checking is not supported
            return CostInfo(
                platform=self.get_platform_name(),
                balance=0.0,
                currency='USD',
                spent="-",
                spent_currency="-",
                raw_data={"message": "Balance checking not supported via API. Please check your Anthropic Console."}
            )
            
        except Exception as e:
            # If the request fails, return an informative error
            return CostInfo(
                platform=self.get_platform_name(),
                balance=0.0,
                currency='USD',
                spent="-",
                spent_currency="-",
                raw_data={"error": f"Unable to check balance: {str(e)}"}
            )
    
    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "Anthropic"
    
    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get model-level token information from Anthropic"""
        raise NotImplementedError(f"Model token checking not implemented for {self.get_platform_name()}")