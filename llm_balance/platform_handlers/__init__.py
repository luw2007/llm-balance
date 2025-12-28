"""
Platform handlers for different LLM services
"""

from .registry import registry

def create_handler(config, browser: str = 'chrome'):
    """Factory function to create platform handlers using Python-based configuration"""
    # Get handler class from registry
    handler_class = registry.get_handler_class(config.name.lower())
    if handler_class:
        try:
            return handler_class(config, browser)
        except Exception as e:
            print(f"Error creating handler for {config.name}: {e}")
    
    # No fallback - platform must be explicitly supported
    raise ValueError(f"Unsupported platform: {config.name}")
