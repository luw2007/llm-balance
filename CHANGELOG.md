# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **DawClaudeCode platform support**:
  - Added DawClaudeCode third-party relay platform with quota-based balance and package information
  - API endpoint: `https://dawclaudecode.com/api/user/self`
  - Cookie authentication via `new-api-user` header
  - Configuration via `DAWCLAUDECODE_API_USER_ID` environment variable or `~/.llm_balance/dawclaudecode_config.yaml`
  - Supports both balance/spent tracking and token usage monitoring
  - Balance calculation: `(quota + bonus_quota) / 500000` CNY
  - Spent calculation: `used_quota / 500000` CNY
  - Default status: Disabled

- **Magic666 platform support**:
  - Added Magic666 third-party relay platform with quota-based balance and package information
  - API endpoint: `https://magic666.top/api/user/self`
  - Cookie authentication via `new-api-user` header
  - Configuration via `MAGIC666_API_USER_ID` environment variable or `~/.llm_balance/magic666_config.yaml`
  - Supports both balance/spent tracking and token usage monitoring
  - Balance calculation: `(quota + bonus_quota) / 500000` CNY
  - Spent calculation: `used_quota / 500000` CNY
  - Default status: Disabled

- **Jimiai platform support**:
  - Added Jimiai third-party relay platform with quota-based balance and package information
  - API endpoint: `https://jimiai.ai/api/user/self`
  - Cookie authentication via `new-api-user` header
  - Configuration via `JIIMIAI_API_USER_ID` environment variable or `~/.llm_balance/jimiai_config.yaml`
  - Supports both balance/spent tracking and token usage monitoring
  - Balance calculation: `quota / 500000` CNY (5,000,000 tokens = 10 CNY)
  - Spent calculation: `used_quota / 500000` CNY
  - Default status: Disabled

### Changed
- **Platform count increased from 24 to 27**:
  - Updated all documentation to reflect new platform count
  - Third-party relay platforms now total 13 (was 10)
  - Independent configuration platforms expanded to 9 (was 6)

### Documentation
- **Updated CLAUDE.md**:
  - Added DawClaudeCode, Magic666, and Jimiai to third-party relay platforms list
  - Updated independent configuration architecture section
  - Added DAWCLAUDECODE_API_USER_ID, MAGIC666_API_USER_ID, and JIIMIAI_API_USER_ID to environment variables reference
  - Updated platform count from 24 to 27
- **Updated README.md**:
  - Added DawClaudeCode, Magic666, and Jimiai to platform features list (27 platforms)
  - Added detailed configuration sections for all three platforms
  - Updated third-party relay platforms table (9 platforms)
  - Updated token monitoring availability list
  - Updated production-ready platform count to 17

## [0.2.8] - 2025-11-28

### Added
- **Cubence platform support**:
  - Added Cubence AI platform with token-based authentication
  - API endpoint: `https://cubence.com/api/v1/dashboard/overview`
  - Configuration via `CUBENCE_TOKEN` environment variable or `~/.llm_balance/cubence_config.yaml`
  - Supports balance query with CNY currency
  - Note: Despite field name 'balance_dollar', actual currency is CNY (人民币)
  - Cookie-based token authentication using `token` cookie

- **Enhanced platform_config CLI command**:
  - Extended to support 5 platforms: `duckcoding`, `cubence`, `csmindai`, `yourapi`, `deepseek`
  - Each platform gets dedicated config file mapping and display names
  - Improved error messages with platform-specific guidance
  - Dynamic platform validation with supported platform list

### Changed
- **PlatformConfig dataclass extended**:
  - Added `token` field to support token-based authentication platforms
  - Enables consistent token configuration across multiple platforms

### Documentation
- **Updated README files**:
  - Added Cubence to supported platforms list (22 platforms total)
  - Added Cubence configuration examples in Special Platforms section
  - Updated platform count from 21 to 22 in feature highlights

## [0.2.7] - 2025-11-27

### Added
- **PackyCode platform support**:
  - Added PackyCode third-party relay platform (balance + package)
  - Cookie authentication via `new-api-user` header
  - API endpoint: `https://packyapi.com/api/user/self`
  - Configuration via `PACKYCODE_API_USER_ID` environment variable or `~/.llm_balance/packycode_config.yaml`
  - Pure pay-per-use model with quota-based billing

### Changed
- **Performance optimization with multi-threading**:
  - Implemented concurrent platform checking using ThreadPoolExecutor
  - Thread pool size: 5 workers (optimal balance between performance and resource usage)
  - Both `cost` and `package` commands now check platforms in parallel
  - Thread-safe handler caching with double-checked locking pattern
  - Significantly reduced total execution time for multi-platform queries

