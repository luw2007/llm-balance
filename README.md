# LLM Balance Checker

**A unified CLI tool for monitoring costs and usage across multiple LLM platforms**

## Key Features

- **🔑 Multiple Authentication**: API Key, browser cookie, official SDK support
- **🌐 14 Platforms Supported**: DeepSeek, Moonshot, Volcengine, Aliyun, Tencent, Zhipu, SiliconFlow, OpenAI, Anthropic, Google (+ third-party relays: FoxCode, DuckCoding, 88Code, YouAPI)
- **💰 Real-time Balance & Spent**: Track both current balance and actual spending
- **📊 Flexible Output**: Table, JSON, Markdown, and total-only formats
- **💱 Multi-Currency**: Automatic conversion between CNY, USD, EUR, and more
- **🎯 Token Monitoring**: Detailed token usage for supported platforms
- **🛡️ Fault Tolerant**: Single platform failures won't break the entire tool
- **⚙️ Easy Configuration**: Simple setup with environment variables
- **🔒 Independent Configuration**: Special platforms use separate config files to avoid global pollution

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd llm_balance

# Install dependencies (includes Volcengine SDK)
pip install -r requirements.txt

# Install CLI tool
pip install -e .

# Verify installation
llm-balance --help
llm-balance rates
```

### Platform Setup

Choose the platforms you want to use and configure their authentication:

#### API Key Platforms (Quick Setup)
```bash
# DeepSeek (API Key)
export DEEPSEEK_API_KEY="sk-your-deepseek-api-key"

# Moonshot (API Key)
export MOONSHOT_API_KEY="sk-your-moonshot-api-key"

# SiliconFlow (API Key)
export SILICONFLOW_API_KEY="your-siliconflow-api-key"
```

#### SDK Platforms (Enterprise Setup)
```bash
# Volcengine (Official SDK)
export VOLCENGINE_ACCESS_KEY="your-volcengine-access-key"
export VOLCENGINE_SECRET_KEY="your-volcengine-secret-key"

# Aliyun (Official SDK)
export ALIYUN_ACCESS_KEY_ID="your-aliyun-access-key-id"
export ALIYUN_ACCESS_KEY_SECRET="your-aliyun-access-key-secret"

# Tencent Cloud (SDK)
export TENCENT_API_KEY="your-tencent-secret-id:your-tencent-secret-key"
```

#### Browser-based Platforms
```bash
# Zhipu AI (Requires browser login)
# 1. Login to https://open.bigmodel.cn
# 2. Set global browser for cookie extraction
llm-balance set-browser chrome
# Or override per command: llm-balance cost --browser=chrome
```

#### Special Platforms with Independent Configuration
```bash
# DuckCoding (Requires independent configuration)
# Method 1: Environment variable
export DUCKCODING_API_USER_ID="your_user_id"

# Method 2: Separate config file
llm-balance platform_config duckcoding api_user_id your_user_id

# Method 3: Manual config file creation
cat > ~/.llm_balance/duckcoding_config.yaml << EOF
api_user_id: your_user_id
EOF

# Then login to https://duckcoding.com and run:
llm-balance cost --platform=duckcoding
```

### First Use

```bash
# Test a single platform (choose one you configured)
llm-balance cost --platform=deepseek

# Check all configured platforms
llm-balance cost

# View results in different formats
llm-balance cost --format=table    # Clean console output
llm-balance cost --format=json     # Machine-readable
llm-balance cost --format=total    # Just the totals
```

### Quick Troubleshooting

If you encounter issues, try these steps:

```bash
# Check if environment variables are set
echo $DEEPSEEK_API_KEY
echo $VOLCENGINE_ACCESS_KEY

# Test individual platform with debug output
llm-balance cost --platform=deepseek --format=json

# Verify configuration
llm-balance list

# Check browser setting for cookie-based platforms
llm-balance set-browser chrome

# Test network connectivity
curl -I https://api.deepseek.com
```

**Common Issues:**
- **API Key not found**: Make sure environment variables are set correctly
- **Browser authentication failed**: Ensure you're logged into the platform website
- **Permission denied**: Check API key permissions and account status
- **Network timeout**: Verify internet connection and platform API status

## Usage

### Essential Commands

#### Balance & Spent Monitoring
```bash
# Check all configured platforms
llm-balance cost

