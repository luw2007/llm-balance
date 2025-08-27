# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool for checking costs and balances across multiple LLM platforms. The tool supports multiple authentication methods, multi-currency conversion, global browser configuration, and provides real-time cost monitoring with flexible output formats.

**Current Status**: Master branch contains 7 production-ready platforms. Dev branch contains additional platforms under development.

**Configuration System**: Recently refactored to use Python-based configuration management with automatic YAML generation.

## Commands

### Development Commands
```bash
# Install the package in development mode
pip install -e .

# Run the main cost checking command
llm-balance cost

# Check specific platform
llm-balance cost --platform=openai

# Different output formats
llm-balance cost --format=json
llm-balance cost --format=markdown
llm-balance cost --format=table
llm-balance cost --format=total

# Multi-currency support
llm-balance cost --currency=USD      # Show totals in USD
llm-balance cost --currency=EUR      # Show totals in EUR
llm-balance cost --currency=CNY      # Show totals in CNY (default)
llm-balance rates                    # View current exchange rates

# Custom exchange rates
LLM_BALANCE_RATES='{"USD": 7.5}' llm-balance cost

# Platform management
llm-balance list                    # List all platforms
llm-balance enable <platform>       # Enable a platform
llm-balance disable <platform>      # Disable a platform
llm-balance enable all               # Enable all platforms
llm-balance disable all              # Disable all platforms
llm-balance config <platform>        # View platform configuration

# Global browser configuration
llm-balance set-browser chrome       # Set browser for all cookie platforms
llm-balance set-browser firefox      # Set browser for all cookie platforms
llm-balance set-browser arc          # Set browser for all cookie platforms

# Setup and troubleshooting
llm-balance setup_guide              # Show complete setup guide
llm-balance summary                  # Show platform summary
```

### Required Environment Variables
```bash
# API Key authentication platforms
export DEEPSEEK_API_KEY="your_deepseek_api_key"
export ANTHROPIC_API_KEY="your_anthropic_api_key"
export OPENAI_ADMIN_KEY="your_openai_admin_key"
export ALIYUN_ACCESS_KEY_ID="your_aliyun_access_key_id"
export ALIYUN_ACCESS_KEY_SECRET="your_aliyun_access_key_secret"
export MOONSHOT_API_KEY="your_moonshot_api_key"

# Official SDK authentication platforms
export VOLCENGINE_ACCESS_KEY="your_volcengine_access_key"
export VOLCENGINE_SECRET_KEY="your_volcengine_secret_key"

# Additional platforms (API Key authentication)
export GEMINI_API_KEY="your_gemini_api_key"
export AZURE_ACCESS_TOKEN="your_azure_access_token"
export LINGYI_API_KEY="your_lingyi_api_key"
export MINIMAX_API_KEY="your_minimax_api_key"
export TENCENT_API_KEY="your_tencent_api_key"

# Cookie authentication platforms require browser login

# Optional: Custom configuration file path
export LLM_BALANCE_CONFIG_FILE="/path/to/custom/config.yaml"
```

### Development Environment Setup
```bash
# Clone and setup
git clone <repository-url>
cd llm-cost-checker
pip install -r requirements.txt
pip install -e .

# Verify installation
llm-balance --help
llm-balance rates

# Test with environment variables
export DEEPSEEK_API_KEY="your_key"
llm-balance cost --platform=deepseek
```

## Architecture

### Core Components

**BalanceChecker** (`src/llm_balance/balance_checker.py`):
- Main orchestrator that manages platform checking
- Handles errors gracefully and continues with other platforms
- Supports both individual and bulk platform checking
- Delegates formatting to utility functions

**ConfigManager** (`src/llm_balance/config.py`):
- Manages YAML configuration file at `~/.llm_balance/platforms.yaml`
- Handles global browser configuration for all cookie-based platforms
- Handles platform enable/disable states
- Provides configuration validation and updates

