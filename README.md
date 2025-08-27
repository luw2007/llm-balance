# LLM Balance Checker

A Python CLI tool for checking balance and usage across multiple LLM platforms. Supports multiple authentication methods, multi-currency conversion, global browser configuration, and provides real-time balance monitoring with flexible output formats.

## Features

- 🔑 **Multiple Authentication**: API Key, browser cookie, official SDK, and proxy service authentication
- 🌐 **Multi-Platform Support**: Integrated with 7 major LLM platforms (production-ready)
- 📊 **Multiple Output Formats**: JSON, Markdown, table, total-only
- 💱 **Multi-Currency Support**: Support for CNY, USD, EUR and more
- 🌍 **Global Browser Configuration**: Single browser setting for all cookie-based platforms
- ⚙️ **Flexible Configuration**: YAML configuration file with dynamic enable/disable
- 🔧 **Easy to Extend**: Modular design for easy platform addition
- 💰 **Real-time Monitoring**: Unified balance and usage query interface
- 🛡️ **Error Tolerance**: Single platform failure doesn't affect others
- 🏢 **Enterprise Ready**: Official SDK support for automated deployment

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd llm-cost-checker

# Install dependencies (includes Volcengine SDK)
pip install -r requirements.txt

# Install CLI tool
pip install -e .

# Verify installation
llm-balance --help
llm-balance rates
```

### Environment Variables

Configure environment variables based on the platforms you use:

```bash
# API Key authentication platforms
export DEEPSEEK_API_KEY="your_deepseek_api_key"
export OPENAI_ADMIN_KEY="your_openai_admin_key"
export MOONSHOT_API_KEY="your_moonshot_api_key"

# Official SDK authentication platforms
export VOLCENGINE_ACCESS_KEY="your_volcengine_access_key"
export VOLCENGINE_SECRET_KEY="your_volcengine_secret_key"
export ALIYUN_ACCESS_KEY_ID="your_aliyun_access_key_id"
export ALIYUN_ACCESS_KEY_SECRET="your_aliyun_access_key_secret"

# Chinese platforms (API Key authentication)
export TENCENT_API_KEY="your_tencent_api_key"

# Cookie authentication platforms (require browser login)
# Zhipu requires login to https://open.bigmodel.cn
```

## Usage

### Basic Commands

```bash
# Check all platform balance
llm-balance cost

# Check specific platform
llm-balance cost --platform=openai

# Check multiple platforms (comma-separated)
llm-balance cost --platform=volcengine,aliyun
llm-balance cost --platform="deepseek, moonshot, tencent"

# Specify browser (for cookie authentication)
llm-balance cost --browser=chrome

# Set global browser for all cookie-based platforms
llm-balance set-browser chrome

# Different output formats
llm-balance cost --format=json      # Machine-readable format
llm-balance cost --format=markdown  # Document-friendly format
llm-balance cost --format=table     # Console table format
llm-balance cost --format=total     # Show total only

# Specify currency
llm-balance cost --currency=USD     # Show total in USD
llm-balance cost --currency=EUR     # Show total in EUR
llm-balance cost --currency=CNY     # Show total in CNY (default)
```

> 💡 Backward compatibility: `llm-balance check` command is still available as an alias for `llm-balance cost`

### Platform Management

```bash
# List all platforms and their status
llm-balance list

# Enable platform
llm-balance enable moonshot

# Disable platform
llm-balance disable moonshot

# Switch authentication method (SDK vs Cookie)
llm-balance config volcengine auth_type sdk    # Use official SDK
llm-balance config volcengine auth_type cookie  # Use browser cookies
```

### Configuration Management

```bash
# View complete platform configuration
llm-balance config deepseek

# View specific configuration item
llm-balance config deepseek api_url

# Set configuration item (supports automatic type conversion)
llm-balance config deepseek enabled true
llm-balance config deepseek timeout 30
```

### Advanced Usage Examples

```bash
# View total balance in USD for all platforms
llm-balance cost --currency=USD --format=total

# Get detailed EUR balance for specific platform
llm-balance cost --platform=deepseek --currency=EUR --format=table

# Check multiple platforms at once
llm-balance cost --platform=volcengine,aliyun,deepseek --format=table
llm-balance cost --platform="openai, deepseek, moonshot" --currency=USD --format=total

# Use custom exchange rates and output as JSON
LLM_BALANCE_RATES='{"USD": 7.5}' llm-balance cost --currency=USD --format=json