# Check specific platform
llm-balance cost --platform=deepseek

# Multiple platforms (comma-separated)
llm-balance cost --platform=volcengine,aliyun

# Browser override for cookie-based platforms
llm-balance cost --platform=zhipu --browser=chrome

# Output formats
llm-balance cost --format=table     # Clean console view (default)
llm-balance cost --format=json      # Machine-readable
llm-balance cost --format=total     # Just the totals

# Currency conversion
llm-balance cost --currency=USD     # Convert to USD
llm-balance cost --currency=EUR     # Convert to EUR
```

> 💡 **New Feature**: The cost command now displays both current balance and spent amount for all platforms, providing a complete financial overview of your LLM usage.

#### Token Usage Monitoring
```bash
# Check token usage for supported platforms
llm-balance package

# Specific platform and model
llm-balance package --platform=volcengine --model=deepseek-r1

# Multiple platforms
llm-balance package --platform=volcengine,zhipu

# Different output formats
llm-balance package --format=table   # Console view
llm-balance package --format=json    # Machine-readable
```

> **Note**: Token monitoring is available for Volcengine and Zhipu platforms only
> Plus, FoxCode relay exposes package/quotas via dashboard (see below).

#### Quick Reference
| Command | Purpose | Example |
|---------|---------|---------|
| `llm-balance cost` | Check balance & spent | `llm-balance cost --platform=volcengine` |
| `llm-balance package` | Check token usage | `llm-balance package --platform=zhipu` |
| `llm-balance list` | List platforms | `llm-balance list` |
| `llm-balance enable` | Enable platform | `llm-balance enable deepseek` |
| `llm-balance disable` | Disable platform | `llm-balance disable tencent` |

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

# Independent configuration for special platforms
llm-balance platform_config duckcoding         # View DuckCoding config
llm-balance platform_config duckcoding api_user_id 10801  # Set user ID
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

#### Balance Checking
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

#### Token Usage Monitoring
```bash
# Check token usage across all supported platforms
llm-balance package

# Check token usage for specific model on Volcengine
llm-balance package --platform=volcengine --model=deepseek-r1

# Check token usage for Zhipu AI with specific model
llm-balance package --platform=zhipu --model=glm-4-plus

# Compare token usage across multiple platforms
llm-balance package --platform=volcengine,zhipu --format=table

# Get detailed JSON output for token usage
llm-balance package --platform=volcengine --format=json

# Filter models by partial name matching
llm-balance package --platform=volcengine --model=deepseek
llm-balance package --platform=zhipu --model=glm-4

# Check token usage in different currencies
llm-balance package --currency=USD --format=table
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

### 🌍 International Platforms (3)

| Platform | Authentication | Status | Description | Token Usage | Spent Tracking |
|----------|----------------|--------|-------------|-------------|---------------|
| **OpenAI** | Admin API | ✅ | Requires OPENAI_ADMIN_KEY | ❌ Not Available | ✅ Full Support |
| **Anthropic** | Admin API | ✅ | Requires ANTHROPIC_ADMIN_KEY | ❌ Not Available | ✅ Full Support |
| **Google** | API Key | ✅ | Requires GOOGLE_API_KEY | ❌ Not Available | ✅ Full Support |

### 🇨🇳 Chinese Platforms (7)

| Platform | Authentication | Status | Description | Token Usage | Spent Tracking |
|----------|----------------|--------|-------------|-------------|---------------|
| **DeepSeek** | API Key | ✅ | Requires DEEPSEEK_API_KEY | ❌ Not Available | ❌ Not Supported |
| **Moonshot** | API Key | ✅ | Requires MOONSHOT_API_KEY | ❌ Not Available | ❌ Not Supported |
| **Volcengine** | SDK/Cookie | ✅ | Requires VOLCENGINE_ACCESS_KEY + SECRET_KEY or browser login | ✅ Full Support | ✅ Full Support |
| **Aliyun** | Official SDK | ✅ | Requires ALIYUN_ACCESS_KEY_ID + SECRET_KEY | ❌ Not Available | ✅ Full Support |
| **Tencent** | SDK | ✅ | Requires TENCENT_API_KEY (SecretId:SecretKey) | ❌ Not Available | ✅ Available |
| **Zhipu** | Cookie | ✅ | Requires login to https://open.bigmodel.cn | ✅ Full Support | ✅ Full Support |
| **SiliconFlow** | API Key | ✅ | Requires SILICONFLOW_API_KEY | ❌ Not Available | ✅ Full Support |

