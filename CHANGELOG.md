# Changelog

All notable changes to this project will be documented in this file.

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

