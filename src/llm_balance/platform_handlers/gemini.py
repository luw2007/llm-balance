"""
Google Gemini platform handler
"""

import os
from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig

class GeminiHandler(BasePlatformHandler):
    """Google Gemini platform cost handler"""
    
    def __init__(self, config: PlatformConfig, browser: str = None):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from Google Gemini"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for Gemini")
        
        # Prepare authentication headers
        headers = self.config.headers.copy()
        
        # Add API key authentication
        if self.config.auth_type == 'api_key':
            api_key = self._get_api_key()
            # Add API key to headers or URL based on Gemini API requirements
            if 'x-goog-api-key' not in headers:
                headers['x-goog-api-key'] = api_key
        elif self.config.auth_type == 'bearer_token':
            api_key = self._get_api_key()
            if 'Authorization' not in headers:
                headers['Authorization'] = f'Bearer {api_key}'
        
        # Make API request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers,
            data=self.config.data if self.config.method.upper() == 'POST' else None,
            params=self.config.params
        )
        
        if not response:
            raise ValueError("No response from Gemini API")
        
        # Extract balance and currency from response
        balance = self._extract_balance(response)
        currency = self._extract_currency(response)
        
        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance or 0.0,
            currency=currency or 'USD',
            raw_data=response
        )
    
    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "Google Gemini"
    
    def _get_api_key(self) -> str:
        """Get API key from environment variable"""
        env_var = self.config.env_var or 'GEMINI_API_KEY'
        api_key = os.getenv(env_var)
        if not api_key:
            raise ValueError(f"Environment variable {env_var} not set for Gemini")
        return api_key
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from Gemini API response"""
        # Try multiple possible balance field names
        balance_fields = [
            'balance', 'available_balance', 'credits', 'total_balance',
            'remaining_balance', 'account_balance', 'usage_balance'
        ]
        
        # First try direct fields
        for field in balance_fields:
            if field in response:
                try:
                    return float(response[field])
                except (ValueError, TypeError):
                    continue
        
        # Try nested fields
        nested_paths = [
            ['data', 'balance'],
            ['usage', 'balance'],
            ['account', 'balance'],
            ['billing', 'balance'],
            ['result', 'balance'],
            ['response', 'balance'],
            ['totalUsage'],
            ['usage', 'total_tokens'],
            ['usage', 'total_cost']
        ]
        
        for path in nested_paths:
            value = self._get_nested_value(response, path)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from Gemini API response"""
        # Try direct currency fields
        currency_fields = ['currency', 'unit', 'currency_code']
        
        for field in currency_fields:
            if field in response:
                currency = response[field]
                if isinstance(currency, str):
                    return currency.upper()
        
        # Try nested currency fields
        nested_paths = [
            ['data', 'currency'],
            ['usage', 'currency'],
            ['account', 'currency'],
            ['billing', 'currency'],
            ['result', 'currency'],
            ['response', 'currency']
        ]
        
        for path in nested_paths:
            value = self._get_nested_value(response, path)
            if value is not None and isinstance(value, str):
                return value.upper()
        
        # Default to USD for Google services
        return 'USD'
    
    def _get_nested_value(self, data: Dict[str, Any], path: list) -> Any:
        """Get nested value from dictionary using path"""
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current