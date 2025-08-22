"""
Tencent Cloud platform handler
"""

from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig

class TencentHandler(BasePlatformHandler):
    """Tencent Cloud platform cost handler"""
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from Tencent Cloud using DescribeAccountBalance API"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for Tencent Cloud")
        
        # Prepare authentication
        headers = self.config.headers.copy()
        
        # Get API credentials from environment variables
        import os
        secret_id = os.getenv('TENCENT_SECRET_ID')
        secret_key = os.getenv('TENCENT_SECRET_KEY')
        
        if not secret_id or not secret_key:
            # Fallback to combined API key format
            api_key = os.getenv('TENCENT_API_KEY')
            if not api_key:
                raise ValueError("Tencent Cloud credentials required. Set TENCENT_SECRET_ID and TENCENT_SECRET_KEY environment variables, or TENCENT_API_KEY")
            
            # Handle combined format: "SecretId:SecretKey"
            if ':' in api_key:
                secret_id, secret_key = api_key.split(':', 1)
            else:
                raise ValueError("Invalid TENCENT_API_KEY format. Use 'SecretId:SecretKey' format")
        
        # Use Tencent Cloud official SDK for authentication
        try:
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
            from tencentcloud.billing.v20180709 import billing_client, models
            
            # Create credential
            cred = credential.Credential(secret_id, secret_key)
            
            # Create HTTP profile
            http_profile = HttpProfile()
            http_profile.endpoint = "billing.tencentcloudapi.com"
            
            # Create client profile
            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile
            
            # Create client
            client = billing_client.BillingClient(cred, "", client_profile)
            
            # Create request
            req = models.DescribeAccountBalanceRequest()
            
            # Execute request
            resp = client.DescribeAccountBalance(req)
            # Parse response
            response_data = resp.to_json_string()
            import json
            response = json.loads(response_data)
            
        except ImportError:
            # Fallback to HTTP request if SDK not available
            import time
            import hashlib
            import hmac
            import base64
            import urllib.parse
            
            # Build request parameters for DescribeAccountBalance
            params = {
                'Action': 'DescribeAccountBalance',
                'Version': '2018-07-09',
                'Region': 'ap-beijing',
                'Timestamp': int(time.time()),
                'Nonce': int(time.time() * 1000) % 1000000,
                'SecretId': secret_id,
                'SignatureMethod': 'HmacSHA256'
            }
            
            # Generate signature
            sorted_params = sorted(params.items())
            canonical_query_string = '&'.join(f'{k}={urllib.parse.quote(str(v), safe="")}' for k, v in sorted_params)
            string_to_sign = f'GET{billing.tencentcloudapi.com}/?{canonical_query_string}'
            signature = base64.b64encode(
                hmac.new(secret_key.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256).digest()
            ).decode('utf-8')
            
            params['Signature'] = signature
            
            # Make HTTP request
            response = self._make_request(
                url="https://billing.tencentcloudapi.com/",
                method="GET",
                headers=headers,
                params=params
            )
            
            if not response:
                raise ValueError("No response from Tencent Cloud Billing API")
        
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
        return "Tencent Cloud"
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from Tencent Cloud API response"""
        # Tencent Cloud response format: {"Balance": 1, "Uin": 100005258329, "RealBalance": 1, ...}
        # Note: Balance is in cents (分), need to divide by 100 to get yuan (元)
        if 'Balance' in response:
            try:
                return float(response['Balance']) / 100.0
            except (ValueError, TypeError):
                return None
        
        # Fallback to Response wrapper format
        response_data = response.get('Response', {})
        if 'Balance' in response_data:
            try:
                return float(response_data['Balance']) / 100.0
            except (ValueError, TypeError):
                return None
        return None
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from Tencent Cloud API response"""
        # Tencent Cloud API returns CNY by default
        return 'CNY'
