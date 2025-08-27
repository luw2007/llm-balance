"""
MiniMax platform handler
"""

import os
from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig

class MiniMaxHandler(BasePlatformHandler):
    """MiniMax platform cost handler"""
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from MiniMax"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for MiniMax")
        
        # Prepare authentication
        headers = self.config.headers.copy()
        
        # Get API key from environment variable
        api_key = os.getenv('MINIMAX_API_KEY')
        
        if not api_key:
            raise ValueError("MiniMax API key required. Set MINIMAX_API_KEY environment variable.")
        
        headers['Authorization'] = f'Bearer {api_key}'
        
        # Make API request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers
        )
        
        if not response:
            raise ValueError("No response from MiniMax API")
        
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
        return "MiniMax"
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from MiniMax API response"""
        # MiniMax response format: {"hard_balance_usd": "10.00", ...}
        balance_fields = ['hard_balance_usd', 'balance', 'available_balance', 'total_balance']
        
        for field in balance_fields:
            if field in response:
                try:
                    return float(response[field])
                except (ValueError, TypeError):
                    continue
        
        # Try nested fields
        data = response.get('data', {})
        for field in balance_fields:
            if field in data:
                try:
                    return float(data[field])
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from MiniMax API response"""
        # MiniMax typically uses USD
        return 'USD'