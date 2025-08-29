# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool for checking costs and balances across multiple LLM platforms. The tool supports multiple authentication methods (API keys, browser cookies, official SDKs), multi-currency conversion, global browser configuration, and provides real-time cost monitoring with flexible output formats.

## Architecture

### Core Components

- **CLI Layer** (`cli.py`): Fire-based CLI interface with commands like `cost`, `list`, `enable`, `disable`
- **BalanceChecker** (`balance_checker.py`): Main orchestrator that manages platform checking and formatting
- **ConfigManager** (`config.py`): YAML configuration management with global browser settings
- **Platform Handlers** (`platform_handlers/`): Modular platform-specific implementations
- **Utilities** (`utils.py`): Currency conversion, output formatting, and helper functions

### Authentication Methods

1. **API Key**: Bearer token authentication (DeepSeek, Moonshot, OpenAI)
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

# Multi-currency testing
llm-balance cost --currency=USD
llm-balance rates

# Platform management
llm-balance list
llm-balance enable moonshot
llm-balance disable tencent

# Package commands (only for supported platforms)
llm-balance package
llm-balance package --model=doubao
llm-balance package --format=json
```

### Environment Variables
```bash
# API Key platforms
export DEEPSEEK_API_KEY="your_key"
export MOONSHOT_API_KEY="your_key"
export OPENAI_ADMIN_KEY="your_key"

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
- Authentication logic specific to platform type

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
```

### Browser Configuration
```bash
# Set global browser
llm-balance set-browser chrome

# Override for single command
llm-balance cost --browser=firefox
```

### Configuration Management
```bash
# Generate fresh config
llm-balance generate_config

# View/edit platform config
llm-balance config volcengine auth_type sdk
```