"""
Platform handlers for different LLM services
"""

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
from ._88code import Handler88Code
from .yourapi import YourAPIHandler

def create_handler(config, browser: str = 'chrome'):
    """Factory function to create platform handlers using Python-based configuration"""
    # Import handler classes
    handler_classes = {
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
        '88code': Handler88Code,
        'yourapi': YourAPIHandler,
    }
    
    # Get handler class from configuration
    handler_class = handler_classes.get(config.name.lower())
    if handler_class:
        try:
            return handler_class(config, browser)
        except Exception as e:
            print(f"Error creating handler for {config.name}: {e}")
    
    # No fallback - platform must be explicitly supported
    raise ValueError(f"Unsupported platform: {config.name}")
