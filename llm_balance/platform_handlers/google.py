"""
Google platform handler
"""

import os
import json
from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig
from ..utils import get_proxy_config

class GoogleHandler(BasePlatformHandler):
    """Google platform cost handler"""
    
    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for Google platform"""
        return {
            "api_url": "https://generativelanguage.googleapis.com/v1beta/models",
            "method": "GET",
            "auth_type": "api_key",
            "env_var": "GOOGLE_API_KEY",
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
    
    def get_balance(self) -> CostInfo:
        """Get cost information from Google"""
        return self._get_balance_with_api_key()
    
    def _get_balance_with_api_key(self) -> CostInfo:
        """Get balance using API key authentication"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for Google")
        
        # Get API key from environment variable
        api_key = os.getenv(self.config.env_var or 'GOOGLE_API_KEY')
        
        if not api_key:
            raise ValueError("Google API key required. Set GOOGLE_API_KEY environment variable.")
        
        # Google AI Studio uses API key as query parameter
        params = self.config.params.copy() if self.config.params else {}
        params['key'] = api_key
        
        # Try to get available models to verify API key works
        try:
            # Get proxy configuration
            proxies = get_proxy_config()
            
            response = self._make_request(
                url=self.config.api_url,
                method=self.config.method,
                headers=self.config.headers,
                params=params,
                proxies=proxies
            )
            
            # If we get here, the API key is valid
            # Google doesn't provide a direct balance API for Gemini
            # Users need to check their Google Cloud Console or AI Studio
            return CostInfo(
                platform=self.get_platform_name(),
                balance=0.0,
                currency='USD',
                spent="-",
                spent_currency="-",
                raw_data={"message": "Balance checking not supported via API. Please check your Google AI Studio or Google Cloud Console.", "models": response.get("models", [])}
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
        return "Google"
    
    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get model-level token information from Google"""
        raise NotImplementedError(f"Model token checking not implemented for {self.get_platform_name()}")