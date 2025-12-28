"""
Platform registry to centralize platform-to-handler mapping.
"""

from typing import Dict, Any, List, Optional, Type

class PlatformRegistry:
    """Registry for LLM platform handlers"""
    
    def __init__(self):
        self._handlers = {}
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization to avoid circular imports"""
        if self._initialized:
            return
            
        from .deepseek import DeepSeekHandler
        from .moonshot import MoonshotHandler
        from .volcengine import VolcengineHandler
        from .aliyun import AliyunHandler
        from .tencent import TencentHandler
        from .zhipu import ZhipuHandler
        from .siliconflow import SiliconFlowHandler
        from .openai import OpenAIHandler
        from .anthropic import AnthropicHandler
        from .google import GoogleHandler
        from .foxcode import FoxCodeHandler
        from .duckcoding import DuckCodingHandler
        from .packycode import PackyCodeHandler
        from ._88code import Handler88Code
        from ._88996 import Handler88996
        from .yourapi import YourAPIHandler
        from .csmindai import CSMindAIHandler
        from .yescode import YesCodeHandler
        from .oneapi import OneAPIHandler
        from .apiproxy import APIProxyHandler
        from .fastgpt import FastGPTHandler
        from .minimax import MiniMaxHandler
        from .cubence import CubenceHandler
        from .aicoding import AICodingHandler
        from .dawclaudecode import DawClaudeCodeHandler
        from .magic666 import Magic666Handler
        from .jimiai import JimiaiHandler
        from .openclaudecode import OpenClaudeCodeHandler
        from .ikuncode import IKunCodeHandler

        self._handlers = {
            'deepseek': DeepSeekHandler,
            'moonshot': MoonshotHandler,
            'volcengine': VolcengineHandler,
            'aliyun': AliyunHandler,
            'tencent': TencentHandler,
            'zhipu': ZhipuHandler,
            'siliconflow': SiliconFlowHandler,
            'openai': OpenAIHandler,
            'anthropic': AnthropicHandler,
            'google': GoogleHandler,
            'foxcode': FoxCodeHandler,
            'duckcoding': DuckCodingHandler,
            'packycode': PackyCodeHandler,
            '88code': Handler88Code,
            '88996': Handler88996,
            'yourapi': YourAPIHandler,
            'csmindai': CSMindAIHandler,
            'yescode': YesCodeHandler,
            'oneapi': OneAPIHandler,
            'apiproxy': APIProxyHandler,
            'fastgpt': FastGPTHandler,
            'minimax': MiniMaxHandler,
            'cubence': CubenceHandler,
            'aicoding': AICodingHandler,
            'dawclaudecode': DawClaudeCodeHandler,
            'magic666': Magic666Handler,
            'jimiai': JimiaiHandler,
            'openclaudecode': OpenClaudeCodeHandler,
            'ikuncode': IKunCodeHandler,
        }
        self._initialized = True

    def get_handler_class(self, platform_name: str) -> Optional[Type]:
        """Get handler class for a platform"""
        self._ensure_initialized()
        return self._handlers.get(platform_name.lower())

    def list_platforms(self) -> List[str]:
        """List all available platform names"""
        self._ensure_initialized()
        return sorted(list(self._handlers.keys()))

    def get_all_handlers(self) -> Dict[str, Type]:
        """Get all registered handlers"""
        self._ensure_initialized()
        return self._handlers.copy()

    def get_platform(self, platform_name: str):
        """
        Get platform info (mimicking expectation in error_handler.py)
        Actually returns a proxy object or just enough info.
        """
        handler_cls = self.get_handler_class(platform_name)
        if not handler_cls:
            return None
            
        # Many handlers have get_default_config() which contains metadata
        config = handler_cls.get_default_config()
        
        # Create a simple data object for compatibility
        class PlatformInfoProxy:
            def __init__(self, name, config):
                self.name = name
                self.display_name = config.get('display_name', name.title())
                self.description = config.get('description', f"{self.display_name} platform")
                self.auth_type = config.get('auth_type', 'api_key')
                self.env_var = config.get('env_var')
                self.setup_steps = config.get('setup_steps', [])
                self.notes = config.get('notes', [])
                self.official_url = config.get('official_url', '')
                self.api_management_url = config.get('api_management_url', '')
                
        return PlatformInfoProxy(platform_name, config)

# Global registry instance
registry = PlatformRegistry()
