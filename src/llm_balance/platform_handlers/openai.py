"""
OpenAI platform handler
"""

from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig

class OpenAIHandler(BasePlatformHandler):
    """OpenAI platform balance handler"""
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from OpenAI"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for OpenAI")
        
        # Get API key from environment variable
        import os
        api_key = os.getenv('OPENAI_ADMIN_KEY')
        
        if not api_key:
            raise ValueError("OpenAI Admin API key required. Set OPENAI_ADMIN_KEY environment variable.")
        
        # Prepare headers with Bearer token
        headers = self.config.headers.copy()
        headers['Authorization'] = f'Bearer {api_key}'
        
        # Make API request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers,
            data=self.config.params
        )
        
        if not response:
            raise ValueError("No response from OpenAI API")
        
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
        return "OpenAI"
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from OpenAI API response"""
        # OpenAI costs API response structure:
        # data[0].results[0].amount.value
        
        # Try to extract from costs API response structure
        try:
            if 'data' in response and response['data']:
                first_bucket = response['data'][0]
                if 'results' in first_bucket and first_bucket['results']:
                    first_result = first_bucket['results'][0]
                    if 'amount' in first_result and 'value' in first_result['amount']:
                        return float(first_result['amount']['value'])
        except (ValueError, TypeError, KeyError, IndexError):
            pass
        
        # Fallback to other balance fields
        balance_fields = ['total_usage', 'balance', 'available_credit', 'remaining_balance']
        
        for field in balance_fields:
            if field in response:
                try:
                    return float(response[field])
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from OpenAI API response"""
        # OpenAI costs API response structure:
        # data[0].results[0].amount.currency
        
        # Try to extract from costs API response structure
        try:
            if 'data' in response and response['data']:
                first_bucket = response['data'][0]
                if 'results' in first_bucket and first_bucket['results']:
                    first_result = first_bucket['results'][0]
                    if 'amount' in first_result and 'currency' in first_result['amount']:
                        return first_result['amount']['currency']
        except (ValueError, TypeError, KeyError, IndexError):
            pass
        
        # Default to USD
        return 'USD'