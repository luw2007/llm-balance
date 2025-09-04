"""
Volcengine platform handler using official SDK
"""

import os
from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
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
                
                # Calculate spent amount from token packages
                spent = self._calculate_spent_amount()
                
                return CostInfo(
                    platform=self.get_platform_name(),
                    balance=balance,
                    currency=currency,
                    spent=spent,
                    spent_currency=currency,
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
                spent=0.0,
                spent_currency='CNY',
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
            
            # Calculate spent amount from token packages
            spent = self._calculate_spent_amount()
            
            return CostInfo(
                platform=self.get_platform_name(),
                balance=balance or 0.0,
                currency=currency or 'CNY',
                spent=spent,
                spent_currency=currency or 'CNY',
                raw_data=response
            )
        except Exception as e:
            print(f"Warning: Volcengine cookie authentication failed: {e}")
            return CostInfo(
                platform=self.get_platform_name(),
                balance=0.0,
                currency='CNY',
                spent=0.0,
                spent_currency='CNY',
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
    
    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get model-level token information from Volcengine"""
        return self._get_model_tokens_with_sdk()
    
    def _get_model_tokens_with_sdk(self) -> PlatformTokenInfo:
        """Get model-level tokens using official Volcengine SDK with ListResourcePackages API"""
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
                from volcenginesdkbilling.models import ListResourcePackagesRequest
                
                # Configure SDK
                configuration = volcenginesdkcore.Configuration()
                configuration.ak = access_key
                configuration.sk = secret_key
                configuration.region = self.config.region or "cn-beijing"
                volcenginesdkcore.Configuration.set_default(configuration)
                
                # Use ListResourcePackages API for actual model-level token data
                api_instance = volcenginesdkbilling.BILLINGApi()
                list_resource_packages_request = volcenginesdkbilling.ListResourcePackagesRequest(
                    max_results="20",
                    resource_type="Package",
                )
                # Call ListResourcePackages API
                resp = api_instance.list_resource_packages(list_resource_packages_request)
                
                # Parse response from official SDK
                if not resp:
                    raise ValueError("No response from Volcengine SDK")
                
                # Extract actual model-level token data from response
                model_tokens = self._extract_model_tokens_from_packages(resp)
                
                return PlatformTokenInfo(
                    platform=self.get_platform_name(),
                    models=model_tokens,
                    raw_data=resp.__dict__ if hasattr(resp, '__dict__') else str(resp)
                )
                
            except ImportError as e:
                print(f"Warning: Volcengine SDK import error: {e}")
                return self._get_model_tokens_with_cookie()
            except ApiException as e:
                print(f"Warning: Volcengine API error: {e}")
                return self._get_model_tokens_with_cookie()
                
        except ImportError:
            # SDK not available, fallback to cookie authentication
            print("Warning: Volcengine SDK not found, falling back to cookie authentication")
            return self._get_model_tokens_with_cookie()
        except Exception as e:
            # SDK authentication failed, fallback to cookie authentication
            print(f"Warning: Volcengine SDK authentication failed: {e}, falling back to cookie authentication")
            return self._get_model_tokens_with_cookie()
    
    def _get_model_tokens_with_cookie(self) -> PlatformTokenInfo:
        """Get model-level tokens using cookie authentication (fallback)"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for Volcengine cookie authentication")
        
        # Get cookies
        cookies = {}
        if self.config.cookie_domain:
            cookies = self._get_cookies(self.config.cookie_domain)
        
        # Check if we have necessary cookies for authentication
        if not cookies:
            print(f"Warning: No authentication cookies found for {self.config.cookie_domain}. Please ensure you are logged in to Volcengine Console in {self.browser} browser.")
            return PlatformTokenInfo(
                platform=self.get_platform_name(),
                models=[],
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
            
            # Extract model-level token data
            model_tokens = self._extract_model_tokens(response)
            
            return PlatformTokenInfo(
                platform=self.get_platform_name(),
                models=model_tokens,
                raw_data=response
            )
        except Exception as e:
            print(f"Warning: Volcengine cookie authentication failed: {e}")
            return PlatformTokenInfo(
                platform=self.get_platform_name(),
                models=[],
                raw_data={'error': str(e)}
            )
    
    def _extract_model_tokens_from_packages(self, response) -> List[ModelTokenInfo]:
        """Extract actual model-level token information from ListResourcePackages response"""
        models = []
        
        try:
            # Extract package list from response
            package_list = []
            
            # Handle SDK response format
            if hasattr(response, 'list') and response.list:
                package_list = response.list
            elif hasattr(response, 'List') and response.List:
                package_list = response.List
            elif isinstance(response, dict):
                # Handle dict response
                result = response.get('Result', response.get('result', {}))
                package_list = result.get('List', result.get('list', []))
            
            # Process each package
            for package in package_list:
                if not package:
                    continue
                
                # Extract package details
                config_name = None
                available_amount = 0
                total_amount = 0
                unit = None
                status = None
                
                # Handle both object and dict formats
                if hasattr(package, 'configuration_name'):
                    config_name = package.configuration_name
                elif hasattr(package, 'ConfigurationName'):
                    config_name = package.ConfigurationName
                elif isinstance(package, dict):
                    config_name = package.get('configuration_name') or package.get('ConfigurationName')
                
                if hasattr(package, 'available_amount'):
                    available_amount = float(package.available_amount)
                elif hasattr(package, 'AvailableAmount'):
                    available_amount = float(package.AvailableAmount)
                elif isinstance(package, dict):
                    available_amount = float(package.get('available_amount', 0) or package.get('AvailableAmount', 0))
                
                if hasattr(package, 'total_amount'):
                    total_amount = float(package.total_amount)
                elif hasattr(package, 'TotalAmount'):
                    total_amount = float(package.TotalAmount)
                elif isinstance(package, dict):
                    total_amount = float(package.get('total_amount', 0) or package.get('TotalAmount', 0))
                
                if hasattr(package, 'unit'):
                    unit = package.unit
                elif hasattr(package, 'Unit'):
                    unit = package.Unit
                elif isinstance(package, dict):
                    unit = package.get('unit') or package.get('Unit')
                
                if hasattr(package, 'status'):
                    status = package.status
                elif hasattr(package, 'Status'):
                    status = package.Status
                elif isinstance(package, dict):
                    status = package.get('status') or package.get('Status')
                
                # Only process token-based packages that are effective and have remaining tokens
                if unit != "token" or available_amount <= 0:
                    continue
                
                # Skip used-up packages
                if status and str(status).upper() == "USEDUP":
                    continue
                
                # Extract package/model name from ConfigurationName using regex
                import re
                package_name = config_name or "Unknown Model"
                model_name = config_name or "Unknown Model"
                if config_name:
                    # Extract English prefix from ConfigurationName
                    match = re.search(r'^([A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*)', config_name)
                    if match:
                        model_name = match.group(1)
                
                
                # Calculate used tokens
                used_tokens = max(0, total_amount - available_amount)
                
                models.append(ModelTokenInfo(
                    package=package_name,
                    model=model_name.lower(),
                    remaining_tokens=available_amount,
                    used_tokens=used_tokens,
                    total_tokens=total_amount
                ))
        
        except Exception as e:
            print(f"Warning: Error extracting model tokens from packages: {e}")
            # Fallback to estimation if API data extraction fails
            return self._extract_model_tokens(response)
        
        return models
    
    def _calculate_spent_amount(self) -> float:
        """Calculate spent amount from token packages"""
        try:
            # Get token information to calculate spent amount
            token_info = self.get_model_tokens()
            total_spent = 0.0
            
            for model in token_info.models:
                # Calculate spent tokens for each package
                spent_tokens = model.used_tokens
                
                # Convert tokens to monetary value (rough estimation)
                # This is a simplified calculation - in practice, you'd need actual pricing
                if model.total_tokens > 0:
                    # Estimate cost based on token usage (assuming ~$0.002 per 1K tokens as rough estimate)
                    spent_amount = (spent_tokens / 1000) * 0.002 * 7.2  # Convert to CNY
                    total_spent += spent_amount
            
            return total_spent
        except Exception:
            # If calculation fails, return 0
            return 0.0
    
    def _extract_model_tokens(self, response) -> List[ModelTokenInfo]:
        """Extract model-level token information from Volcengine response using ConfigurationName"""
        return self._extract_model_tokens_from_packages(response)
    