**Platform Handlers** (`src/llm_balance/platform_handlers/`):
- Each platform inherits from `BasePlatformHandler`
- Implements `get_balance()` method returning `CostInfo`
- Handles authentication, API calls, and response parsing
- Uses `pycookiecheat` for cookie-based authentication (no hardcoded paths)

**Utility Functions** (`src/llm_balance/utils.py`):
- Multi-currency conversion with `convert_currency()` function
- Flexible output formatting with `format_output()` function
- Exchange rate management with `get_exchange_rates()` function
- Cookie handling using standard `pycookiecheat` library

### Authentication Flow

1. **API Key Authentication**: Direct Bearer token in headers
2. **Cookie Authentication**: Uses `pycookiecheat` to extract browser cookies from globally configured browser
3. **SDK Authentication**: Uses official SDKs for enterprise platforms (Aliyun, Volcengine, Tencent)
4. **Special Services**: Some platforms use custom API endpoints or access tokens

### Factory Pattern
The `create_handler()` function in `platform_handlers/__init__.py` instantiates appropriate handlers based on platform name configuration. This pattern allows easy addition of new platforms without modifying core logic.

### Multi-Currency System

**Currency Conversion** (`src/llm_balance/utils.py`):
- `convert_currency(amount, from_currency, to_currency)` converts between any currencies
- Default exchange rates provided for CNY, USD, EUR, GBP, JPY, KRW, Points
- Custom rates via `LLM_BALANCE_RATES` environment variable
- All conversions go through CNY as intermediate currency

**Exchange Rate Management**:
- Default rates relative to CNY: CNY=1.0, USD=7.2, EUR=7.8, GBP=9.1, JPY=0.048, KRW=0.0054, Points=0.01
- Custom rates override defaults via JSON environment variable
- `get_available_currencies()` returns list of supported currencies
- Unknown currencies default to 1:1 conversion rate

**Output Formatting**:
- Table format shows original currency + converted total in target currency
- Total format shows only the converted total
- JSON and Markdown formats preserve original currency data
- All formats accept `target_currency` parameter

## Platform Integration

### Adding New Platforms

1. **Configuration**: Add platform entry to `~/.llm_balance/platforms.yaml`
2. **Handler**: Create new handler class inheriting from `BasePlatformHandler`
3. **Factory**: Update `create_handler()` function to include new platform
4. **Error Handler**: Add platform information to `error_handler.py` for helpful error messages
5. **Testing**: Verify with `llm-balance cost --platform=<new_platform>`

### Configuration Structure
```yaml
# Global browser configuration for all cookie-based platforms
browser: chrome

platforms:
  platform_name:
    api_url: "https://api.example.com/endpoint"
    method: "GET"  # or POST
    auth_type: "bearer_token"  # cookie, api_key, sdk
    env_var: "API_KEY_ENV_VAR"  # for auth_type: bearer_token/api_key
    cookie_domain: "example.com"  # for auth_type: cookie
    balance_path: ["data", "balance"]  # JSON path to balance value
    currency_path: ["data", "currency"]  # JSON path to currency
    headers: {}  # Additional headers
    params: {}  # Query parameters for GET requests
    data: {}  # Request body for POST requests
    enabled: true
    region: "cn-beijing"  # for SDK-based platforms
```

### Error Handling

- Platform failures don't stop other platforms from being checked
- Timeouts are set to 10 seconds per platform
- Missing environment variables show detailed setup guides
- Network errors are caught and displayed gracefully with troubleshooting steps

## Testing

### Manual Testing
```bash
# Test specific platform
llm-balance cost --platform=deepseek

# Test with different formats
llm-balance cost --format=json
llm-balance cost --format=table
llm-balance cost --format=total

# Test multi-currency functionality
llm-balance cost --currency=USD
llm-balance cost --currency=EUR
llm-balance rates

# Test custom exchange rates
LLM_BALANCE_RATES='{"USD": 7.5}' llm-balance cost --currency=USD

# Verify platform listing
llm-balance list

# Test batch enable/disable
llm-balance enable all
llm-balance disable all
```