# Combine multiple parameters
llm-balance cost --platform=openai --browser=chrome --currency=GBP --format=markdown

# Test Volcengine SDK authentication
export VOLCENGINE_ACCESS_KEY="your_access_key"
export VOLCENGINE_SECRET_KEY="your_secret_key"
llm-balance cost --platform=volcengine --format=table

# Test Chinese platforms
export TENCENT_API_KEY="your_tencent_api_key"
llm-balance cost --platform=tencent --format=table

# Test cookie authentication platforms
# Zhipu requires login to open.bigmodel.cn
llm-balance cost --platform=zhipu --browser=chrome
```

## Exchange Rate Features

### Overview

Supports automatic exchange rate conversion to convert balances in different currencies to a target currency for total calculation. Supports multiple currency types including CNY, USD, EUR, etc.

### Default Exchange Rates

System includes following default rates (relative to CNY):
- CNY: 1.0
- USD: 7.2
- EUR: 7.8
- GBP: 9.1
- JPY: 0.048
- KRW: 0.0054
- Points: 0.01

### Viewing and Managing Exchange Rates

```bash
# View current exchange rates
llm-balance rates

# Custom exchange rates (session level)
LLM_BALANCE_RATES='{"USD": 7.5}' llm-balance cost

# Set multiple exchange rates
LLM_BALANCE_RATES='{"USD": 7.5, "EUR": 8.0}' llm-balance cost
```

### Currency Conversion Rules

- **Flexible Conversion**: Supports conversion between any currencies
- **Total Display**: Table and total formats show totals in specified currency
- **Original Data**: JSON and Markdown formats preserve original currency display
- **Default Currency**: Uses CNY as default output currency
- **Custom Rates**: Set via `LLM_BALANCE_RATES` environment variable

### Supported Currencies

- CNY (Chinese Yuan)
- USD (US Dollar)
- EUR (Euro)
- GBP (British Pound)
- JPY (Japanese Yen)
- KRW (Korean Won)
- Points (Points)

## Configuration File

Configuration file is located at `~/.llm_balance/platforms.yaml`, automatically created on first run:

```yaml
# Global browser configuration for all cookie-based platforms
browser: chrome

platforms:
  deepseek:
    api_url: "https://api.deepseek.com/user/balance"
    method: "GET"
    auth_type: "bearer_token"
    env_var: "DEEPSEEK_API_KEY"
    balance_path: ["balance_infos", "0", "total_balance"]
    currency_path: ["balance_infos", "0", "currency"]
    enabled: true
    headers:
      User-Agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
      Accept: "application/json"
  
  openai:
    api_url: "https://api.openai.com/v1/organization/costs"
    method: "GET"
    auth_type: "bearer_token"
    env_var: "OPENAI_ADMIN_KEY"
    balance_path: ["data", "0", "results", "0", "amount", "value"]
    currency_path: ["data", "0", "results", "0", "amount", "currency"]
    enabled: true
    params:
      start_time: 1730419200
      limit: 1
```

## Supported Platforms

### 🌍 International Platforms (0)

| Platform | Authentication | Status | Description |
|----------|----------------|--------|-------------|
| **OpenAI** | Admin API | ❌ | Currently not supported for balance queries |

### 🇨🇳 Chinese Platforms (6)

| Platform | Authentication | Status | Description |
|----------|----------------|--------|-------------|
| **DeepSeek** | API Key | ✅ | Requires DEEPSEEK_API_KEY |
| **Moonshot** | API Key | ✅ | Requires MOONSHOT_API_KEY |
| **Volcengine** | SDK/Cookie | ✅ | Requires VOLCENGINE_ACCESS_KEY + SECRET_KEY or browser login |
| **Aliyun** | Official SDK | ✅ | Requires ALIYUN_ACCESS_KEY_ID + SECRET_KEY |
| **Tencent** | SDK | ✅ | Requires TENCENT_API_KEY (SecretId:SecretKey) |
| **Zhipu** | Cookie | ✅ | Requires login to https://open.bigmodel.cn |

### 📊 Platform Status Summary

**Production-Ready (6 platforms)**: All platforms listed above are fully tested and ready for production use.

**Development Status**: Additional platforms (Claude, Google Gemini, Azure OpenAI, Lingyi, MiniMax) are available in the `dev` branch and under active development.

### Authentication Methods

#### 🔑 API Key Authentication
For platforms providing API interfaces:
```bash
# DeepSeek
export DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"

