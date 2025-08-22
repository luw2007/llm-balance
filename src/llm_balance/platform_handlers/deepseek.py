"""
DeepSeek platform handler
"""

from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig

class DeepSeekHandler(BasePlatformHandler):
    """DeepSeek platform cost handler"""
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from DeepSeek"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for DeepSeek")
        
        # Prepare authentication
        headers = self.config.headers.copy()
        
        # Get API key from environment variable
        import os
        api_key = os.getenv('DEEPSEEK_API_KEY')
        
        if not api_key:
            raise ValueError("DeepSeek API key required. Set DEEPSEEK_API_KEY environment variable.")
        
        headers['Authorization'] = f'Bearer {api_key}'
        
        # Make API request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers
        )
        
        if not response:
            raise ValueError("No response from DeepSeek API")
        
        # Extract balance and currency from response
        balance = self._extract_balance(response)
        currency = self._extract_currency(response)
        
        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance or 0.0,
            currency=currency or 'CNY',
            raw_data=response
        )
    
    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "DeepSeek"
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from DeepSeek API response"""
        # DeepSeek response format: {"is_available": true, "balance_infos": [{"currency": "CNY", "total_balance": "100.00", ...}]}
        balance_infos = response.get('balance_infos', [])
        if balance_infos:
            total_balance = balance_infos[0].get('total_balance', '0')
            try:
                return float(total_balance)
            except (ValueError, TypeError):
                return None
        return None
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from DeepSeek API response"""
        balance_infos = response.get('balance_infos', [])
        if balance_infos:
            return balance_infos[0].get('currency', 'CNY')
        return 'CNY'