### 🔄 Third-Party Relay Platforms (4)

| Platform | Authentication | Status | Description | Token Usage | Spent Tracking | Independent Config |
|----------|----------------|--------|-------------|-------------|---------------|-------------------|
| **FoxCode** | Cookie | ✅ | Relay service with dashboard access | ✅ Full Support | ✅ Full Support | ❌ No |
| **DuckCoding** | Cookie | ✅ | Relay service with token packages | ✅ Full Support | ✅ Full Support | ✅ Yes |
| **88Code** | Console Token | ✅ | Relay service with subscription packages | ✅ Full Support | ✅ Full Support | ✅ Yes |
| **YouAPI** | Cookie | ✅ | Relay service with quota system | ✅ Full Support | ✅ Full Support | ✅ Yes |

### 📊 Platform Status Summary

**Production-Ready (14 platforms)**: All platforms listed above are fully tested and ready for production use.

**Independent Configuration**: DuckCoding, 88Code, and YouAPI use separate configuration files to avoid polluting global settings.

**Development Status**: Additional platforms (Azure OpenAI, Lingyi, MiniMax) are available in the `dev` branch and under active development.

### Token Usage Support

Some platforms provide token usage monitoring capabilities:

| Platform | Token Usage Support | Models Available |
|----------|-------------------|------------------|
| **Volcengine** | ✅ Full Support | deepseek-r1, deepseek-v3, doubao-pro-32k, doubao-pro-128k, etc. |
| **Zhipu AI** | ✅ Full Support | glm-4-plus, glm-4, glm-3-turbo, cogview-3, etc. |
| **DeepSeek** | ❌ Not Available | - |
| **Moonshot** | ❌ Not Available | - |
| **Aliyun** | ❌ Not Available | - |
| **Tencent** | ❌ Not Available | - |
| **SiliconFlow** | ❌ Not Available | - |

### Spent Amount Tracking

Real-time spent amount tracking across supported platforms:

| Platform | Spent Tracking | Data Source | Accuracy |
|----------|---------------|-------------|----------|
| **Volcengine** | ✅ Full Support | Official API | High |
| **Aliyun** | ✅ Full Support | BSS Transaction API | High |
| **Zhipu AI** | ✅ Full Support | Billing API | High |
| **Tencent Cloud** | ✅ Available | Billing API | Medium |
| **SiliconFlow** | ✅ Full Support | Billing API | High |
| **DeepSeek** | ❌ Not Supported | N/A | N/A |
| **Moonshot** | ❌ Not Supported | N/A | N/A |

> **Note**: Platforms marked as "Not Supported" for spent tracking will display "-" instead of a numeric value to clearly distinguish between unsupported functionality and zero spending.

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

# SiliconFlow
export SILICONFLOW_API_KEY="your_siliconflow_api_key"
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

### Third-Party Relay: FoxCode

FoxCode is a cookie-authenticated relay with dashboard-based package and cost information.

- Auth: Browser cookie on `foxcode.rjj.cc`. Read `auth_token` and query `https://foxcode.rjj.cc/api/user/dashboard` with `Authorization: Bearer <token>`.
- package: Uses `data.subscription.active` entries.
  - Total = plan `quotaLimit`
  - Remaining = `quotaRemaining` (fallback to plan `duration`)
  - Used = Total - Remaining
  - Package column shows `plan.name`
- cost: Balance is shown as `-` (no top-up on this relay); Spent = sum of `data.subscription.history[*].plan.price` in CNY.

Examples:
```bash
llm-balance package --platform=foxcode
llm-balance cost --platform=foxcode
# Specify browser if needed
llm-balance package --platform=foxcode --browser=chrome
llm-balance cost --platform=foxcode --browser=chrome
```

### Third-Party Relay: DuckCoding

DuckCoding is a cookie-authenticated relay with token-based package and cost information, using independent configuration.

- Auth: Browser cookie on `duckcoding.com`. Query `https://duckcoding.com/api/user/self` with `new-api-user` header.
- Configuration: Requires `api_user_id` setting via environment variable or separate config file.
- package: Uses `data.quota` and `data.used_quota` from user info.
  - Total = `quota` (in tokens)
  - Used = `used_quota` (in tokens)
  - Remaining = Total - Used
  - Package column shows "DuckCoding 按量计费(不到期)"
