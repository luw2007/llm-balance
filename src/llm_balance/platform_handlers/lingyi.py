"""
Lingyi (零一万物) platform handler
"""

from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig

class LingyiHandler(BasePlatformHandler):
    """Lingyi (零一万物) platform cost handler"""
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from Lingyi"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for Lingyi")
        
        # Prepare authentication
        headers = self.config.headers.copy()
        
        # Get cookies from browser
        cookies = {}
        if self.config.cookie_domain:
            cookies = self._get_cookies(self.config.cookie_domain)
        
        # Check if we have necessary cookies for authentication
        if not cookies:
            raise ValueError(f"No authentication cookies found for {self.config.cookie_domain}. Please ensure you are logged in to Lingyi Console in {self.browser} browser.")
        
        # Make API request with cookies
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers,
            params=self.config.params,
            data=self.config.data,
            cookies=cookies
        )
        
        if not response:
            raise ValueError("No response from Lingyi API")
        
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
        return "Lingyi"
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from Lingyi API response"""
        # Lingyi response format: {"message": "成功", "data": {"balance": "36.00", ...}, "status": 0}
        data = response.get('data', {})
        if 'balance' in data:
            try:
                return float(data['balance'])
            except (ValueError, TypeError):
                return None
        return None
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from Lingyi API response"""
        # 灵忆API返回的余额默认是人民币
        return 'CNY'