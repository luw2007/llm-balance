"""
Platform handlers for different LLM services
"""

from .deepseek import DeepSeekHandler
from .moonshot import MoonshotHandler
from .volcengine import VolcengineHandler
from .aliyun import AliyunHandler
from .tencent import TencentHandler
from .zhipu import ZhipuHandler
from .siliconflow_handler import SiliconFlowHandler

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