"""
Base handler for platform cost checking
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field

@dataclass
class CostInfo:
    platform: str
    balance: float
    currency: str
    raw_data: Dict[str, Any]
    spent: Union[float, str] = 0.0
    spent_currency: str = None

@dataclass
class ModelTokenInfo:
    model: str
    package: str
    remaining_tokens: float
    used_tokens: float
    total_tokens: float
    status: str = "active"
    expiry_date: Optional[str] = None
    reset_count: Optional[int] = None
    reset_time: Optional[str] = None

@dataclass
class PlatformTokenInfo:
    platform: str
    models: List[ModelTokenInfo]
    raw_data: Dict[str, Any]

class BasePlatformHandler(ABC):
    """Base class for platform cost handlers"""

    def __init__(self, browser='chrome'):
        self.browser = browser

    def _validate_balance(self, balance: float, field_name: str = "balance") -> float:
        """验证余额值，确保其合理性"""
        if balance is None:
            return 0.0

        try:
            balance_float = float(balance)
        except (ValueError, TypeError):
            print(f"Warning: Invalid {field_name} value: {balance}, using 0.0")
            return 0.0

        # 处理负数余额
        if balance_float < 0:
            print(f"Warning: Negative {field_name} detected: {balance_float}, using 0.0")
            return 0.0

        # 处理异常大值（超过100万）
        if balance_float > 1000000:
            print(f"Warning: Extremely large {field_name} detected: {balance_float}, using 0.0")
            return 0.0

        return balance_float
        
    @abstractmethod
    def get_balance(self) -> CostInfo:
        """Get cost information for the platform"""
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Get platform display name"""
        pass
    
    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get model-level token information for the platform (optional)"""
        raise NotImplementedError(f"Model token checking not implemented for {self.get_platform_name()}")
    
    def _get_cookies(self, domain: str, silent: bool = True) -> Dict[str, str]:
        """Get cookies for domain using pycookiecheat

        Args:
            domain: The domain to get cookies for
            silent: If True, suppress warning messages when cookies are not found (default: True)
        """
        # Check if browser is None (non-cookie authentication)
        if self.browser is None:
            raise ValueError(f"This platform doesn't use cookie-based authentication. Please check your API key configuration.")
        
        try:
            import pycookiecheat
            from pycookiecheat.common import BrowserType
            
            # Map browser names to pycookiecheat BrowserType
            browser_mapping = {
                'chrome': BrowserType.CHROME,
                'firefox': BrowserType.FIREFOX,
                'brave': BrowserType.BRAVE,
                'chromium': BrowserType.CHROMIUM,
                'slack': BrowserType.SLACK,
            }

            # Chromium-based browsers with custom cookie paths
            chromium_custom_paths = {
                'arc': {
                    'path': '~/Library/Application Support/Arc/User Data/Default/Cookies',
                    'keyring_service': 'Arc Safe Storage',
                    'keyring_user': 'Arc',
                },
                'vivaldi': {
                    'path': '~/Library/Application Support/Vivaldi/Default/Cookies',
                    'keyring_service': 'Vivaldi Safe Storage',
                    'keyring_user': 'Vivaldi',
                },
            }

            # Get the browser type, default to chrome
            browser_lower = self.browser.lower()
            supported_browsers = list(browser_mapping.keys()) + list(chromium_custom_paths.keys())
            if browser_lower not in supported_browsers:
                raise ValueError(f"Browser '{self.browser}' is not supported. Try: {', '.join(supported_browsers)}")

            # Special handling for Arc and Vivaldi browsers
            if browser_lower in chromium_custom_paths:
                # Arc and Vivaldi have different cookie path structures and keyring passwords
                browser_config = chromium_custom_paths[browser_lower]
                return self._get_chromium_custom_cookies(
                    domain,
                    browser_config['path'],
                    browser_config['keyring_service'],
                    browser_config['keyring_user'],
                    silent=silent
                )

            browser_type = browser_mapping[browser_lower]

            # Use appropriate function based on browser family
            if browser_type in [BrowserType.FIREFOX]:
                cookies = pycookiecheat.firefox_cookies(domain, browser=browser_type)
            else:
                cookies = pycookiecheat.chrome_cookies(domain, browser=browser_type)

            if not cookies and not silent:
                print(f"Warning: No cookies found for {domain}. Please ensure you are logged in to {domain} in {self.browser} browser.")
            return cookies
            
        except ImportError:
            raise ValueError(f"pycookiecheat library not found. Please install it with: pip install pycookiecheat")
        except Exception as e:
            # Check for common browser issues
            if "is not a valid BrowserType" in str(e):
                raise ValueError(f"Browser '{self.browser}' is not supported. Try: {', '.join(browser_mapping.keys())}")
            elif "No such file or directory" in str(e):
                raise ValueError(f"Browser profile not found for {self.browser}. Please ensure {self.browser} is installed and running.")
            else:
                raise ValueError(f"Failed to get cookies for {domain}: {e}. Please ensure you are logged in to {domain} in {self.browser} browser.")
    
    def _get_chromium_custom_cookies(self, domain: str, cookie_path_pattern: str,
                                     keyring_service: str, keyring_user: str,
                                     silent: bool = True) -> Dict[str, str]:
        """Get cookies for Chromium-based browsers with custom cookie paths (Arc, Vivaldi, etc.)

        Args:
            domain: The domain to get cookies for
            cookie_path_pattern: Path pattern for cookie file (supports ~ expansion)
            keyring_service: Keyring service name for the browser (e.g., 'Vivaldi Safe Storage')
            keyring_user: Keyring username for the browser (e.g., 'Vivaldi')
            silent: If True, suppress warning messages when cookies are not found (default: True)
        """
        try:
            from pathlib import Path
            import keyring
            import pycookiecheat

            # Expand and resolve cookie file path
            cookie_file = Path(cookie_path_pattern).expanduser().resolve()

            # Check if cookie file exists
            if not cookie_file.exists():
                raise ValueError(f"Cookie file not found at {cookie_file}. Please ensure the browser is installed.")

            # Get browser's Safe Storage password from keyring
            password = keyring.get_password(keyring_service, keyring_user)
            if password is None:
                raise ValueError(
                    f"Could not find password for keyring ({keyring_service}, {keyring_user}). "
                    f"Please verify the browser is installed and check Keychain Access.app"
                )

            # Prepare URL for pycookiecheat
            url = f"https://{domain}" if not domain.startswith('http') else domain

            # Use pycookiecheat with custom cookie file and browser-specific password
            cookies = pycookiecheat.chrome_cookies(
                url=url,
                cookie_file=cookie_file,
                password=password
            )

            if not cookies and not silent:
                print(f"Warning: No cookies found for {domain}. Please ensure you are logged in to {domain}.")

            return cookies

        except Exception as e:
            raise ValueError(f"Failed to get cookies for {domain}: {e}. Please ensure you are logged in to {domain}.")

    def _get_arc_cookies(self, domain: str, silent: bool = True) -> Dict[str, str]:
        """Get cookies for Arc browser using custom implementation

        Args:
            domain: The domain to get cookies for
            silent: If True, suppress warning messages when cookies are not found (default: True)

        Note: This method is kept for backward compatibility but delegates to _get_chromium_custom_cookies
        """
        return self._get_chromium_custom_cookies(
            domain,
            '~/Library/Application Support/Arc/User Data/Default/Cookies',
            'Arc Safe Storage',
            'Arc',
            silent
        )
    
    def _chrome_decrypt(self, encrypted_value: bytes, key: bytes, init_vector: bytes) -> str:
        """Decrypt Chrome/Chromium's encrypted cookies"""
        from cryptography.hazmat.primitives.ciphers import Cipher
        from cryptography.hazmat.primitives.ciphers.algorithms import AES
        from cryptography.hazmat.primitives.ciphers.modes import CBC
        
        # Remove v10/v11 prefix
        encrypted_value = encrypted_value[3:]
        
        # Decrypt
        cipher = Cipher(algorithm=AES(key), mode=CBC(init_vector))
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted_value) + decryptor.finalize()
        
        # Remove padding
        last = decrypted[-1]
        if isinstance(last, int):
            return decrypted[32:-last].decode("utf8", errors="ignore")
        try:
            return decrypted[32: -ord(last)].decode("utf8", errors="ignore")
        except UnicodeDecodeError:
            raise ValueError("Failed to decrypt cookie value")
    
    def _generate_host_keys(self, domain: str):
        """Generate host keys for domain matching"""
        import re
        from urllib.parse import urlparse
        
        # Extract domain from URL if needed
        if domain.startswith('http'):
            parsed = urlparse(domain)
            domain = parsed.netloc
        
        # Remove port if present
        domain = domain.split(':')[0]
        
        # Generate variations
        yield domain
        if '.' in domain:
            yield '.' + domain.split('.', 1)[1]
    
    def _make_request(self, url: str, method: str = 'GET', 
                     headers: Optional[Dict] = None, 
                     cookies: Optional[Dict] = None,
                     data: Optional[Dict] = None,
                     params: Optional[Dict] = None,
                     proxies: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request with error handling"""
        import requests
        
        try:
            # For GET requests, use params instead of json
            if method.upper() == 'GET' and params:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers or {},
                    cookies=cookies or {},
                    params=params,
                    timeout=10,
                    proxies=proxies
                )
            elif method.upper() == 'GET' and data:
                # Fallback for backward compatibility
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers or {},
                    cookies=cookies or {},
                    params=data,
                    timeout=10,
                    proxies=proxies
                )
            else:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers or {},
                    cookies=cookies or {},
                    json=data,
                    timeout=10,
                    proxies=proxies
                )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            result = response.json()
            
            # Check for authentication/authorization errors in response
            if isinstance(result, dict):
                # Common authentication error patterns
                error_patterns = [
                    ('code', ['ConsoleNeedLogin', 'Unauthorized', 'AuthenticationFailed', 'InvalidToken', 'InvalidCSRFToken']),
                    ('message', ['needLogin', 'unauthorized', 'authentication failed', 'invalid token', 'login required']),
                    ('error', ['Unauthorized', 'AuthenticationError', 'InvalidToken']),
                    ('success', [False])
                ]
                
                for field, patterns in error_patterns:
                    if field in result:
                        value = result[field]
                        if isinstance(value, str) and any(pattern.lower() in value.lower() for pattern in patterns):
                            raise ValueError(f"Authentication failed: {value}. Please ensure you are logged in and try again.")
                        elif isinstance(value, bool) and not value and field == 'success':
                            # Check if there's an error message
                            if 'message' in result:
                                raise ValueError(f"Request failed: {result['message']}")
                            elif 'error' in result:
                                raise ValueError(f"Request failed: {result['error']}")
            
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError(f"Authentication failed (401): Please check your API key or login status.")
            elif e.response.status_code == 403:
                raise ValueError(f"Access forbidden (403): Please check your permissions or API key.")
            elif e.response.status_code == 429:
                raise ValueError(f"Rate limit exceeded (429): Please try again later.")
            else:
                raise ValueError(f"HTTP error {e.response.status_code}: {e}")
        except requests.exceptions.Timeout:
            raise ValueError(f"Request timeout for {url}: The server took too long to respond.")
        except requests.exceptions.ConnectionError:
            raise ValueError(f"Connection failed for {url}: Please check your internet connection.")
        except ValueError as e:
            # Re-raise ValueError with authentication info
            raise e
        except Exception as e:
            raise ValueError(f"Request failed for {url}: {e}")
