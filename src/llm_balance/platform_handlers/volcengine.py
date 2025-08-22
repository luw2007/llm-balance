"""
Volcengine platform handler using official SDK
"""

import os
from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig

class VolcengineHandler(BasePlatformHandler):
    """Volcengine platform handler using official SDK"""
    
    def __init__(self, config: PlatformConfig, browser: str = None):
        super().__init__(browser)  # SDK doesn't need browser
        self.config = config
        self.client = None
        self._initialized = False
    
    def _initialize_client(self):
        """Initialize SDK client"""
        if self._initialized:
            return
        
        try:
            from volcenginesdkbilling.api.billing_api import BILLINGApi
            from volcenginesdkcore.rest import ApiException
            from volcenginesdkcore.configuration import Configuration
            from volcenginesdkcore.api_client import ApiClient
            
            # Set AK/SK from environment variables
            access_key = self._get_access_key()
            secret_key = self._get_secret_key()
            
            if not access_key or not secret_key:
                raise ValueError("VOLCENGINE_ACCESS_KEY and VOLCENGINE_SECRET_KEY environment variables are required")
            
            # Create configuration with proper initialization
            config = Configuration()
            # Set credentials using the correct attributes
            config.ak = access_key
            config.sk = secret_key
            
            # Set region if configured
            if hasattr(self.config, 'region') and self.config.region:
                config.region = self.config.region
            else:
                config.region = 'cn-beijing'  # Default region
            
            # Create API client with configuration
            api_client = ApiClient(config)
            
            # Create billing client
            self.client = BILLINGApi(api_client)
            self.ApiException = ApiException
            
            self._initialized = True
            
        except ImportError as e:
            raise ValueError(f"Failed to import volcengine SDK: {e}. Please install with: pip install volcengine-python-sdk==4.0.13")
        except Exception as e:
            raise ValueError(f"Failed to initialize Volcengine SDK client: {e}")
    
    def _get_access_key(self) -> str:
        """Get access key from environment variable"""
        return os.getenv('VOLCENGINE_ACCESS_KEY', '')
    
    def _get_secret_key(self) -> str:
        """Get secret key from environment variable"""
        return os.getenv('VOLCENGINE_SECRET_KEY', '')
    
    def get_balance(self) -> CostInfo:
        """Get balance information using Volcengine SDK"""
        self._initialize_client()
        
        try:
            # Import the request model
            from volcenginesdkbilling.models.query_balance_acct_request import QueryBalanceAcctRequest
            
            # Create request body
            request_body = QueryBalanceAcctRequest()
            
            # Call QueryBalanceAcct API
            response = self.client.query_balance_acct(request_body)
            
            if not response:
                raise ValueError("Empty response from Volcengine SDK")
            
            # Parse response and extract balance information
            balance = self._extract_balance(response)
            currency = self._extract_currency(response)
            
            return CostInfo(
                platform=self.get_platform_name(),
                balance=balance or 0.0,
                currency=currency or 'CNY',
                raw_data=response
            )
            
        except self.ApiException as e:
            # Handle SDK-specific API exceptions
            error_msg = str(e)
            if e.status == 401:
                raise ValueError(f"Volcengine authentication failed: {error_msg}. Please check your VOLCENGINE_ACCESS_KEY and VOLCENGINE_SECRET_KEY environment variables.")
            elif e.status == 403:
                raise ValueError(f"Volcengine authorization failed: {error_msg}. Please check your permissions.")
            elif e.status == 429:
                raise ValueError(f"Volcengine rate limit exceeded: {error_msg}. Please try again later.")
            else:
                raise ValueError(f"Volcengine API error: {error_msg}")
        except Exception as e:
            # Handle other errors
            error_msg = str(e)
            if "access key" in error_msg.lower() or "secret key" in error_msg.lower():
                raise ValueError(f"Volcengine authentication failed: {error_msg}. Please check your VOLCENGINE_ACCESS_KEY and VOLCENGINE_SECRET_KEY environment variables.")
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                raise ValueError(f"Volcengine network error: {error_msg}. Please check your network connection.")
            else:
                raise ValueError(f"Volcengine SDK error: {error_msg}")
    
    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "Volcengine"
    
    def _extract_balance(self, response) -> Optional[float]:
        """Extract balance from SDK response"""
        try:
            # QueryBalanceAcctResponse has available_balance attribute
            balance = getattr(response, 'available_balance', None)
            if balance is not None:
                return float(balance)
        except (ValueError, TypeError, AttributeError):
            pass
        return None
    
    def _extract_currency(self, response) -> Optional[str]:
        """Extract currency from SDK response"""
        # Volcengine uses CNY by default
        return 'CNY'