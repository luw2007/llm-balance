"""
Volcengine platform handler using official SDK
"""

import os
from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig

class VolcengineHandler(BasePlatformHandler):
    """Volcengine platform cost handler using official SDK"""
    
    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for Volcengine platform"""
        return {
            "api_url": "https://api.volcengine.com/api/billing/2022-01-01/QueryBalanceAcct",
            "method": "POST",
            "auth_type": "sdk",
            "env_var": "VOLCENGINE_ACCESS_KEY",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            "params": {},
            "data": {},
            "enabled": True,
            "region": "cn-beijing"
        }
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from Volcengine using official SDK"""
        return self._get_balance_with_sdk()
    
    def _get_balance_with_sdk(self) -> CostInfo:
        """Get balance using official Volcengine SDK with QueryBalanceAcct API"""
        try:
            import os
            from volcenginesdkcore.rest import ApiException
            
            # Get credentials from environment variables
            access_key = os.getenv('VOLCENGINE_ACCESS_KEY')
            secret_key = os.getenv('VOLCENGINE_SECRET_KEY')
            
            if not access_key:
                raise ValueError("VOLCENGINE_ACCESS_KEY environment variable not set")
            if not secret_key:
                raise ValueError("VOLCENGINE_SECRET_KEY environment variable not set")
            
            try:
                # Import official SDK
                import volcenginesdkcore
                import volcenginesdkbilling
                from volcenginesdkbilling.models import QueryBalanceAcctRequest
                
                # Configure SDK
                configuration = volcenginesdkcore.Configuration()
                configuration.ak = access_key
                configuration.sk = secret_key
                configuration.region = self.config.region or "cn-beijing"
                volcenginesdkcore.Configuration.set_default(configuration)
                
                # Use official billing API
                api_instance = volcenginesdkbilling.BILLINGApi()
                query_balance_acct_request = QueryBalanceAcctRequest()
                
                # Call QueryBalanceAcct API
                resp = api_instance.query_balance_acct(query_balance_acct_request)
                
                # Parse response from official SDK
                if not resp:
                    raise ValueError("No response from Volcengine SDK")
                
                # Extract balance and currency from official response
                balance = 0.0
                currency = 'CNY'
                
                # Handle QueryBalanceAcct response format
                if hasattr(resp, 'available_balance'):
                    balance = float(resp.available_balance)
                elif hasattr(resp, 'available_cash_amount'):
                    balance = float(resp.available_cash_amount)
                elif hasattr(resp, 'cash_balance'):
                    balance = float(resp.cash_balance)
                elif hasattr(resp, 'result') and resp.result:
                    result = resp.result
                    if hasattr(result, 'available_balance'):
                        balance = float(result.available_balance)
                    elif hasattr(result, 'available_cash_amount'):
                        balance = float(result.available_cash_amount)
                    elif hasattr(result, 'cash_balance'):
                        balance = float(result.cash_balance)
                
                # Currency is typically CNY for Volcengine
                currency = 'CNY'
                
                return CostInfo(
                    platform=self.get_platform_name(),
                    balance=balance,
                    currency=currency,
                    raw_data=resp.__dict__ if hasattr(resp, '__dict__') else str(resp)
                )
                
            except ImportError as e:
                print(f"Warning: Volcengine SDK import error: {e}")
                return self._get_balance_with_cookie()
            except ApiException as e:
                print(f"Warning: Volcengine API error: {e}")
                return self._get_balance_with_cookie()
                
        except ImportError:
            # SDK not available, fallback to cookie authentication
            print("Warning: Volcengine SDK not found, falling back to cookie authentication")
            return self._get_balance_with_cookie()
        except Exception as e:
            # SDK authentication failed, fallback to cookie authentication
            print(f"Warning: Volcengine SDK authentication failed: {e}, falling back to cookie authentication")
            return self._get_balance_with_cookie()
    
    def _get_balance_with_cookie(self) -> CostInfo:
        """Get balance using cookie authentication (fallback)"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for Volcengine cookie authentication")
        
        # Get cookies
        cookies = {}
        if self.config.cookie_domain:
            cookies = self._get_cookies(self.config.cookie_domain)
        
        # Check if we have necessary cookies for authentication
        if not cookies:
            print(f"Warning: No authentication cookies found for {self.config.cookie_domain}. Please ensure you are logged in to Volcengine Console in {self.browser} browser.")
            return CostInfo(
                platform=self.get_platform_name(),
                balance=0.0,
                currency='CNY',
                raw_data={'error': 'No authentication cookies found'}
            )
        
        try:
            # Prepare headers with CSRF token
            headers = self.config.headers.copy()
            csrf_token = cookies.get('csrfToken') or cookies.get('csrf_token') or cookies.get('x-csrf-token')
            if csrf_token:
                headers['X-CSRF-Token'] = csrf_token
            else:
                # Try to get CSRF token from the finance overview page
                csrf_token = self._get_csrf_token_from_page()
                if csrf_token:
                    headers['X-CSRF-Token'] = csrf_token
                else:
                    print(f"Warning: No CSRF token found for Volcengine. The request might fail due to missing CSRF protection.")
            
            # Make API request
            response = self._make_request(
                url=self.config.api_url,
                method=self.config.method,
                headers=headers,
                cookies=cookies,
                data=self.config.data
            )
            
            if not response:
                raise ValueError("No response from Volcengine API")
            
            # Extract balance and currency from response
            balance = self._extract_balance(response)
            currency = self._extract_currency(response)
            
            return CostInfo(
                platform=self.get_platform_name(),
                balance=balance or 0.0,
                currency=currency or 'CNY',
                raw_data=response
            )
        except Exception as e:
            print(f"Warning: Volcengine cookie authentication failed: {e}")
            return CostInfo(
                platform=self.get_platform_name(),
                balance=0.0,
                currency='CNY',
                raw_data={'error': str(e)}
            )
    
    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "Volcengine"
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from Volcengine API response"""
        try:
            # Extract from Result.InvoiceAccount.AvailableAmount
            if 'Result' in response and 'InvoiceAccount' in response['Result']:
                invoice_account = response['Result']['InvoiceAccount']
                balance = invoice_account.get('AvailableAmount') or invoice_account.get('TotalAmount')
                if balance:
                    return float(balance)
        except (ValueError, TypeError, KeyError):
            pass
        
        return None
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from Volcengine API response"""
        return 'CNY'