### Configuration Testing
```bash
# Test configuration changes
llm-balance config deepseek
llm-balance enable moonshot
llm-balance disable moonshot

# Test global browser configuration
llm-balance set-browser chrome
llm-balance set-browser firefox
llm-balance set-browser arc

# Test per-command browser override
llm-balance cost --browser=chrome
llm-balance cost --browser=firefox
```

### Integration Testing
```bash
# Test all platforms with different currencies
llm-balance cost --currency=USD --format=table
llm-balance cost --currency=EUR --format=total

# Test error handling with invalid platforms
llm-balance cost --platform=nonexistent

# Test backward compatibility
llm-balance check  # Should work as alias for cost
```

## Current Platform Support

### Master Branch (Production-Ready)

#### International Platforms (1)
- **OpenAI**: Admin API authentication via api.openai.com

#### Chinese Platforms (6)
- **DeepSeek**: API Key authentication via api.deepseek.com
- **Moonshot**: API Key authentication via api.moonshot.cn (now redirects to www.kimi.com)
- **Volcengine**: Official SDK authentication via volcengine-python-sdk (recommended) or Cookie authentication (fallback)
- **Aliyun**: Official SDK authentication via aliyun-python-sdk-bssopenapi
- **Tencent**: SDK authentication via Tencent Cloud SDK
- **Zhipu**: Cookie authentication via open.bigmodel.cn

### Dev Branch (Under Development)
Additional platforms available in dev branch:
- **Claude**: API Key authentication
- **Google Gemini**: API Key authentication  
- **Azure OpenAI**: Bearer token authentication
- **Lingyi**: API Key authentication
- **MiniMax**: API Key authentication

## Key Implementation Details

### Request Handling
- GET requests use `params` for query parameters
- POST requests use `json` for request body
- Headers include User-Agent and Accept headers by default
- 10-second timeout per platform request

### Response Processing
- Balance values extracted using JSON path traversal
- Currency detection from response or default to USD
- Raw response data preserved for debugging
- Error handling prevents single platform failure from affecting others

### Security Considerations
- **No hardcoded API keys**: All authentication via environment variables
- **No hardcoded paths**: Uses standard `pycookiecheat` library
- **Local processing**: All data processed locally, no external servers
- **Cookie safety**: Only reads necessary authentication cookies from globally configured browser
- **Environment variables**: Sensitive data managed via environment variables
- **Global browser config**: Simplified browser management for all cookie-based platforms

### Multi-Currency Implementation
- **Conversion algorithm**: All currencies convert via CNY as intermediate
- **Default rates**: CNY=1.0, USD=7.2, EUR=7.8, GBP=9.1, JPY=0.048, KRW=0.0054, Points=0.01
- **Custom rates**: Override via `LLM_BALANCE_RATES` JSON environment variable
- **Output formatting**: Table and total formats show converted totals, JSON/Markdown preserve original data

### Dependencies
- **fire>=0.5.0**: CLI framework
- **requests>=2.31.0**: HTTP requests
- **pycookiecheat>=0.5.0**: Cookie authentication
- **beautifulsoup4>=4.12.0**: HTML parsing
- **PyYAML>=6.0**: Configuration management
- **aliyun-python-sdk-bssopenapi>=2.0.0**: Aliyun SDK
- **volcengine-python-sdk==4.0.13**: Volcengine SDK

### Backward Compatibility
- `llm-balance check` command maintained as alias for `llm-balance cost`
- Existing configuration files remain compatible
- Default currency is CNY (maintains existing behavior)
- No breaking changes in public API

### Code Quality Standards
- **Type hints**: Used throughout the codebase
- **Error handling**: Graceful degradation with clear error messages
- **Modular design**: Clear separation of concerns between components
- **Documentation**: Comprehensive docstrings and comments
- **Testing**: Manual testing procedures documented

###验收情况
- Aliyun,DeepSeek,Moonshot,OpenAI,Tencent,Volcengine,Zhipu 已经通过验收
- 未验收平台已移至dev分支进行开发： Azure OpenAI、Claude、Google Gemini、lingyi、MiniMax。
