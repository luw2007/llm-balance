# YesCode 平台快速使用指南

YesCode 是一个提供 AI API 中继服务的平台，支持订阅制模型和标准 OpenAI 兼容接口。

## 平台特性

- 🔑 **API Key 认证**: 使用 Bearer Token 认证方式
- 💰 **订阅制模型**: 支持每日/每周/每月额度管理
- 🔄 **标准兼容**: 支持标准 OpenAI 兼容接口 (/v1/messages)
- 📊 **多维度限额**: 包含 daily/weekly/monthly 三个维度的使用限额
- 🤖 **Claude 支持**: 支持 Claude Code/Plan 模型

## 快速配置

### 1. 注册账号并获取 API Key

1. 访问 [YesCode 官网](https://api.yescode.cloud)
2. 注册或登录您的账号
3. 进入 "API Keys" 页面
4. 点击 "创建密钥" 创建新的 API Key
5. 复制生成的 API Key

### 2. 配置环境变量

**方法 1: 直接设置环境变量**
```bash
export YESCODE_API_KEY="your_api_key_here"
```

**方法 2: 使用独立配置文件** (推荐)
```bash
mkdir -p ~/.llm_balance
cat > ~/.llm_balance/yescode_config.yaml << EOF
console_token: your_api_key_here
EOF
```

或者使用 `api_key` 字段：
```yaml
api_key: your_api_key_here
```

### 3. 配置平台

在 `~/.llm_balance/platforms.yaml` 中添加或确认 YesCode 配置：

```yaml
platforms:
  yescode:
    api_url: "https://api.yescode.cloud/api/v1/subscriptions"
    official_url: "https://api.yescode.cloud"
    api_management_url: "https://api.yescode.cloud/keys"
    method: "GET"
    auth_type: "bearer_token"
    env_var: "YESCODE_API_KEY"
    enabled: true
    params:
      timezone: "Asia/Shanghai"
    headers:
      User-Agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
      Accept: "application/json"
      Content-Type: "application/json"
```

## 使用方法

### 检查余额

```bash
llm-balance cost --platform=yescode
```

输出示例：
```
Platform    Balance    Currency    Spent    Details
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YesCode     $2.50      USD         $1.20    剩余额度: $2.50
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 检查 Token 使用量

```bash
llm-balance package --platform=yescode
```

输出示例：
```
Platform    Model       Package         Total      Used       Remaining    Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YesCode     yescode     Pro Plan        500.00     120.00     380.00       active
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 检查 Coding Plan 用量

```bash
llm-balance plan --platform=yescode
```

输出示例：
```
Platform    Status     Daily Usage    Weekly Usage    Monthly Usage    Update Time
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YesCode     Running    45.2%          32.8%           18.5%            2026-03-04 12:00:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 不同输出格式

```bash
llm-balance cost --platform=yescode --format=json
llm-balance cost --platform=yescode --format=markdown
llm-balance cost --platform=yescode --format=table
llm-balance cost --platform=yescode --format=total
```

## API 响应结构

YesCode API 返回的订阅信息结构：

```json
{
  "code": 0,
  "data": [
    {
      "status": "active",
      "expires_at": "2026-12-31T23:59:59+08:00",
      "daily_usage_usd": 1.5,
      "weekly_usage_usd": 8.2,
      "monthly_usage_usd": 25.3,
      "group": {
        "name": "Pro Plan",
        "platform": "yescode",
        "daily_limit_usd": 10.0,
        "weekly_limit_usd": 50.0,
        "monthly_limit_usd": 150.0,
        "claude_code_only": false
      }
    }
  ]
}
```

## 余额计算逻辑

YesCode 采用多维度限额管理，余额计算遵循以下规则：

1. **每日限额**: `daily_limit_usd - daily_usage_usd`
2. **每周限额**: `weekly_limit_usd - weekly_usage_usd`
3. **每月限额**: `monthly_limit_usd - monthly_usage_usd`

**实际可用余额 = min(每日剩余, 每周剩余, 每月剩余)**

这种方式确保在任何时间维度都不会超出限额。

## 支持的功能

| 功能 | 支持状态 | 说明 |
|------|----------|------|
| 余额查询 | ✅ | 查询多维度剩余额度 |
| 支出追踪 | ✅ | 追踪每月累计支出 |
| Token 监控 | ✅ | 监控套餐使用情况 |
| Coding Plan | ✅ | 监控每日/周/月使用百分比 |
| 多订阅支持 | ✅ | 支持同时管理多个订阅 |

## 注意事项

1. **API Key 安全**: 请妥善保管您的 API Key，不要泄露给他人
2. **时区设置**: API 请求默认使用 Asia/Shanghai 时区
3. **限额重置**: 
   - 每日限额在每天 00:00:00 重置
   - 每周限额在每周一 00:00:00 重置
   - 每月限额在每月 1 日 00:00:00 重置
4. **订阅状态**: 仅统计 `status=active` 的订阅
5. **货币单位**: 所有金额均以 USD 计价

## 常见问题

### Q: 环境变量不生效？

A: 确保正确设置环境变量：
```bash
export YESCODE_API_KEY="your_api_key"
llm-balance cost --platform=yescode
```

或使用独立配置文件：
```bash
cat ~/.llm_balance/yescode_config.yaml
```

### Q: 显示余额为 0？

A: 可能的原因：
1. API Key 无效或已过期
2. 所有维度的限额都已用完
3. 订阅状态不是 `active`

使用 JSON 格式查看详细信息：
```bash
llm-balance cost --platform=yescode --format=json
```

### Q: 如何查看原始 API 响应？

A: 使用 JSON 格式输出并查看 `raw_data` 字段：
```bash
llm-balance cost --platform=yescode --format=json | jq '.platforms[0].raw_data'
```

## 链接

- [YesCode 官网](https://api.yescode.cloud)
- [API 密钥管理](https://api.yescode.cloud/keys)
- [使用文档](https://api.yescode.cloud/docs)

## 更新日志

- **2026-03-04**: 初始版本，支持余额查询、Token 监控、Coding Plan 功能
