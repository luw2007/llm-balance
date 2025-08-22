"""
Zhipu AI (智谱AI) platform handler
"""

from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig

class ZhipuHandler(BasePlatformHandler):
    """Zhipu AI (智谱AI) platform cost handler"""
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from Zhipu AI"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for Zhipu AI")
        
        # Prepare authentication
        headers = self.config.headers.copy()
        
        # Get cookies
        cookies = {}
        if self.config.cookie_domain:
            cookies = self._get_cookies(self.config.cookie_domain)
        
        # Check if we have necessary cookies for authentication
        if not cookies:
            raise ValueError(f"No authentication cookies found for {self.config.cookie_domain}. Please ensure you are logged in to Volcengine Console in {self.browser} browser.")
        headers['authorization'] = cookies['bigmodel_token_production']
        
        # Make API request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers,
            params=self.config.params,
            data=self.config.data
        )

        if not response:
            raise ValueError("No response from Zhipu AI API")
        
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
        return "Zhipu AI"
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from Zhipu AI API response"""
        # Zhipu AI response format: {"result": {"balance": 100.00, "currency": "CNY"}, "success": true}
        result = response.get('data', {})
        if 'balance' in result:
            try:
                return float(result['balance'])
            except (ValueError, TypeError):
                return None
        return None
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from Zhipu AI API response"""
        return self.config.currency_path
