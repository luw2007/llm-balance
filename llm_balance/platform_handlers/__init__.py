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
