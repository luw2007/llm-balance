# LLM Balance Checker Quick Reference

**Supporting 12 major LLM platforms worldwide**

## Basic Commands

### Check Balance
```bash
# Check all platform balance (default CNY)
llm-balance cost

# Check specific platform
llm-balance cost --platform=deepseek   # DeepSeek
llm-balance cost --platform=moonshot    # Moonshot AI
llm-balance cost --platform=openai      # OpenAI
llm-balance cost --platform=claude      # Anthropic
llm-balance cost --platform=volcengine  # Volcengine
llm-balance cost --platform=aliyun      # Alibaba Cloud
llm-balance cost --platform=gemini      # Google Gemini
llm-balance cost --platform=azure_openai # Azure OpenAI
llm-balance cost --platform=tencent     # Tencent Cloud
llm-balance cost --platform=lingyi      # Lingyi Wanwu
llm-balance cost --platform=minimax     # MiniMax
llm-balance cost --platform=zhipu       # Zhipu AI

# Use alias command
llm-balance check
```

### Currency Conversion
```bash
# USD display
llm-balance cost --currency=USD

# EUR display
llm-balance cost --currency=EUR

# Show total only
llm-balance cost --currency=USD --format=total
```

### Output Formats
```bash
# Table format (default)
llm-balance cost --format=table

# JSON format
llm-balance cost --format=json

# Markdown format
llm-balance cost --format=markdown

# Show total only
llm-balance cost --format=total
```

## Platform Management

### View Platforms
```bash
# List all platforms
llm-balance list
```

### Enable/Disable Platforms
```bash
# Enable platform
llm-balance enable moonshot

# Disable platform
llm-balance disable moonshot
```

## Configuration Management

### View Configuration
```bash
# View complete platform configuration
llm-balance config deepseek

# View specific configuration item
llm-balance config deepseek api_url
```

### Set Configuration
```bash
# Enable/disable platform
llm-balance config deepseek enabled true

# Set timeout
llm-balance config deepseek timeout 30
```

## Exchange Rate Management

### View Exchange Rates
```bash
llm-balance rates
```

### Custom Exchange Rates
```bash
# Set USD exchange rate
LLM_BALANCE_RATES='{"USD": 7.5}' llm-balance cost

# Set multiple exchange rates
LLM_BALANCE_RATES='{"USD": 7.5, "EUR": 8.0}' llm-balance cost
```

> 💡 For more exchange rate features, please refer to the "Exchange Rate Features" section in README.md

## Browser Settings

### Specify Browser
```bash
# Chrome (default)
llm-balance cost --browser=chrome

# Firefox
llm-balance cost --browser=firefox

# Arc
llm-balance cost --browser=arc

# Brave
llm-balance cost --browser=brave
```

## Common Combinations

```bash
# View total balance in USD
llm-balance cost --currency=USD --format=total

# EUR details for specific platform
llm-balance cost --platform=deepseek --currency=EUR --format=table

# Use custom exchange rates and JSON output
LLM_BALANCE_RATES='{"USD": 7.5}' llm-balance cost --currency=USD --format=json

# Complete parameter example
llm-balance cost --platform=openai --browser=chrome --currency=GBP --format=markdown
```

## Environment Variables

```bash
# International Platforms
export OPENAI_ADMIN_KEY="your_openai_admin_key"      # OpenAI (requires admin key)
export ANTHROPIC_API_KEY="your_anthropic_api_key"   # Anthropic Claude
export GEMINI_API_KEY="your_gemini_api_key"         # Google Gemini
export AZURE_ACCESS_TOKEN="your_azure_token"        # Azure OpenAI

# Chinese Platforms  
export DEEPSEEK_API_KEY="your_deepseek_api_key"     # DeepSeek
export MOONSHOT_API_KEY="your_moonshot_api_key"     # Moonshot AI
export VOLCENGINE_ACCESS_KEY="your_access_key"      # Volcengine
export VOLCENGINE_SECRET_KEY="your_secret_key"      # Volcengine
export ALIYUN_ACCESS_KEY_ID="your_access_key_id"    # Alibaba Cloud
export ALIYUN_ACCESS_KEY_SECRET="your_secret_key"  # Alibaba Cloud
export TENCENT_API_KEY="your_tencent_api_key"       # Tencent Cloud
export LINGYI_API_KEY="your_lingyi_api_key"         # Lingyi Wanwu
export MINIMAX_API_KEY="your_minimax_api_key"       # MiniMax

# Configuration file path
export LLM_BALANCE_CONFIG_FILE="/path/to/config.yaml"
```

## Supported Currencies

- CNY (Chinese Yuan)
- USD (US Dollar)
- EUR (Euro)
- GBP (British Pound)
- JPY (Japanese Yen)
- KRW (Korean Won)
- Points (Points)

## Supported Browsers

- Chrome (Recommended)
- Firefox
- Arc
- Brave
- Chromium
- Slack

> 💡 **Note**: Zhipu AI requires browser login to open.bigmodel.cn

## Quick Platform Reference

### 🌍 International Platforms (4)
| Platform | Auth Method | Key Variable |
|----------|-------------|---------------|
| OpenAI | Admin API | `OPENAI_ADMIN_KEY` |
| Claude | API Key | `ANTHROPIC_API_KEY` |
| Gemini | API Key | `GEMINI_API_KEY` |
| Azure OpenAI | Access Token | `AZURE_ACCESS_TOKEN` |

### 🇨🇳 Chinese Platforms (8)
| Platform | Auth Method | Key Variables |
|----------|-------------|----------------|
| DeepSeek | API Key | `DEEPSEEK_API_KEY` |
| Moonshot | API Key | `MOONSHOT_API_KEY` |
| Volcengine | SDK | `VOLCENGINE_ACCESS_KEY`, `VOLCENGINE_SECRET_KEY` |
| Aliyun | SDK | `ALIYUN_ACCESS_KEY_ID`, `ALIYUN_ACCESS_KEY_SECRET` |
| Tencent | SDK | `TENCENT_API_KEY` |
| Lingyi | API Key | `LINGYI_API_KEY` |
| MiniMax | API Key | `MINIMAX_API_KEY` |
| Zhipu | Cookie | Browser login required |

### Most Common Commands
```bash
# Check all platforms
llm-balance cost

# Set browser for cookie platforms
llm-balance set-browser chrome

# Check specific platform
llm-balance cost --platform=deepseek

# View in USD
llm-balance cost --currency=USD

# JSON output
llm-balance cost --format=json
```