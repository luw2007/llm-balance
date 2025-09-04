"""
Zhipu AI (智谱AI) platform handler
"""

import json
from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig

class ZhipuHandler(BasePlatformHandler):
    """Zhipu AI (智谱AI) platform cost handler"""
    
    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for Zhipu AI platform"""
        return {
            "api_url": "https://bigmodel.cn/api/biz/customer/accountSet",
            "method": "GET",
            "auth_type": "cookie",
            "env_var": None,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json"
            },
            "params": {},
            "data": {},
            "enabled": True,
            "cookie_domain": ".bigmodel.cn"
        }
    
    def __init__(self, config, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
    
    def get_balance(self) -> CostInfo:
        """Get cost information from Zhipu AI"""
        api_url = self.config.get('api_url') if isinstance(self.config, dict) else self.config.api_url
        if not api_url:
            raise ValueError("No API URL configured for Zhipu AI")
        
        # Prepare authentication
        headers = self.config.headers.copy()
        
        # Get cookies
        cookies = {}
        if self.config.cookie_domain:
            cookies = self._get_cookies(self.config.cookie_domain)
        
        # Check if we have necessary cookies for authentication
        if not cookies:
            raise ValueError(f"No authentication cookies found for {self.config.cookie_domain}. Please ensure you are logged in to Zhipu AI in {self.browser} browser.")
        
        # Try different possible cookie names for authentication
        auth_cookie = None
        for cookie_name in ['bigmodel_token_production', 'token', 'session_token', 'auth_token']:
            if cookie_name in cookies:
                auth_cookie = cookies[cookie_name]
                break
        if not auth_cookie:
            raise ValueError(f"No authentication token found in cookies for {self.config.cookie_domain}. Please ensure you are logged in to Zhipu AI.")
        
        headers['authorization'] = auth_cookie
        
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
        
        # Calculate spent amount from API response
        spent = self._calculate_spent_amount(response)
        
        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance or 0.0,
            currency=currency or 'CNY',
            spent=spent,
            spent_currency=currency or 'CNY',
            raw_data=response
        )
    
    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "Zhipu AI"
    
    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get model-level token information from Zhipu AI using new token API"""
        if not self.config.api_url:
            raise ValueError("No API URL configured for Zhipu AI")
        
        # Token API endpoint
        token_api_url = "https://bigmodel.cn/api/biz/tokenAccounts/list"
        
        # Prepare authentication
        headers = self.config.headers.copy()
        
        # Get cookies
        cookies = {}
        if self.config.cookie_domain:
            cookies = self._get_cookies(self.config.cookie_domain)
        
        # Check if we have necessary cookies for authentication
        if not cookies:
            raise ValueError(f"No authentication cookies found for {self.config.cookie_domain}. Please ensure you are logged in to Zhipu AI in {self.browser} browser.")
        
        # Try different possible cookie names for authentication
        auth_cookie = None
        for cookie_name in ['bigmodel_token_production', 'token', 'session_token', 'auth_token']:
            if cookie_name in cookies:
                auth_cookie = cookies[cookie_name]
                break
        if not auth_cookie:
            raise ValueError(f"No authentication token found in cookies for {self.config.cookie_domain}. Please ensure you are logged in to Zhipu AI.")
        
        headers['authorization'] = auth_cookie
        
        # Make API request to token endpoint
        params = {
            'pageNum': 1,
            'pageSize': 50,  # Increase page size to get all packages
            'filterEnabled': 'false'
        }
        
        response = self._make_request(
            url=token_api_url,
            method='GET',
            headers=headers,
            params=params
        )
        
        if not response:
            raise ValueError("No response from Zhipu AI token API")
        
        # Parse token data from response
        models = self._extract_model_tokens(response)
        
        return PlatformTokenInfo(
            platform=self.get_platform_name(),
            models=models,
            raw_data=response
        )
    
    def _extract_model_tokens(self, response: Dict[str, Any]) -> List[ModelTokenInfo]:
        """Extract model token information from Zhipu AI token API response"""
        models = []
        
        # Get rows from response - handle both direct rows and nested data structure
        data = response.get('data', {})
        if isinstance(data, dict):
            rows = data.get('rows', [])
        else:
            rows = data if isinstance(data, list) else []
        
        # If no rows found, try to get from response directly
        if not rows:
            rows = response.get('rows', [])
        
        for row in rows:
            # Only process effective packages
            if row.get('status') != 'EFFECTIVE':
                continue
            
            # Extract package information - always use resourcePackageName for display
            package_name = row.get('resourcePackageName', row.get('name', 'Unknown Package'))
            
            # Extract model name using suitableModel field, fallback to package name
            model_name = row.get('suitableModel', package_name)
            
            # Get available balance - handle both availableBalance and remaining tokens
            available_balance = float(row.get('availableBalance', row.get('remaining', 0)))
            
            # Always extract total from package name since API returns remaining as "total"
            extracted_total, unit = self._extract_tokens_from_package_name(package_name)
            
            if extracted_total > 0:
                token_balance = extracted_total
                # For usage-based packages (次), available is the count, total is the original
                if unit == '次':
                    used_tokens = max(0, token_balance - available_balance)
                else:
                    # For token-based packages, calculate used from the difference
                    used_tokens = max(0, token_balance - available_balance)
            else:
                # Fallback to API values if extraction fails
                token_balance = float(row.get('tokenBalance', row.get('total', available_balance)))
                used_tokens = max(0, token_balance - available_balance)
            
            # Create model token info with package name as primary identifier
            model_info = ModelTokenInfo(
                model=model_name.lower(),
                package=package_name,  # Always use resourcePackageName for display
                remaining_tokens=available_balance,
                used_tokens=used_tokens,
                total_tokens=token_balance
            )
            models.append(model_info)
        
        # Sort models by remaining tokens (descending) for better display
        models.sort(key=lambda x: x.remaining_tokens, reverse=True)
        
        return models
    
    def _extract_tokens_from_package_name(self, package_name: str) -> tuple[float, str]:
        """Extract token count and unit from Chinese package names like '1亿GLM-4.5资源包' or '100次视频资源包'"""
        import re
        
        # Chinese number mappings
        chinese_numbers = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '百': 100, '千': 1000, '万': 10000, '亿': 100000000
        }
        
        # First check for 次 (times) unit
        times_patterns = [
            r'(\d+)次',           # 100次, 50次
            r'(\d+)次',           # 100次 (with Chinese)
        ]
        
        for pattern in times_patterns:
            match = re.search(pattern, package_name)
            if match:
                number_str = match.group(1)
                try:
                    return float(number_str), '次'
                except ValueError:
                    continue
        
        # Patterns for token counts: 1亿, 1000万, 200万, etc.
        token_patterns = [
            r'(\d+)亿',           # 1亿, 100亿
            r'(\d+)万',           # 1000万, 200万
            r'(\d+)千',           # 1000千
            r'(\d+)百',           # 200百
            r'(\d+)',             # plain numbers like 200
        ]
        
        for pattern in token_patterns:
            match = re.search(pattern, package_name)
            if match:
                number_str = match.group(1)
                try:
                    base_number = float(number_str)
                    
                    # Check for unit suffixes
                    if '亿' in package_name:
                        return base_number * 100000000, 'tokens'
                    elif '万' in package_name:
                        return base_number * 10000, 'tokens'
                    elif '千' in package_name:
                        return base_number * 1000, 'tokens'
                    elif '百' in package_name:
                        return base_number * 100, 'tokens'
                    else:
                        return base_number, 'tokens'
                except ValueError:
                    continue
        
        # Handle Chinese character numbers like "二百" or "一千"
        chinese_pattern = r'([一二三四五六七八九十百千万亿]+)'
        match = re.search(chinese_pattern, package_name)
        if match:
            chinese_str = match.group(1)
            try:
                # Simple conversion for common patterns
                if '亿' in chinese_str:
                    return 100000000, 'tokens'
                elif '万' in chinese_str:
                    # Extract the number before 万
                    num_match = re.search(r'(\d+|[一二三四五六七八九十])万', chinese_str)
                    if num_match:
                        num_str = num_match.group(1)
                        if num_str.isdigit():
                            return float(num_str) * 10000, 'tokens'
                        else:
                            return chinese_numbers.get(num_str, 1) * 10000, 'tokens'
                    return 10000, 'tokens'  # Default 1万
                elif '千' in chinese_str:
                    return 1000, 'tokens'
                elif '百' in chinese_str:
                    return 100, 'tokens'
                else:
                    return 2000000, 'tokens'  # Default 200万 for common packages
            except:
                pass
        
        return 0, 'tokens'
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from Zhipu AI API response"""
        # Zhipu AI response format: {"code": 200, "msg": "操作成功", "data": {"basicCustomerInfo": {"balance": 100.00}}, "success": true}
        result = response.get('data', {}).get('basicCustomerInfo', {})
        if 'balance' in result:
            try:
                return float(result['balance'])
            except (ValueError, TypeError):
                return None
        return None
    
    def _calculate_spent_amount(self, response: Dict[str, Any]) -> float:
        """Calculate spent amount from Zhipu billing API"""
        try:
            # Use the billing API to get spent amount
            billing_api_url = "https://www.bigmodel.cn/api/finance/monthlyBill/aggregatedMonthlyBills"
            
            # Calculate date range for last 6 months
            from datetime import datetime, date
            today = date.today()
            end_month = today.strftime("%Y-%m")
            
            # Calculate start month (6 months ago)
            start_year = today.year
            start_month = today.month - 5
            if start_month <= 0:
                start_year -= 1
                start_month += 12
            start_month_str = f"{start_year}-{start_month:02d}"
            
            params = {
                'billingMonthStart': start_month_str,
                'billingMonthEnd': end_month,
                'pageNum': 1,
                'pageSize': 10
            }
            
            # Prepare authentication
            headers = self.config.headers.copy()
            cookies = {}
            if self.config.cookie_domain:
                cookies = self._get_cookies(self.config.cookie_domain)
            
            if cookies:
                auth_cookie = None
                for cookie_name in ['bigmodel_token_production', 'token', 'session_token', 'auth_token']:
                    if cookie_name in cookies:
                        auth_cookie = cookies[cookie_name]
                        break
                if auth_cookie:
                    headers['authorization'] = auth_cookie
            
            # Make billing API request
            billing_response = self._make_request(
                url=billing_api_url,
                method='GET',
                headers=headers,
                params=params
            )
            
            if billing_response and billing_response.get('code') == 200:
                rows = billing_response.get('rows', [])
                total_spent = 0.0
                
                # Sum up paid amounts from all billing periods
                for row in rows:
                    paid_amount = row.get('paidAmount', 0)
                    if paid_amount:
                        total_spent += float(paid_amount)
                
                return total_spent
            
            return 0.0
            
        except Exception as e:
            # If billing API fails, return 0.0
            return 0.0
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from Zhipu AI API response"""
        try:
            result = response.get('data', {})
            if 'currency' in result:
                return result['currency']
        except (ValueError, TypeError, KeyError):
            pass
        return 'CNY'
