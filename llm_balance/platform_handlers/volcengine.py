"""
Volcengine platform handler
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime, date, timedelta
from .base import BasePlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig

class VolcengineHandler(BasePlatformHandler):
    """Volcengine platform cost handler"""
    
    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for Volcengine platform"""
        return {
            "api_url": "https://billing.volcengineapi.com",
            "method": "GET",
            "auth_type": "sdk",
            "region": "cn-beijing",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json"
            },
            "params": {},
            "data": {},
            "enabled": True,
            "cookie_domain": "console.volcengine.com"
        }
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from Volcengine"""
        # 根据配置的认证类型选择方法
        if self.config.auth_type == 'sdk':
            try:
                return self._get_balance_with_sdk()
            except Exception as e:
                print(f"Warning: Volcengine SDK authentication failed: {e}")
                return self._get_balance_with_cookies()
        else:
            return self._get_balance_with_cookies()
    
    def _get_balance_with_sdk(self) -> CostInfo:
        """Get balance using Volcengine official SDK"""
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
                
                # Create API instance
                api_instance = volcenginesdkbilling.BILLINGApi()
                
                # Create balance query request
                query_balance_request = QueryBalanceAcctRequest()
                
                # Call API to get balance
                resp = api_instance.query_balance_acct(query_balance_request)
                
                                
                if resp:
                    # Extract balance and calculate spent from billing data
                    balance = self._extract_balance(resp)
                    spent = self._calculate_spent_amount(resp)
                    
                                        
                    return CostInfo(
                        platform=self.get_platform_name(),
                        balance=balance or 0.0,
                        currency='CNY',
                        spent=spent,
                        spent_currency='CNY',
                        raw_data=resp
                    )
                else:
                    raise ValueError("No response from Volcengine API")
                    
            except ImportError as e:
                return self._get_balance_with_cookies()
            except ApiException as e:
                return self._get_balance_with_cookies()
                
        except Exception as e:
            return self._get_balance_with_cookies()
    
    def _get_balance_with_cookies(self) -> CostInfo:
        """Get balance using browser cookies"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for Volcengine")
        
        # Get cookies
        cookies = {}
        if self.config.cookie_domain:
            cookies = self._get_cookies(self.config.cookie_domain)
        
        # Check if we have necessary cookies for authentication
        if not cookies:
            raise ValueError("No authentication cookies found")
        
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
            
            # Extract balance and calculate spent
            balance = self._extract_balance(response)
            spent = self._calculate_spent_amount(response)
            
            return CostInfo(
                platform=self.get_platform_name(),
                balance=balance or 0.0,
                currency='CNY',
                spent=spent,
                spent_currency='CNY',
                raw_data=response
            )
        except Exception as e:
            raise ValueError(f"Volcengine cookie authentication failed: {e}")
    
    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "Volcengine"
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from Volcengine API response"""
        try:
            # Handle SDK response object - check for balance_acct_result first (legacy)
            if hasattr(response, 'balance_acct_result'):
                result = response.balance_acct_result

                if hasattr(result, 'available_amount'):
                    return self._validate_balance(float(result.available_amount), "available_amount")
                elif hasattr(result, 'AvailableAmount'):
                    return self._validate_balance(float(result.AvailableAmount), "AvailableAmount")
                elif hasattr(result, 'total_amount'):
                    return self._validate_balance(float(result.total_amount), "total_amount")
                elif hasattr(result, 'TotalAmount'):
                    return self._validate_balance(float(result.TotalAmount), "TotalAmount")

            # Try direct attributes on response - check for new API structure
            # Define field priority (available > cash > total)
            balance_attributes = [
                'available_balance', 'AvailableBalance',
                'cash_balance', 'CashBalance',
                'available_amount', 'AvailableAmount',
                'balance', 'Balance',
                'total_amount', 'TotalAmount'
            ]

            for attr in balance_attributes:
                if hasattr(response, attr):
                    value = getattr(response, attr)
                    if value is not None and value != '-':
                        try:
                            balance_float = float(value)
                            validated_balance = self._validate_balance(balance_float, attr)
                            if validated_balance > 0:
                                return validated_balance
                        except (ValueError, TypeError):
                            continue

            # Handle dict response (legacy format)
            if isinstance(response, dict):
                # Extract from Result.InvoiceAccount.AvailableAmount
                if 'Result' in response and 'InvoiceAccount' in response['Result']:
                    invoice_account = response['Result']['InvoiceAccount']
                    balance = invoice_account.get('AvailableAmount') or invoice_account.get('TotalAmount')
                    if balance:
                        return self._validate_balance(float(balance), "AvailableAmount")

        except (ValueError, TypeError, KeyError) as e:
            pass

        return 0.0
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from Volcengine API response"""
        return 'CNY'
    
    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get model-level token information from Volcengine"""
        # 根据配置的认证类型选择方法
        if self.config.auth_type == 'sdk':
            try:
                return self._get_model_tokens_with_sdk()
            except Exception as e:
                print(f"Warning: Volcengine SDK authentication failed: {e}")
                return self._get_model_tokens_with_cookies()
        else:
            return self._get_model_tokens_with_cookies()
    
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
                return self._get_model_tokens_with_cookies()
            except ApiException as e:
                print(f"Warning: Volcengine API error: {e}")
                return self._get_model_tokens_with_cookies()
                
        except ImportError:
            # SDK not available, fallback to cookie authentication
            print("Warning: Volcengine SDK not found, falling back to cookie authentication")
            return self._get_model_tokens_with_cookies()
        except Exception as e:
            # SDK authentication failed, fallback to cookie authentication
            print(f"Warning: Volcengine SDK authentication failed: {e}, falling back to cookie authentication")
            return self._get_model_tokens_with_cookies()
    
    def _get_model_tokens_with_cookies(self) -> PlatformTokenInfo:
        """Get model-level tokens using browser cookies"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for Volcengine")
        
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
                    available_amount = float(package.get('available_amount') or package.get('AvailableAmount') or 0)
                
                if hasattr(package, 'total_amount'):
                    total_amount = float(package.total_amount)
                elif hasattr(package, 'TotalAmount'):
                    total_amount = float(package.TotalAmount)
                elif isinstance(package, dict):
                    total_amount = float(package.get('total_amount') or package.get('TotalAmount') or 0)
                
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
                    model=model_name.lower(),
                    package=package_name,
                    remaining_tokens=available_amount,
                    used_tokens=used_tokens,
                    total_tokens=total_amount
                ))
        
        except Exception as e:
            print(f"Warning: Error extracting model tokens from packages: {e}")
            # Fallback to estimation if API data extraction fails
            return self._extract_model_tokens(response)
        
        return models
    
    def _calculate_spent_amount(self, response: Dict[str, Any]) -> float:
        """Calculate spent amount from Volcengine billing API"""
        try:
            # Use the billing API to get actual consumption data
            return self._get_spent_from_billing_api()
        except Exception:
            # Fallback to simple calculation if billing API fails
            return 0.0
    
    def _get_spent_from_billing_api(self) -> float:
        """Get spent amount from Volcengine billing API using ListBillOverviewByCategory"""
        try:
            import os
            from volcenginesdkcore.rest import ApiException
            
            # Get credentials from environment variables
            access_key = os.getenv('VOLCENGINE_ACCESS_KEY')
            secret_key = os.getenv('VOLCENGINE_SECRET_KEY')
            
            if not access_key or not secret_key:
                return 0.0
            
            try:
                # Import official SDK
                import volcenginesdkcore
                import volcenginesdkbilling
                
                # Configure SDK
                configuration = volcenginesdkcore.Configuration()
                configuration.ak = access_key
                configuration.sk = secret_key
                configuration.region = self.config.region or "cn-beijing"
                volcenginesdkcore.Configuration.set_default(configuration)
                
                # Use billing API to get actual consumption data
                api_instance = volcenginesdkbilling.BILLINGApi()
                
                total_spent = 0.0
                
                # Use ListBillOverviewByCategory API as specified
                try:
                    from volcenginesdkbilling.models import ListBillOverviewByCategoryRequest
                    
                    # Try current month and previous months
                    current_date = datetime.now()
                    months_to_try = []
                    
                    # Add current month and previous 5 months
                    for i in range(6):
                        month_date = current_date - timedelta(days=30 * i)
                        months_to_try.append(month_date.strftime("%Y-%m"))
                    
                    for month in months_to_try:
                        try:
                            list_bill_overview_request = ListBillOverviewByCategoryRequest(
                                bill_period=month
                            )
                            
                            # Call ListBillOverviewByCategory API
                            resp = api_instance.list_bill_overview_by_category(list_bill_overview_request)
                            
                            if resp and hasattr(resp, 'list') and resp.list:
                                # The response has a nested structure: resp.list[0].list contains actual bill items
                                overview_items = []
                                for convert_item in resp.list:
                                    if hasattr(convert_item, 'list') and convert_item.list:
                                        # Add actual bill items from the nested list
                                        for bill_item in convert_item.list:
                                            overview_items.append(bill_item)
                                
                                # Sum up amounts from consumption items, skip total items
                                for item in overview_items:
                                    # Only add amounts for "消费" (consumption) items, skip "合计" (total) items
                                    bill_category = getattr(item, 'bill_category_parent', '')
                                    
                                    if bill_category == '合计':
                                        continue  # Skip total items to avoid double counting
                                    
                                    # Try different amount fields based on the actual API response
                                    amount_fields = [
                                        'original_bill_amount', 'OriginalBillAmount',
                                        'paid_amount', 'PaidAmount',
                                        'pretax_amount', 'PretaxAmount',
                                        'posttax_amount', 'PosttaxAmount',
                                        'real_value', 'RealValue',
                                        'cash_amount', 'CashAmount',
                                        'amount', 'Amount'
                                    ]
                                    
                                    for field in amount_fields:
                                        if hasattr(item, field):
                                            value = getattr(item, field)
                                            if value and value != '-' and str(value) != '0.00':
                                                try:
                                                    amount = float(value)
                                                    total_spent += amount
                                                    break
                                                except (ValueError, TypeError):
                                                    continue
                                
                                # Stop searching if we found spending data
                                if total_spent > 0:
                                    break
                        
                        except ApiException as e:
                            # Rate limiting or other API errors, continue to next month
                            if e.status == 429:  # Too Many Requests
                                continue
                            raise
                            
                except (ImportError, ApiException) as e:
                    # Fallback to simple calculation if billing API fails
                    pass
                
                # Return the total spent amount
                return total_spent
                
            except ImportError:
                return 0.0
            except ApiException as e:
                return 0.0
                
        except Exception as e:
            return 0.0
    
    def _extract_model_tokens(self, response) -> List[ModelTokenInfo]:
        """Extract model-level token information from Volcengine response using ConfigurationName"""
        return self._extract_model_tokens_from_packages(response)