# OpenAI (currently not supported for balance queries)
# export OPENAI_ADMIN_KEY="sk-admin-xxxxxxxxxxxxxxxxxxxxxxxx"

# Aliyun (requires both access key ID and secret)
export ALIYUN_ACCESS_KEY_ID="your_access_key_id"
export ALIYUN_ACCESS_KEY_SECRET="your_access_key_secret"

# Moonshot
export MOONSHOT_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
```

#### 🍪 Cookie Authentication
For platforms requiring browser sessions:
1. Login to the corresponding platform website
2. Tool automatically retrieves authentication cookies from browser
3. Supports Chrome, Firefox, Arc, Brave and other mainstream browsers

#### 🌐 Special Services
Some platforms use special access methods:
- Zhipu uses cookie authentication via browser login
- Requires login to https://open.bigmodel.cn

## Browser Support

### 🌍 Global Browser Configuration
All cookie-based platforms use a single global browser configuration:

```bash
# Set global browser (affects all cookie platforms)
llm-balance set-browser chrome
llm-balance set-browser firefox
llm-balance set-browser arc
```

### 🍪 Supported Browsers
- **Chrome** (Recommended)
- **Firefox**
- **Arc** 
- **Brave**
- **Chromium**

### 🔧 Troubleshooting

#### Common Issues

**Q: Cookie Authentication Failed**
```bash
# Ensure you're logged in to the corresponding platform
# Check global browser setting
llm-balance set-browser chrome
# Or override for single command
llm-balance cost --browser=chrome
```

**Q: Invalid API Key**
```bash
# Check if environment variables are set
echo $DEEPSEEK_API_KEY
echo $OPENAI_ADMIN_KEY

# Reset environment variables
export DEEPSEEK_API_KEY="your_valid_api_key"
```

**Q: Specific Platform Timeout**
```bash
# Test problematic platform individually
llm-balance cost --platform=deepseek

# Check network connection
curl -I https://api.deepseek.com
```

#### Configuration File Locations
- Main configuration: `~/.llm_balance/platforms.yaml`
- Customizable via `LLM_BALANCE_CONFIG_FILE` environment variable

## Security Notes

- 🔒 **Local Processing**: All authentication information is processed locally, not uploaded to external servers
- 🍪 **Cookie Reading**: Only reads necessary authentication cookies from browser, doesn't get other sensitive information
- 🛡️ **Environment Variables**: API keys managed via environment variables, not written to configuration files
- 🔄 **Session Nature**: Cookie authentication has时效性, requires regular platform re-login

## Development Guide

### Project Structure

```
src/llm_balance/
├── __init__.py              # Package info and version
├── cli.py                  # CLI command interface
├── balance_checker.py      # Main business logic
├── config.py              # Configuration file management
├── error_handler.py       # Error handling
├── utils.py               # Utility functions
└── platform_handlers/     # Platform handlers
    ├── __init__.py         # Handler factory
    ├── base.py            # Base handler class
    ├── aliyun.py          # Aliyun handler ✅
    ├── deepseek.py        # DeepSeek handler ✅
    ├── openai.py          # OpenAI handler ✅
    ├── moonshot.py        # Moonshot handler ✅
    ├── volcengine.py      # Volcengine handler ✅
    ├── tencent.py         # Tencent handler ✅
    ├── zhipu.py           # Zhipu handler ✅
    └── generic.py         # Generic handler
```

**Note**: Additional platform handlers (Claude, Gemini, Azure OpenAI, Lingyi, MiniMax) are available in the `dev` branch.

### Adding New Platforms

1. **Configure Platform**: Add new platform configuration in `~/.llm_balance/platforms.yaml`
2. **Create Handler**: Inherit from `BasePlatformHandler` class, implement necessary authentication and parsing logic
3. **Register Handler**: Add new platform in `create_handler` function in `platform_handlers/__init__.py`
4. **Test Verification**: Test with `llm-balance cost --platform=<new_platform>`

### Development Environment

```bash
# Install development dependencies
pip install -e .

# Run tests
llm-balance cost --format=json

# Debug specific platform
llm-balance cost --platform=deepseek --browser=chrome
```

## Contributing

Issues and Pull Requests are welcome!

1. Fork this repository
2. Create feature branch (`git checkout -b feature/new-platform`)
3. Commit changes (`git commit -am 'Add new platform support'`)
4. Push to branch (`git push origin feature/new-platform`)
5. Create Pull Request

## License

MIT License - See [LICENSE](LICENSE) file for details