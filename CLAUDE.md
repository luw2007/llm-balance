# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool for checking costs and balances across 28 LLM platforms with support for multiple authentication methods (API keys, browser cookies, official SDKs), multi-currency conversion, and real-time cost monitoring.

**Current Version**: 0.3.0

## Development Commands

### Setup & Installation
```bash
# Install in development mode
pip install -e .

# Install dependencies (includes Volcengine SDK)
pip install -r requirements.txt

# Optional platform-specific SDKs
pip install aliyun-python-sdk-bssopenapi>=2.0.0  # Aliyun billing
pip install tencentcloud-sdk-python>=3.0.0      # Tencent Cloud

# Verify installation
llm-balance --help
```

### Testing
```bash
# Run comprehensive automated tests
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

### Common Commands
```bash
# Check balance and spent across platforms
llm-balance cost
llm-balance cost --platform=deepseek --format=json

# Check token usage for supported platforms
llm-balance package
llm-balance package --platform=volcengine --model=deepseek-r1

# Platform management
llm-balance list                    # List all platforms
llm-balance enable moonshot         # Enable platform
llm-balance disable tencent         # Disable platform

# Configuration
llm-balance config deepseek         # View platform config
llm-balance set-browser chrome      # Set global browser for cookie auth
llm-balance platform_config duckcoding api_user_id your_user_id  # Independent config

# Build & distribution
python setup.py sdist bdist_wheel
pip install dist/llm_balance-0.3.0-py3-none-any.whl
```

## Architecture

### Core Components & Flow

```
CLI (cli.py - Fire-based)
    ↓
BalanceChecker (balance_checker.py)
    ↓
ConfigManager (config.py) → YAML config at ~/.llm_balance/config.yaml
    ↓
Factory (platform_handlers/__init__.py) → create_handler()
    ↓
