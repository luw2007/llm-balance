# Changelog

All notable changes to this project will be documented in this file.

## [0.2.4] - 2025-09-19

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
- Updated all documentation files to include 88Code and YourAPI support
- Added comprehensive configuration examples for new platforms
- Updated platform status summaries (now supports 14 platforms total)
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
    - `llm-balance platform_config duckcoding api_user_id 10801`
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
