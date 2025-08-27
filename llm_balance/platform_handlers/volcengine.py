"""
Volcengine platform handler
"""

import json
from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig

class VolcengineHandler(BasePlatformHandler):
    """Volcengine platform cost handler"""
    
    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for Volcengine platform"""
        return {
            "api_url": "https://console.volcengine.com/api/top/bill_volcano_engine/cn-north-1/2020-01-01/GetInvoiceAccount",
            "method": "POST",
            "auth_type": "sdk",
            "env_var": "VOLCENGINE_ACCESS_KEY",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            "params": {},
            "data": {
                "Region": "cn-north-1"
            },
            "enabled": True,
            "cookie_domain": "console.volcengine.com",
            "region": "cn-beijing"
        }
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from Volcengine"""
        # Use cookie authentication as primary method for better reliability
        return self._get_balance_with_cookie()
    
    def _get_balance_with_sdk(self) -> CostInfo:
        """Get balance using Volcengine SDK"""
        try:
            import os
            
            # Get credentials from environment variables
            access_key = os.getenv('VOLCENGINE_ACCESS_KEY')
            secret_key = os.getenv('VOLCENGINE_SECRET_KEY')
            
            if not access_key:
                raise ValueError("VOLCENGINE_ACCESS_KEY environment variable not set")
            if not secret_key:
                raise ValueError("VOLCENGINE_SECRET_KEY environment variable not set")
            
            # Try different SDK initialization approaches
            try:
                # Approach 1: Try volcengine billing service with correct method
                from volcengine.billing.BillingService import BillingService
                billing_service = BillingService()
                billing_service.set_ak(access_key)
                billing_service.set_sk(secret_key)
                
                # Use list_bill for account balance information
                import datetime
                current_month = datetime.datetime.now().strftime('%Y-%m')
                resp = billing_service.list_bill({}, {'BillPeriod': current_month})
                
            except ImportError:
                # Approach 2: Fallback to cookie authentication
                return self._get_balance_with_cookie()
            
            # Parse response based on SDK version
            if not resp:
                raise ValueError("No response from Volcengine SDK")
            
            # Handle different response formats for Volcengine SDK
            balance = 0.0
            currency = 'CNY'
            
            try:
                # Handle dict response from volcengine billing service
                if isinstance(resp, dict):
                    # Check for error response
                    if 'Error' in resp.get('ResponseMetadata', {}):
                        # This is an error response, fallback to cookie
                        raise ValueError("SDK authentication failed")
                    
                    # Try to extract from Result
                    result = resp.get('Result', {})
                    if isinstance(result, dict):
                        # Try different balance fields
                        balance = float(result.get('TotalAmount', result.get('AvailableAmount', 0.0)))
                        currency = result.get('Currency', 'CNY')
                    else:
                        balance = float(resp.get('TotalAmount', resp.get('AvailableAmount', 0.0)))
                        currency = resp.get('Currency', 'CNY')
                
                # Handle object response
                elif hasattr(resp, 'TotalAmount'):
                    balance = float(resp.TotalAmount)
                    currency = getattr(resp, 'Currency', 'CNY')
                elif hasattr(resp, 'available_amount'):
                    balance = float(resp.available_amount)
                    currency = getattr(resp, 'currency', 'CNY')
                    
            except (AttributeError, KeyError, ValueError, TypeError) as e:
                # Fallback to cookie authentication if parsing fails
                print(f"Warning: Volcengine SDK error: {e}")
                return self._get_balance_with_cookie()
            
            return CostInfo(
                platform=self.get_platform_name(),
                balance=balance,
                currency=currency,
                raw_data=resp
            )
            
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
        # New API response format for GetInvoiceAccount
        # Response structure: {Result: {InvoiceAccount: {AvailableAmount: "5.86", TotalAmount: "5.86"}}}
        
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
        # Try different possible response structures for currency
        currency_data = None
        
        # Try structure 1: {Result: {Data: {Currency: ...}}}
        if 'Result' in response:
            result = response['Result']
            if 'Data' in result:
                currency_data = result['Data'].get('Currency')
            else:
                currency_data = result.get('Currency')
        
        # Try structure 2: {Data: {Currency: ...}}
        if not currency_data and 'Data' in response:
            currency_data = response['Data'].get('Currency')
        
        # Try structure 3: Direct currency field
        if not currency_data:
            currency_data = response.get('Currency')
        
        return currency_data or 'CNY'
    
    def _get_csrf_token_from_page(self) -> Optional[str]:
        """Get CSRF token from Volcengine finance overview page"""
        try:
            import requests
            import re
            
            # Try to access the finance overview page to get CSRF token
            overview_url = "https://console.volcengine.com/finance/account-overview/"
            
            # Get cookies for the domain
            cookies = {}
            if self.config.cookie_domain:
                cookies = self._get_cookies(self.config.cookie_domain)
            
            # Make request to the overview page
            response = requests.get(
                overview_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                },
                cookies=cookies,
                timeout=10
            )
            
            if response.status_code == 200:
                # Try to extract CSRF token from HTML content
                # Look for common CSRF token patterns
                patterns = [
                    r'csrfToken["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'csrf_token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'X-CSRF-Token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'meta\s+name="csrf-token"\s+content="([^"]+)"',
                    r'<input\s+type="hidden"\s+name="csrf_token"\s+value="([^"]+)"',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        return match.group(1)
            
            # If we can't get from page, try to extract from cookies again with different patterns
            if cookies:
                for cookie_name in ['csrfToken', 'csrf_token', 'x-csrf-token', 'xsrf-token']:
                    if cookie_name in cookies:
                        return cookies[cookie_name]
            
            return None
            
        except Exception as e:
            print(f"Failed to get CSRF token from page: {e}")
            return None
