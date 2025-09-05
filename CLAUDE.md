# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool for checking costs and balances across multiple LLM platforms. The tool supports multiple authentication methods (API keys, browser cookies, official SDKs), multi-currency conversion, global browser configuration, and provides real-time cost monitoring with flexible output formats.

## Architecture

### Core Components

- **CLI Layer** (`cli.py`): Fire-based CLI interface with commands like `cost`, `tokens`, `list`, `enable`, `disable`
- **BalanceChecker** (`balance_checker.py`): Main orchestrator that manages platform checking and formatting
- **TokenChecker** (`token_checker.py`): Token usage monitoring for supported platforms
- **ConfigManager** (`config.py`): YAML configuration management with global browser settings
- **Platform Handlers** (`platform_handlers/`): Modular platform-specific implementations
- **Utilities** (`utils.py`): Currency conversion, output formatting, and helper functions

### Authentication Methods

1. **API Key**: Bearer token authentication (DeepSeek, Moonshot)
2. **Browser Cookies**: Automatic cookie extraction via pycookiecheat (Zhipu)
3. **Official SDK**: Enterprise SDK integration (Aliyun, Volcengine, Tencent)

### Configuration System

- **Location**: `~/.llm_balance/platforms.yaml`
- **Global Settings**: Single browser configuration for all cookie-based platforms
- **Per-Platform**: Enable/disable, authentication type, API endpoints
- **Dynamic Updates**: Runtime configuration changes via CLI commands

## Development Commands

### Setup & Installation
```bash
# Install in development mode
pip install -e .

# Install dependencies
pip install -r requirements.txt

# Verify installation
llm-balance --help
```

### Automated Testing
```bash
# Run comprehensive tests
python test_llm_balance.py

# Run with verbose output
python test_llm_balance.py --verbose

# Test specific platforms only
python test_llm_balance.py --platforms deepseek volcengine

# Generate JSON report for analysis
python test_llm_balance.py --json-report

# Fast fail on first error
python test_llm_balance.py --fail-fast
```

### Testing Commands
```bash
# Check all platforms
llm-balance cost

# Check specific platform
llm-balance cost --platform=deepseek

# Different output formats
llm-balance cost --format=json
llm-balance cost --format=table
llm-balance cost --format=total

# Token usage monitoring
llm-balance package
llm-balance package --platform=volcengine
llm-balance package --platform=zhipu --model=glm-4

# Package table output shows Total/Used/Remaining summary
# The table format includes detailed model information with totals at the bottom
llm-balance package --format=table

# Multi-currency testing
llm-balance cost --currency=USD
llm-balance rates

# Platform management
llm-balance list
llm-balance enable moonshot
llm-balance disable tencent
```

### Environment Variables
```bash
# API Key platforms
export DEEPSEEK_API_KEY="your_key"
export MOONSHOT_API_KEY="your_key"
export SILICONFLOW_API_KEY="your_key"

# SDK platforms
export VOLCENGINE_ACCESS_KEY="your_key"
export VOLCENGINE_SECRET_KEY="your_key"
export ALIYUN_ACCESS_KEY_ID="your_key"
export ALIYUN_ACCESS_KEY_SECRET="your_key"
export TENCENT_API_KEY="your_key"

# Custom configuration
export LLM_BALANCE_CONFIG_FILE="/path/to/config.yaml"
export LLM_BALANCE_RATES='{"USD": 7.5}'
```

### Dependencies & SDK Installation

The project requires specific SDK installations for certain platforms:
```bash
# Base dependencies (always required)
pip install -r requirements.txt

# Optional platform-specific SDKs
pip install aliyun-python-sdk-bssopenapi>=2.0.0  # Aliyun billing
pip install volcengine-python-sdk==4.0.13        # Volcengine
pip install tencentcloud-sdk-python>=3.0.0      # Tencent Cloud
```

Note: Some SDKs are included in requirements.txt, others may need manual installation based on platform requirements.

### Important Development Notes

#### Recent Bug Fixes
- **Volcengine Package API**: Fixed `ListResourcePackages` parameter format (requires string `"20"` not integer `100`)
- **ModelTokenInfo Constructor**: Updated parameter names to match current data structure
- **Cost Total Type Error**: Fixed int/str type mismatch in spent calculation
- **JSON Serialization**: Added cleanup for non-serializable Configuration objects

#### Testing Framework
The automated test script (`test_llm_balance.py`) provides comprehensive testing:
- **16 test cases** covering all platforms and output formats
- **Environment validation** and dependency checking
- **Detailed reporting** with JSON export capability
- **Platform-specific testing** for isolated debugging

#### Known Issues
- Some platforms return `"-"` for spent values when tracking is not supported
- Volcengine SDK requires specific parameter formatting (strings vs integers)
- Configuration objects may need JSON serialization cleanup

## Key Files & Patterns

### Adding New Platforms

