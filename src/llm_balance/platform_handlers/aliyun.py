"""
Aliyun platform handler using official SDK
"""

import json
import os
from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig

try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException
    from aliyunsdkbssopenapi.request.v20171214.QueryAccountBalanceRequest import QueryAccountBalanceRequest
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

class AliyunHandler(BasePlatformHandler):
    """Aliyun platform cost handler using official SDK"""
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from Aliyun using official SDK"""
        if not SDK_AVAILABLE:
            raise ValueError("Aliyun SDK not available. Please install with: pip install aliyun-python-sdk-bssopenapi")
        
        # Check for required environment variables
        access_key_id = os.getenv(self.config.env_var or 'ALIYUN_ACCESS_KEY_ID')
        access_key_secret = os.getenv('ALIYUN_ACCESS_KEY_SECRET')
        
        if not access_key_id:
            raise ValueError(f"Aliyun Access Key ID not found. Please set {self.config.env_var or 'ALIYUN_ACCESS_KEY_ID'} environment variable.")
        
        if not access_key_secret:
            raise ValueError("Aliyun Access Key Secret not found. Please set ALIYUN_ACCESS_KEY_SECRET environment variable.")
        
        # Create client
        client = AcsClient(access_key_id, access_key_secret, 'cn-hangzhou')
        
        # Create request
        request = QueryAccountBalanceRequest()
        request.set_accept_format('json')
        
        try:
            # Send request
            response = client.do_action_with_exception(request)
            
            # Parse response
            import json
            response_data = json.loads(response.decode('utf-8'))
            
            # Extract balance and currency from response
            balance = self._extract_balance(response_data)
            currency = self._extract_currency(response_data)
            
            return CostInfo(
                platform=self.get_platform_name(),
                balance=balance or 0.0,
                currency=currency or 'CNY',
                raw_data=response_data
            )
            
        except ServerException as e:
            raise ValueError(f"Aliyun server error: {str(e)}")
        except ClientException as e:
            raise ValueError(f"Aliyun client error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Aliyun API error: {e}")
    
    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "Aliyun"
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from Aliyun API response"""
        # Aliyun BSS OpenAPI SDK response format
        try:
            data = response.get('Data', {})
            available_amount = data.get('AvailableAmount')
            if available_amount is not None:
                try:
                    return float(available_amount)
                except (ValueError, TypeError):
                    return None
        except (AttributeError, TypeError):
            pass
        
        # Fallback to direct response parsing
        balance = response.get('AvailableAmount')
        if balance is not None:
            try:
                return float(balance)
            except (ValueError, TypeError):
                return None
        return None
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from Aliyun API response"""
        try:
            data = response.get('Data', {})
            currency = data.get('Currency')
            if currency:
                return currency
        except (AttributeError, TypeError):
            pass
        
        # Fallback to direct response parsing
        return response.get('Currency', 'CNY')