- **Unified API user ID naming across all platforms**:
  - YourAPI: Changed from `new_api_user` to `api_user_id`
    - Environment variable: `YOURAPI_NEW_API_USER` → `YOURAPI_API_USER_ID`
    - Config file field: `new_api_user` → `api_user_id`
  - CSMindAI: Changed from `new_api_user` to `api_user_id`
    - Environment variable: `CSMINDDAI_NEW_API_USER` → `CSMINDAI_API_USER_ID` (also fixed typo: removed extra 'D')
    - Config file field: `new_api_user` → `api_user_id`
  - HTTP header `new-api-user` remains unchanged (required by API)
  - Provides consistent naming with DuckCoding and PackyCode platforms

### Fixed
- **Cookie domain search warning suppression**:
  - Added `silent` parameter to `_get_cookies()` and `_get_arc_cookies()` methods
  - Default behavior now suppresses warnings when trying multiple cookie domains (silent=True)
  - Eliminates false-positive warnings when platforms correctly try fallback domains
  - Improves user experience by only showing meaningful error messages

- **PackyCode platform cookie domain fix**:
  - Added `www.packyapi.com` to cookie domain search list
  - Fixed authentication failure when logged in via `www.packyapi.com` console
  - Cookie domain search now tries: configured domain, `www.packyapi.com`, `.packyapi.com`, `packyapi.com`

- **DeepSeek spent calculation fix**:
  - Fixed invoice API response parsing by adding missing `biz_data` layer
  - Previous path: `data.invoices.payment_orders` (incorrect, returned empty list)
  - Correct path: `data.biz_data.invoices.payment_orders`
  - Spent now correctly calculated as: total_recharge - current_balance
  - Ensures accurate spending tracking for DeepSeek platform

- **88Code package calculation and status fix**:
  - Fixed remaining tokens calculation for MONTHLY/YEARLY packages (was incorrectly using actual currentCredits instead of time-based remainingCredits)
  - Status now correctly shows "inactive" when remainingDays <= 0 (previously showed "active" when isActive=true even if expired)
  - Ensures accurate balance tracking for subscription plans


## [0.2.6] - 2025-11-20

### Added
- **Billing mode differentiation for subscription-based platforms**:
  - Added `expiry_date`, `reset_count`, and `reset_time` fields to `ModelTokenInfo` dataclass
  - New CLI parameters for package command: `--show-expiry`, `--show-reset`, `--show-reset-time`
  - Dynamic table formatting that adjusts column width based on enabled features

- **88Code platform enhancements**:
  - Implemented `planType`-based calculation logic:
    - `PAY_PER_USE`: Uses actual credit usage (remaining = currentCredits)
    - `MONTHLY/YEARLY`: Uses time-based depreciation (remaining = total × remainingDays/totalDays)
  - Reset information (count/time) only displayed for subscription plans
  - Enhanced spent calculation accuracy for mixed subscription types

- **FoxCode platform enhancements**:
  - Implemented `resetType`-based calculation logic:
    - `NEVER`: Uses actual quota usage (pay-per-use model)
    - `MONTHLY/WEEKLY/YEARLY/DAILY`: Uses time-based depreciation (subscription model)
  - Extracts expiry date from `endDate` field
  - Reset time extracted from `lastResetAt` for subscription plans

- **Moonshot platform package support**:
  - Implemented `get_model_tokens()` method for Moonshot Code Package
  - Queries billing API endpoint with FEATURE_CODING scope
  - Extracts limit, used, remaining, and resetTime information
  - Requires `MOONSHOT_CONSOLE_TOKEN` and `MOONSHOT_ORG_ID` environment variables

- **PackyCode platform support**:
  - Added PackyCode third-party relay platform (balance + package)
  - Cookie authentication via `new-api-user` header
  - API endpoint: `https://packyapi.com/api/user/self`
  - Configuration via `PACKYCODE_API_USER_ID` environment variable or `~/.llm_balance/packycode_config.yaml`
  - Pure pay-per-use model with quota-based billing

### Changed
- **Token formatter improvements**:
  - Table format now supports optional columns for expiry, reset count, and reset time
  - Markdown format includes subscription lifecycle information
  - Column widths dynamically adjust based on enabled features

- **Performance optimization with multi-threading**:
  - Implemented concurrent platform checking using ThreadPoolExecutor
  - Thread pool size: 5 workers (optimal balance between performance and resource usage)
  - Both `cost` and `package` commands now check platforms in parallel
  - Thread-safe handler caching with double-checked locking pattern
  - Significantly reduced total execution time for multi-platform queries

### Technical Details
- Both 88Code and FoxCode now distinguish between:
  - **Pay-per-use packages**: Calculated by actual usage, no reset information
  - **Subscription packages**: Calculated by time depreciation, includes reset information
- This ensures accurate balance and spent reporting for platforms with multiple billing models

## [0.2.5] - 2025-09-20