1. **Create Handler**: Inherit from `BasePlatformHandler` in `platform_handlers/`
2. **Register**: Add to `create_handler()` function in `platform_handlers/__init__.py`
3. **Configure**: Add platform configuration to `platform_configs.py`
4. **Test**: Use `llm-balance cost --platform=new_platform`

### Platform Handler Structure

Each handler implements:
- `get_balance()`: Returns `CostInfo` with balance, currency, raw data
- `get_platform_name()`: Returns display name
- `get_model_tokens()`: Optional method for token usage monitoring
- Authentication logic specific to platform type

### Spent Tracking Implementation

Platforms that support spent tracking should implement one of these approaches:
- **Direct API**: Use platform's billing/spent API (preferred)
- **Transaction History**: Query transaction records and sum expenses (Aliyun approach)
- **Invoice/Recharge**: Calculate as "total_recharge - current_balance" (if recharge API available)

For unsupported platforms, return `"-"` as spent value to distinguish from zero spending.

### Data Class Structures

Key data classes in `base.py`:
- `CostInfo`: Contains balance, spent, currency, and raw API response data
- `ModelTokenInfo`: Contains token usage data for specific models
- `PlatformTokenInfo`: Contains model token info for entire platform

### Output Formats

- **JSON**: Machine-readable with raw data
- **Table**: Console-friendly with totals
- **Markdown**: Document-friendly
- **Total**: Single currency total only

### Currency System

- **Default Rates**: CNY-based with USD=7.2, EUR=7.8, etc.
- **Custom Rates**: Via `LLM_BALANCE_RATES` environment variable
- **Conversion**: All currencies convert through CNY as intermediate

## Common Development Tasks

### Debug Platform Issues
```bash
# Test individual platform
llm-balance cost --platform=deepseek --format=json

# Check configuration
llm-balance config deepseek

# Diagnose system
llm-balance diagnose

# Test specific authentication method
llm-balance config volcengine auth_type sdk
llm-balance config volcengine auth_type cookie
```

### Browser Configuration
```bash
# Set global browser
llm-balance set-browser chrome

# Override for single command
llm-balance cost --browser=firefox

# Test cookie-based platforms (Zhipu)
llm-balance cost --platform=zhipu --browser=chrome
```

### Configuration Management
```bash
# Generate fresh config
llm-balance generate_config

# View/edit platform config
llm-balance config volcengine auth_type sdk

# Enable/disable platforms
llm-balance enable moonshot
llm-balance disable tencent
```

### Development Workflow
```bash
# Install in development mode
pip install -e .

# Run specific platform tests
python -c "from llm_balance.platform_handlers.deepseek import DeepSeekHandler; print(DeepSeekHandler.get_default_config())"

# Test configuration loading
python -c "from llm_balance.config import ConfigManager; cm = ConfigManager(); print([p.name for p in cm.get_enabled_platforms()])"
```

## Technical Implementation Details

### Authentication Flow

1. **API Key Authentication**: Direct HTTP requests with Authorization headers
2. **SDK Authentication**: Use platform-specific SDKs (Aliyun, Volcengine, Tencent)
3. **Cookie Authentication**: Extract cookies from browser using pycookiecheat (Zhipu)

### Error Handling

- Platform failures don't stop other platforms from being checked
- Each handler implements its own error handling and returns appropriate error messages
- Configuration errors are caught and displayed with helpful guidance

### Configuration Architecture

- **Platform Configs**: Defined in `platform_configs.py` with default settings
- **User Configs**: Stored in `~/.llm_balance/platforms.yaml` for user overrides
- **Runtime Configs**: Merged configuration with environment variable support

### Output Formatting

- **Table Format**: Clean console output with proper alignment and totals
- **JSON Format**: Machine-readable with full raw API responses
- **Markdown Format**: Documentation-friendly with proper formatting
- **Total Format**: Single-line summary for scripting

### Special Considerations

- **Spent Tracking**: Some platforms don't support spent queries - return "-" instead of 0
- **Currency Conversion**: All amounts converted through CNY as intermediate currency
- **Time Zones**: Transaction queries use proper date alignment to avoid duplicates
- **Browser Dependencies**: Cookie authentication requires browser login and proper cookie extraction

### Testing Architecture

The test suite (`test_llm_balance.py`) follows a comprehensive approach:
- **Environment Validation**: Checks CLI availability and required environment variables
- **Multi-Format Testing**: Validates table, JSON, total, and markdown output formats
- **Platform Coverage**: Tests all 7 platforms individually and collectively
- **Error Handling**: Gracefully handles platform failures and provides detailed error reporting
- **Performance Tracking**: Measures execution time for each test case
- **Report Generation**: Creates detailed JSON reports for analysis and debugging

#### Test Structure
- **Cost Command Tests**: Validate balance checking across all formats
- **Package Command Tests**: Verify token usage monitoring functionality
- **Platform-Specific Tests**: Isolate individual platform issues
- **Integration Tests**: Ensure overall system reliability
