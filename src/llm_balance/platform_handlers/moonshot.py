"""
Moonshot platform handler
"""

import os
from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig

class MoonshotHandler(BasePlatformHandler):
    """Moonshot platform cost handler"""
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from Moonshot"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for Moonshot")
        
        # Get API key from environment variable
        api_key = os.getenv('MOONSHOT_API_KEY')
        if not api_key:
            raise ValueError("Moonshot API key required. Set MOONSHOT_API_KEY environment variable.")
        
        return self._get_balance_with_api_key(api_key)
    
    def _get_balance_with_api_key(self, api_key: str) -> CostInfo:
        """Get balance using API key authentication"""
        headers = {
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        response = self._make_request(
            url=self.config.api_url,
            headers=headers
        )
        
        if not response:
            raise ValueError("No response from Moonshot API")
        
        # Extract balance from response
        data = response.get('data', {})
        available_balance = data.get('available_balance', 0.0)
        voucher_balance = data.get('voucher_balance', 0.0)
        cash_balance = data.get('cash_balance', 0.0)
        
        return CostInfo(
            platform=self.get_platform_name(),
            balance=available_balance,
            currency='CNY',  # Moonshot uses CNY
            raw_data={
                'available_balance': available_balance,
                'voucher_balance': voucher_balance,
                'cash_balance': cash_balance,
                'full_response': response
            }
        )
    
    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "Moonshot"