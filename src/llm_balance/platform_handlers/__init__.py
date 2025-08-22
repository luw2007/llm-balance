"""
Platform handlers for different LLM services
"""

from .generic import GenericHandler
from .deepseek import DeepSeekHandler
from .volcengine import VolcengineHandler
from .aliyun import AliyunHandler
from .openai import OpenAIHandler
from .claude import ClaudeHandler
from .moonshot import MoonshotHandler
from .gemini import GeminiHandler
from .azure_openai import AzureOpenAIHandler
from .tencent import TencentHandler
from .lingyi import LingyiHandler
from .zhipu import ZhipuHandler

def create_handler(config, browser: str = 'chrome'):
    """Factory function to create platform handlers"""
    # For cookie-based platforms, pass the browser
    # For non-cookie platforms, pass None as browser
    handler_browser = browser if config.auth_type == 'cookie' else None
    
    # Special handling for volcengine with SDK authentication
    if config.name == 'volcengine':
        return VolcengineHandler(config, handler_browser)
    
    if config.name == 'deepseek':
        return DeepSeekHandler(config, handler_browser)
    elif config.name == 'gemini':
        return GeminiHandler(config, handler_browser)
    elif config.name == 'azure_openai':
        return AzureOpenAIHandler(config, handler_browser)
    elif config.name == 'tencent':
        return TencentHandler(config, handler_browser)
    elif config.name == 'lingyi':
        return LingyiHandler(config, handler_browser)
    elif config.name == 'zhipu':
        return ZhipuHandler(config, handler_browser)
    elif config.name == 'aliyun':
        return AliyunHandler(config, handler_browser)
    elif config.name == 'openai':
        return OpenAIHandler(config, handler_browser)
    elif config.name == 'claude':
        return ClaudeHandler(config, handler_browser)
    elif config.name == 'moonshot':
        return MoonshotHandler(config, handler_browser)
    return GenericHandler(config, handler_browser)