### Added
- CSMindAI third-party relay support (balance + package):
  - Cookie auth via `new-api-user` header against `https://api.csmindai.com/api/user/self`.
  - package: parse `data.quota` and `data.used_quota`:
    - Total = `quota` (token count, converted to CNY by dividing by 500000)
    - Used = `used_quota` (token count, converted to CNY by dividing by 500000)
    - Remaining = Total - Used
    - Package displays user group information with status display
  - cost: Balance and spent calculated from quota data with currency conversion
  - Requires independent configuration via environment variable or separate config file

### Added
- YourAPI third-party relay support (balance + package):
  - Cookie auth via `new-api-user` header against `https://yourapi.cn/api/user/self`.
  - package: parse `data.quota` and `data.used_quota`:
    - Total = `quota` (token count, converted to CNY by dividing by 500000)
    - Used = `used_quota` (token count, converted to CNY by dividing by 500000)
    - Remaining = Total - Used
    - Package displays user group information with status display
  - cost: Balance and spent calculated from quota data with currency conversion
  - Requires independent configuration via environment variable or separate config file

### Added
- 88Code third-party relay support (balance + package):
  - Console token auth via environment variable or separate config file
  - package: Uses subscription data from `https://www.88code.org/admin-api/cc-admin/system/subscription/my`
    - Total = sum of all subscription costs (active + inactive)
    - Balance = calculated based on usage ratio of active subscriptions
    - Spent = Total cost - Balance
    - Package column shows subscription features with status display
  - Status: Shows "active" or "inactive" based on subscription `isActive` flag
  - Fixed spent calculation to include all subscriptions for accurate total cost

### Added
- Status column feature for package display:
  - Added `status` field to `ModelTokenInfo` dataclass
  - Updated token formatter to display status columns in table and markdown formats
  - Implemented status determination logic across all platforms (88code, zhipuai, duckcoding, foxcode, volcengine, aliyun, tencent, yourapi)
  - Enhanced package display with activation status information

### Changed
- Renamed "code88" platform to "88code" throughout the codebase
- Updated all platform handlers to support status field in token information
- Enhanced independent configuration system for new relay platforms
- Improved spent calculation accuracy for subscription-based platforms

### Docs
- Updated all documentation files to include CSMindAI, 88Code and YourAPI support
- Added comprehensive configuration examples for new platforms
- Updated platform status summaries (now supports 15 platforms total)
- Enhanced authentication and configuration documentation

## [0.2.3] - 2025-09-17

### Added
- DuckCoding third-party relay support (package + cost):
  - Cookie auth via `new-api-user` header against `https://duckcoding.com/api/user/self`.
  - package: parse `data.quota` and `data.used_quota`:
    - Total = `quota` (token count)
    - Used = `used_quota` (token count)
    - Remaining = Total - Used
    - Package displays "DuckCoding 按量计费(不到期)"
  - cost: Balance and spent calculated from quota data:
    - Balance = `quota / 500000` (CNY)
    - Spent = `used_quota / 500000` (CNY)
  - Requires independent configuration via environment variable, CLI command, or separate config file.

### Added
- Independent configuration system for special platforms:
  - Supports environment variables (highest priority)
  - Separate configuration files (medium priority)
  - CLI commands for platform-specific configuration:
    - `llm-balance platform_config duckcoding api_user_id your_user_id`
    - `llm-balance platform_config duckcoding` (view config)
  - Configuration priority: Environment variables → separate config files → global config

### Added
- New CLI command `platform_config` for managing platform-specific configurations
- Support for 12 total platforms (International: 3, Chinese: 7, Third-Party: 2)

### Docs
- Updated all documentation files (README.md, README.zh.md, quickstart.md, quickstart.zh.md, config.example.yaml) to include DuckCoding support and independent configuration system
- Added comprehensive examples for DuckCoding configuration methods
- Updated platform status summaries and authentication type documentation

## [0.2.2] - 2025-09-16

### Fixed
- CLI: `enable`/`disable` now accept multiple platforms via comma-separated values or multiple args (e.g., `llm-balance enable google,openai`).

## [0.2.1] - 2025-09-16

### Added
- FoxCode third-party relay support (package + cost):
  - Cookie auth via `auth_token` (header `Authorization: Bearer <token>`) against `https://foxcode.rjj.cc/api/user/dashboard`.
  - package: parse `data.subscription.active` with mappings:
    - Total = plan `quotaLimit`
    - Remaining = `quotaRemaining` (fallback to plan `duration`)
    - Used = Total - Remaining
    - Package displays `plan.name`
  - cost: Balance displays `-` (relay cannot be topped up); Spent = sum of `data.subscription.history[*].plan.price` in CNY.
  - Registered as `foxcode`, disabled by default to avoid affecting default runs.

### Changed
- Table/Markdown formatting now shows `-` for non-numeric balances and excludes them from totals.
- Token table displays human-readable package name; supports FoxCode field mapping when package info is an object.

### Docs
- README.md/README.zh.md and quickstart.md/quickstart.zh.md updated with FoxCode usage and notes.
