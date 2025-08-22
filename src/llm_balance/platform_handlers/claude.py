"""
Claude platform handler
"""

from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig

class ClaudeHandler(BasePlatformHandler):
    """Claude platform cost handler"""
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from Claude"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for Claude")
        
        # Get API key from environment variable
        import os
        api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not api_key:
            raise ValueError("Claude API key required. Set ANTHROPIC_API_KEY environment variable.")
        
        # Prepare headers with API key
        headers = self.config.headers.copy()
        headers['x-api-key'] = api_key
        
        # Make API request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers,
            data=self.config.data
        )
        
        if not response:
            raise ValueError("No response from Claude API")
        
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
        return "Claude"
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from Claude API response"""
        # Claude cost API response structure
        # Common patterns:
        # - total_cost (in USD)
        # - remaining_credits (in USD)
        # - balance (in USD)
        
        # Try different possible balance fields
        balance_fields = ['total_cost', 'remaining_credits', 'balance', 'available_balance']
        
        for field in balance_fields:
            if field in response:
                try:
                    return float(response[field])
                except (ValueError, TypeError):
                    continue
        
        # If no direct balance field, look for usage data
        if 'usage' in response:
            usage_data = response['usage']
            if isinstance(usage_data, dict):
                for field in balance_fields:
                    if field in usage_data:
                        try:
                            return float(usage_data[field])
                        except (ValueError, TypeError):
                            continue
        
        return None
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from Claude API response"""
        # Claude typically uses USD
        return 'USD'