- cost: Balance and spent calculated from quota data.
  - Balance = `quota / 500000` (in CNY)
  - Spent = `used_quota / 500000` (in CNY)

Configuration Options:
```bash
# Method 1: Environment variable
export DUCKCODING_API_USER_ID="10801"

# Method 2: CLI command
llm-balance platform_config duckcoding api_user_id 10801

# Method 3: Manual config file
cat > ~/.llm_balance/duckcoding_config.yaml << EOF
api_user_id: 10801
EOF
```

Examples:
```bash
# Check balance and spent
llm-balance cost --platform=duckcoding
# Check token usage
llm-balance package --platform=duckcoding
# View configuration
llm-balance platform_config duckcoding
# Configure user ID
llm-balance platform_config duckcoding api_user_id 10801
```

### Third-Party Relay: 88Code

88Code is a console token-authenticated relay with subscription-based packages and cost information.

- Auth: Console token via environment variable or separate config file.
- Configuration: Requires `console_token` setting.
- package: Uses subscription data from `https://www.88code.org/admin-api/cc-admin/system/subscription/my`.
  - Total = sum of all subscription costs (active + inactive)
  - Balance = calculated based on usage ratio of active subscriptions
  - Spent = Total cost - Balance
  - Package column shows subscription features with status display
- Status: Shows "active" or "inactive" based on subscription `isActive` flag

Configuration Options:
```bash
# Method 1: Environment variable
export CODE88_CONSOLE_TOKEN="your_console_token"

# Method 2: Manual config file
cat > ~/.llm_balance/88code_config.yaml << EOF
console_token: your_console_token
EOF
```

Examples:
```bash
# Check balance and spent
llm-balance cost --platform=88code
# Check token usage with status display
llm-balance package --platform=88code
```

### Third-Party Relay: YouAPI

YouAPI is a cookie-authenticated relay with simple quota-based balance and spent calculation.

- Auth: Browser cookie on `yourapi.cn` with `new-api-user` header.
- Configuration: Requires `new_api_user` setting via environment variable or separate config file.
- package: Uses quota data from `https://yourapi.cn/api/user/self`.
  - Total = `quota` (in tokens, converted to CNY by dividing by 500000)
  - Used = `used_quota` (in tokens, converted to CNY by dividing by 500000)
  - Remaining = Total - Used
  - Package column shows user group information
  - Status: Shows "active" or "inactive" based on user status
- cost: Balance and spent calculated from quota data with currency conversion.

Configuration Options:
```bash
# Method 1: Environment variable
export YOUAPI_NEW_API_USER="5942"

# Method 2: Manual config file
cat > ~/.llm_balance/youapi_config.yaml << EOF
new_api_user: "5942"
EOF
```

Examples:
```bash
# Check balance and spent
llm-balance cost --platform=youapi
# Check token usage
llm-balance package --platform=youapi
# View configuration
llm-balance platform_config youapi
```

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
├── platform_configs.py     # Platform configuration management
├── error_handler.py       # Error handling
├── utils.py               # Utility functions
├── token_checker.py       # Token usage monitoring
├── token_formatter.py     # Token output formatting
└── platform_handlers/     # Platform handlers
    ├── __init__.py         # Handler factory
    ├── base.py            # Base handler class
    ├── aliyun.py          # Aliyun handler ✅
    ├── deepseek.py        # DeepSeek handler ✅
    ├── moonshot.py        # Moonshot handler ✅
    ├── volcengine.py      # Volcengine handler ✅
    ├── tencent.py         # Tencent handler ✅
    ├── zhipu.py           # Zhipu handler ✅
    ├── siliconflow.py     # SiliconFlow handler ✅
    ├── openai.py          # OpenAI handler ✅
    ├── anthropic.py       # Anthropic handler ✅
    ├── google.py          # Google handler ✅
    ├── foxcode.py         # FoxCode relay handler ✅
    ├── duckcoding.py      # DuckCoding relay handler ✅
    ├── _88code.py         # 88Code relay handler ✅
    └── youapi.py          # YouAPI relay handler ✅
```

**Note**: Additional platform handlers (Azure OpenAI, Lingyi, MiniMax) are available in the `dev` branch.

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
