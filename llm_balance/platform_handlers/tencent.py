"""
Tencent Cloud platform handler
"""

from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig

class TencentHandler(BasePlatformHandler):
    """Tencent Cloud platform cost handler"""
    
    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for Tencent Cloud platform"""
        return {
            "api_url": "https://billing.tencentcloudapi.com/",
            "method": "GET",
            "auth_type": "sdk",
            "env_var": "TENCENT_SECRET_ID",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json"
            },
            "params": {},
            "data": {},
            "enabled": True,
            "cookie_domain": None,
            "region": "ap-beijing"
        }
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from Tencent Cloud"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for Tencent Cloud")
        
        # Get credentials
        import os
        secret_id = os.getenv('TENCENT_SECRET_ID')
        secret_key = os.getenv('TENCENT_SECRET_KEY')
        
        if not secret_id or not secret_key:
            api_key = os.getenv('TENCENT_API_KEY')
            if not api_key:
                raise ValueError("Tencent Cloud credentials required")
            if ':' in api_key:
                secret_id, secret_key = api_key.split(':', 1)
            else:
                raise ValueError("Invalid TENCENT_API_KEY format")
        
        # Use SDK if available
        try:
            from tencentcloud.common import credential
            from tencentcloud.billing.v20180709 import billing_client, models
            
            cred = credential.Credential(secret_id, secret_key)
            client = billing_client.BillingClient(cred, "ap-beijing")
            req = models.DescribeAccountBalanceRequest()
            resp = client.DescribeAccountBalance(req)
            import json
            response = json.loads(resp.to_json_string())
            
        except ImportError:
            # Fallback to HTTP request
            import time
            import hashlib
            import hmac
            import base64
            import urllib.parse
            
            params = {
                'Action': 'DescribeAccountBalance',
                'Version': '2018-07-09',
                'Region': 'ap-beijing',
                'Timestamp': int(time.time()),
                'Nonce': int(time.time() * 1000) % 1000000,
                'SecretId': secret_id,
                'SignatureMethod': 'HmacSHA256'
            }
            
            sorted_params = sorted(params.items())
            canonical_query_string = '&'.join(f'{k}={urllib.parse.quote(str(v), safe="")}' for k, v in sorted_params)
            string_to_sign = f'GETbilling.tencentcloudapi.com/?{canonical_query_string}'
            signature = base64.b64encode(
                hmac.new(secret_key.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256).digest()
            ).decode('utf-8')
            
            params['Signature'] = signature
            response = self._make_request(
                url="https://billing.tencentcloudapi.com/",
                method="GET",
                headers=self.config.headers,
                params=params
            )
            
            if not response:
                raise ValueError("No response from Tencent Cloud API")
        
        balance = self._extract_balance(response)
        currency = self._extract_currency(response)
        
        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance or 0.0,
            currency=currency or 'CNY',
            raw_data=response
        )
    
    def get_platform_name(self) -> str:
        return "Tencent Cloud"
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        if 'Balance' in response:
            try:
                return float(response['Balance']) / 100.0
            except (ValueError, TypeError):
                return None
        
        response_data = response.get('Response', {})
        if 'Balance' in response_data:
            try:
                return float(response_data['Balance']) / 100.0
            except (ValueError, TypeError):
                return None
        return None
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        return 'CNY'