Platform Handlers (platform_handlers/*.py)
    ↓
BasePlatformHandler (base.py) → CostInfo / PlatformTokenInfo
```

### Key Architectural Patterns

#### 1. **Factory Pattern with Handler Registry**
- `create_handler()` in `platform_handlers/__init__.py` maps platform names to handler classes
- All 27 platforms registered in a dictionary
- No fallback - platforms must be explicitly supported

#### 2. **Multi-threaded Concurrent Checking**
- ThreadPoolExecutor with **5 workers** (see `balance_checker.py:24`)
- Thread-safe handler caching with locks
- Platforms checked in parallel for performance
- Individual platform failures don't block others

#### 3. **Independent Configuration Architecture**
Some platforms (DuckCoding, CSMindAI, YouAPI, 88Code, 88996, Cubence, DawClaudeCode, Magic666, Jimiai, OpenClaudeCode) use separate config files:
- Priority: Environment variables > Separate config files > Global config
- Separate configs at `~/.llm_balance/{platform}_config.yaml`
- Prevents pollution of global `config.yaml`
- Example: `DUCKCODING_API_USER_ID` or `~/.llm_balance/duckcoding_config.yaml`

#### 4. **Template Method Pattern**
All handlers inherit from `BasePlatformHandler` and implement:
- `get_balance()` → Returns `CostInfo` with balance, spent, currency, raw_data
- `get_platform_name()` → Returns display name
- `get_model_tokens()` → Optional, returns `PlatformTokenInfo` for token monitoring

#### 5. **Error Resilience**
- Each platform wrapped in try-catch
- Single platform failure doesn't stop other checks
- Returns `None` for failed platforms, continues execution
- Meaningful error messages without stack traces

### Authentication Methods

1. **API Key** (DeepSeek, Moonshot, SiliconFlow, MiniMax)
   - Bearer token in Authorization header
   - Environment variable: `{PLATFORM}_API_KEY`

2. **Official SDK** (Volcengine, Aliyun, Tencent)
   - Platform-specific SDKs with access key + secret key
   - Volcengine SDK included in requirements.txt
   - Others require manual installation

3. **Browser Cookies** (Zhipu, FoxCode, AICoding)
   - Uses pycookiecheat to extract cookies from browser
   - Global browser setting via `llm-balance set-browser chrome`
   - Per-command override: `--browser=chrome`

4. **Third-party Relay** (DuckCoding, PackyCode, CSMindAI, YouAPI, 88Code, 88996, DawClaudeCode, Magic666, Jimiai, OpenClaudeCode)
   - Cookie-based with custom headers (`new-api-user`, `rix-api-user`, etc.)
   - Requires independent configuration (see pattern #3)

### Platform Categories & Default Status

#### Default Enabled (4 platforms - Core Chinese AI Models)
1. **DeepSeek** - Independent AI company, GPT-4 level performance
2. **Moonshot** (Kimi) - Long context specialist
3. **Zhipu** (GLM) - Tsinghua-backed AI company
4. **MiniMax** - Multimodal AI company

#### Default Disabled (23 platforms)

**International Platforms (3)**
- OpenAI, Anthropic, Google

**Cloud Service Providers (4)**
- **Volcengine** = ByteDance's cloud platform (hosts Doubao/豆包 - #1 Chinese LLM)
- **Aliyun** = Alibaba Cloud (hosts Tongyi Qianwen/通义千问 - #3 Chinese LLM)
- Tencent Cloud (hosts Hunyuan/混元)
- SiliconFlow (硅基流动)

**Third-party Relay Platforms (14)**
- FoxCode, DuckCoding, PackyCode, 88Code, 88996, AICoding, YouAPI, CSMindAI, YesCode, Cubence, DawClaudeCode, Magic666, Jimiai, OpenClaudeCode

**Relay Management Platforms (3)**
- OneAPI (self-hosted), API-Proxy (public relay), FastGPT (open-source app platform)

> **Important**: Volcengine and Aliyun query **total cloud account billing**, not just AI model costs. They represent ByteDance's Doubao and Alibaba's Qianwen respectively.

### Configuration System

#### Configuration Hierarchy
1. **Environment Variables** (highest priority)
2. **Separate Config Files** (`~/.llm_balance/{platform}_config.yaml`)
3. **Global Config** (`~/.llm_balance/config.yaml`)
4. **Default Configs** (from handler's `get_default_config()`)

#### Configuration Loading Flow
```python
# In ConfigManager
def get_platform_config(platform_name):
    # Get default from handler
    config = handler_class.get_default_config()
    # Apply user overrides from global config
    config.update(user_config.get(platform_name, {}))
    return config

# In special platform handlers (e.g., DuckCoding)
def _load_env_config():
    # Try environment variable first
    if env_var := os.getenv('DUCKCODING_API_USER_ID'):
        self.config.api_user_id = env_var
        return
    # Try separate config file
    config_path = Path.home() / '.llm_balance' / 'duckcoding_config.yaml'
    if config_path.exists():
        # Load from file
```

#### Per-Platform Configuration
Each platform handler defines default config via `get_default_config()` classmethod:
- `api_url`, `method`, `auth_type`, `env_var`
- `headers`, `params`, `data`
- `enabled`, `show_cost`, `show_package`
- Authentication-specific fields (cookie_domain, region, etc.)

### Currency Conversion System

**Design**: All currencies convert through CNY as intermediate currency.

```python
# Default rates (relative to CNY)
DEFAULT_RATES = {
    'CNY': 1.0,
    'USD': 7.2,
    'EUR': 7.8,
    'GBP': 9.1,
    'JPY': 0.048,
    'KRW': 0.0054,
    'Points': 0.01
}

# Conversion formula
def convert(amount, from_currency, to_currency):
    cny_amount = amount / RATES[from_currency]  # Convert to CNY
    return cny_amount * RATES[to_currency]      # Convert to target
```

**Custom Rates**: Set via `LLM_BALANCE_RATES='{"USD": 7.5}'` environment variable.

### Data Models

Located in `platform_handlers/base.py`:

```python
@dataclass
class CostInfo:
    platform: str           # Display name
    balance: float          # Current balance
    currency: str           # Currency code (CNY, USD, etc.)
    spent: Union[float, str]  # Spent amount or "-" if unsupported
    spent_currency: str     # Spent currency or "-"
    raw_data: Dict          # Original API response

@dataclass
class ModelTokenInfo:
    model: str              # Model name
    package: str            # Package/subscription name
    remaining_tokens: float # Tokens remaining
    used_tokens: float      # Tokens used
    total_tokens: float     # Total tokens
    status: str             # "active" or "inactive"

@dataclass
class PlatformTokenInfo:
    platform: str           # Platform name
    models: List[ModelTokenInfo]
    raw_data: Dict          # Original API response
```

### Output Formats

Implemented in `utils.py`:

- **table**: Console-friendly with rich formatting and totals (default)
- **json**: Machine-readable with full raw API responses
- **markdown**: Documentation-friendly tables
- **total**: Single line with total in target currency

## Platform Handler Implementation Patterns

### Adding New Platforms

1. **Create Handler**: Inherit from `BasePlatformHandler` in `platform_handlers/`
2. **Implement Methods**:
   ```python
   @classmethod
   def get_default_config(cls) -> dict:
       return {
           "api_url": "...",
           "method": "GET",
           "auth_type": "api_key",
           "env_var": "PLATFORM_API_KEY",
           "enabled": False,  # Default disabled for new platforms
           # ...
       }

   def get_balance(self) -> CostInfo:
       # Authentication logic
       # API request
       # Parse response
       return CostInfo(...)

   def get_platform_name(self) -> str:
       return "Platform Name"

   def get_model_tokens(self) -> PlatformTokenInfo:  # Optional
       # Return token usage data
   ```

3. **Register**: Add to `handler_classes` dict in `platform_handlers/__init__.py`
4. **Test**: `llm-balance cost --platform=new_platform`

### Spent Tracking Implementation Strategies

Platforms that support spent tracking should use one of:
- **Direct API**: Use platform's billing/spent API (preferred)
- **Transaction History**: Query transaction records and sum expenses (Aliyun approach)
- **Recharge Calculation**: `total_recharge - current_balance` (if recharge API available)

For unsupported platforms, return `"-"` as spent value to distinguish from zero spending.

### Independent Configuration Pattern

For platforms requiring special configuration:

```python
class SpecialPlatformHandler(BasePlatformHandler):
    def __init__(self, config, browser='chrome'):
        super().__init__(browser)
        self.config = config
        self._load_env_config()  # Load independent config

    def _load_env_config(self):
        # Priority 1: Environment variable
        if env_value := os.getenv('PLATFORM_SPECIAL_KEY'):
            self.config.special_key = env_value
            return

        # Priority 2: Separate config file
        config_path = Path.home() / '.llm_balance' / 'platform_config.yaml'
        if config_path.exists():
            with open(config_path, 'r') as f:
                platform_config = yaml.safe_load(f) or {}
                if 'special_key' in platform_config:
                    self.config.special_key = platform_config['special_key']
```

## Important Implementation Notes

### Version Management
- Version defined in `__init__.py` and `setup.py`
- Currently at **0.3.0**
- Update both files when bumping version

### Thread Safety
- Handler caching uses `threading.Lock()` (see `balance_checker.py:26`)
- Each platform check runs in separate thread
- Thread pool size: 5 workers (configurable via `self.max_workers`)

### Recent Architecture Changes
- **Volcengine Package API**: Parameter format requires string `"20"` not integer `100`
- **Platform Enable/Disable Strategy**: Only 4 core Chinese platforms enabled by default
- **Cloud Platform Clarification**: Volcengine = ByteDance Doubao, Aliyun = Alibaba Qianwen
- **Independent Configuration**: Expanded to 9 platforms to avoid global config pollution

### Testing Framework
Automated test script (`test_llm_balance.py`):
- 16 test cases covering all platforms and output formats
- Environment validation and dependency checking
- JSON export capability for detailed analysis
- Platform-specific testing for isolated debugging
- Measures execution time for performance tracking

### Known Issues & Workarounds
- Some platforms return `"-"` for spent when tracking unsupported
- Volcengine SDK requires specific parameter types (strings vs integers)
- Configuration objects need JSON serialization cleanup for JSON output
- Cookie authentication requires active browser login session

## Environment Variables Reference

```bash
# API Key Platforms
DEEPSEEK_API_KEY="sk-..."
MOONSHOT_API_KEY="sk-..."
SILICONFLOW_API_KEY="..."

# SDK Platforms
VOLCENGINE_ACCESS_KEY="..."
VOLCENGINE_SECRET_KEY="..."
ALIYUN_ACCESS_KEY_ID="..."
ALIYUN_ACCESS_KEY_SECRET="..."
TENCENT_API_KEY="SecretId:SecretKey"

# Third-party Relay (Independent Config)
DUCKCODING_API_USER_ID="..."
CLOUD88996_API_USER_ID="..."
CODE88_CONSOLE_TOKEN="..."
YOURAPI_NEW_API_USER="..."
CUBENCE_TOKEN="..."
CSMINDAI_API_USER_ID="..."
PACKYCODE_API_USER_ID="..."
DAWCLAUDECODE_API_USER_ID="..."
MAGIC666_API_USER_ID="..."
JIIMIAI_API_USER_ID="..."
OPENCLAUDECODE_API_USER_ID="..."

# Global Settings
LLM_BALANCE_CONFIG_FILE="/path/to/config.yaml"
LLM_BALANCE_RATES='{"USD": 7.5}'
```

## CLI Command Reference

### Main Commands
- `cost`: Check balance and spent across platforms
- `package`: Check token usage for supported platforms
- `list`: List all platforms and their status
- `enable/disable`: Enable or disable platforms
- `config`: View/edit platform configuration
- `platform_config`: Manage independent platform configs
- `set-browser`: Set global browser for cookie-based platforms
- `rates`: Show current exchange rates
- `diagnose`: Run system diagnostics
- `generate_config`: Generate fresh config from handlers

### Platform Selection
- Single: `--platform=deepseek`
- Multiple: `--platform=deepseek,volcengine` or `--platform=deepseek --platform=volcengine`
- All enabled: (no --platform flag)

### Output Formats
- `--format=table` (default): Clean console output
- `--format=json`: Machine-readable with raw API responses
- `--format=total`: Single currency total only
- `--format=markdown`: Documentation-friendly tables

### Currency Support
- `--currency=USD`: Convert totals to USD
- `--currency=EUR`: Convert totals to EUR
- Custom rates via `LLM_BALANCE_RATES` environment variable
