# LLM 余额检查器

一个Python CLI工具，用于实时汇总各大语言模型平台的余额和使用情况。支持多种认证方式，提供统一的余额管理界面。

## 功能特性

- 🔑 **多重认证**: 支持API Key、浏览器Cookie和代理服务认证
- 🌐 **多平台支持**: 集成15个主流LLM平台（生产就绪）+ 第三方中转（FoxCode、DuckCoding、88Code、YourAPI、CSMindAI）
- 📊 **多种输出格式**: JSON、Markdown、表格、仅总额
- 💱 **多货币支持**: 支持CNY、USD、EUR等多种货币显示
- ⚙️ **灵活配置**: YAML配置文件，支持动态启用/禁用平台
- 🔧 **易于扩展**: 模块化设计，轻松添加新平台
- 💰 **实时监控**: 统一的余额和使用情况查询界面
- 🛡️ **错误容错**: 单平台失败不影响其他平台查询
- 🔒 **独立配置**: 特殊平台使用独立配置文件，避免污染全局配置

## 快速开始

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd llm-cost-checker

# 安装依赖
pip install -r requirements.txt

# 安装CLI工具
pip install -e .
```

### 环境变量配置

根据使用的平台设置相应的环境变量：

```bash
# API Key 认证平台
export DEEPSEEK_API_KEY="your_deepseek_api_key"
export OPENAI_ADMIN_KEY="your_openai_admin_key"
export MOONSHOT_API_KEY="your_moonshot_api_key"

# SDK 认证平台
export VOLCENGINE_ACCESS_KEY="your_volcengine_access_key"
export VOLCENGINE_SECRET_KEY="your_volcengine_secret_key"
export ALIYUN_ACCESS_KEY_ID="your_aliyun_access_key_id"
export ALIYUN_ACCESS_KEY_SECRET="your_aliyun_access_key_secret"

# 中国平台（API Key 认证）
export TENCENT_API_KEY="your_tencent_api_key"

# Cookie 认证平台（需要浏览器登录）
# Zhipu 需要登录 https://open.bigmodel.cn

# 特殊平台（独立配置）
# DuckCoding 需要额外的用户ID配置
export DUCKCODING_API_USER_ID="your_user_id"

# CSMindAI 需要额外的用户ID配置
export CSMINDDAI_NEW_API_USER="your_user_id"

# YouAPI 需要额外的用户ID配置
export YOUAPI_NEW_API_USER="your_user_id"

# Cubence 需要 Token 配置
export CUBENCE_TOKEN="your_token"
```

## 使用方法

### 基本命令

#### 检查余额
```bash
# 检查所有平台余额
llm-balance cost

# 检查特定平台
llm-balance cost --platform=openai

# 检查多个平台（逗号分隔）
llm-balance cost --platform=volcengine,aliyun
llm-balance cost --platform="deepseek, moonshot, tencent"

# 指定浏览器（用于Cookie认证）
llm-balance cost --browser=chrome

# 不同输出格式
llm-balance cost --format=json      # 机器可读格式
llm-balance cost --format=markdown  # 文档友好格式
llm-balance cost --format=table     # 控制台表格格式
llm-balance cost --format=total     # 仅显示总额

# 指定货币类型
llm-balance cost --currency=USD     # 美元显示总额
llm-balance cost --currency=EUR     # 欧元显示总额
llm-balance cost --currency=CNY     # 人民币显示总额（默认）
```

#### 检查Token使用量
```bash
# 检查所有支持平台的Token使用量
llm-balance package

# 检查特定平台的Token使用量
llm-balance package --platform=volcengine

# 检查特定模型的Token使用量
llm-balance package --platform=volcengine --model=deepseek-r1

# 检查多个平台的Token使用量
llm-balance package --platform=volcengine,zhipu

# Token使用量的不同输出格式
llm-balance package --format=table   # 控制台表格格式
llm-balance package --format=json    # 机器可读格式
llm-balance package --show-all       # 包含已停用套餐
```

> 默认情况下 `package` 命令不会展示 `inactive` 状态的套餐，可通过 `--show-all` 参数强制输出全部数据。

> 💡 向后兼容：`llm-balance check` 命令仍然可用，作为 `llm-balance cost` 的别名

#### 检查 Coding Plan 用量

检查 Claude Code 兼容平台（火山引擎、智谱）的 Coding Plan 限额：

```bash
# 检查所有平台
llm-balance plan

# 检查特定平台
llm-balance plan --platform=volcengine

# 使用特定浏览器的 cookies
llm-balance plan --browser=doubao
```

> **注意**: Coding Plan 监控需要平台特定的认证：
> - **火山引擎**: 浏览器 Cookies（登录 console.volcengine.com）
> - **智谱 AI**: 设置 `ZHIPU_AUTH_TOKEN` 或 `ANTHROPIC_AUTH_TOKEN` 环境变量

### 平台管理

```bash
# 列出所有平台及其状态
llm-balance list

# 启用平台
llm-balance enable moonshot

# 禁用平台
llm-balance disable moonshot
```

### 配置管理

```bash
# 查看平台完整配置
llm-balance config deepseek

# 查看特定配置项
llm-balance config deepseek api_url

# 设置配置项（支持自动类型转换）
llm-balance config deepseek enabled true
llm-balance config deepseek timeout 30
```

### 高级使用示例

#### 余额检查
```bash
# 查看所有平台的美元总余额
llm-balance cost --currency=USD --format=total

# 获取特定平台的欧元余额详情
llm-balance cost --platform=deepseek --currency=EUR --format=table

# 同时检查多个平台
llm-balance cost --platform=volcengine,aliyun,deepseek --format=table
llm-balance cost --platform="openai, deepseek, moonshot" --currency=USD --format=total

# 使用自定义汇率并输出为 JSON
LLM_BALANCE_RATES='{"USD": 7.5}' llm-balance cost --currency=USD --format=json

# 组合使用多个参数
llm-balance cost --platform=openai --browser=chrome --currency=GBP --format=markdown
```

#### Token使用量监控
```bash
# 检查所有支持平台的Token使用量
llm-balance package

# 检查火山引擎特定模型的Token使用量
llm-balance package --platform=volcengine --model=deepseek-r1

# 检查智谱AI特定模型的Token使用量
llm-balance package --platform=zhipu --model=glm-4-plus

# 比较多个平台的Token使用量
llm-balance package --platform=volcengine,zhipu --format=table

# 获取Token使用量的详细JSON输出
llm-balance package --platform=volcengine --format=json
```

## 汇率功能

### 概述

支持自动汇率转换功能，可以将不同货币的余额统一转换为目标货币进行总计。支持多种货币类型，包括人民币（CNY）、美元（USD）、欧元（EUR）等。

### 默认汇率

系统内置以下默认汇率（相对于 CNY）：
- CNY: 1.0
- USD: 7.2
- EUR: 7.8
- GBP: 9.1
- JPY: 0.048
- KRW: 0.0054
- Points: 0.01

### 查看和管理汇率

```bash
# 查看当前汇率
llm-balance rates

# 自定义汇率（会话级别）
LLM_BALANCE_RATES='{"USD": 7.5}' llm-balance cost

# 设置多个汇率
LLM_BALANCE_RATES='{"USD": 7.5, "EUR": 8.0}' llm-balance cost
```

### 货币转换规则

- **灵活转换**: 支持任意货币之间的相互转换
- **总计显示**: 在表格和总计格式中，会显示指定货币的总计
- **原始数据**: JSON 和 Markdown 格式保持原始货币显示
- **默认货币**: 默认使用 CNY 作为输出货币
- **自定义汇率**: 通过环境变量 `LLM_BALANCE_RATES` 设置

### 支持的货币

- CNY (人民币)
- USD (美元)
- EUR (欧元)
- GBP (英镑)
- JPY (日元)
- KRW (韩元)
- Points (积分)

## 配置文件

配置文件位于 `~/.llm_balance/platforms.yaml`，首次运行时会自动创建：

```yaml
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

## 支持的平台

### 🌍 国际平台 (3)

| 平台 | 认证方式 | 状态 | 说明 | Token监控 | 支出追踪 |
|------|----------|------|------|-----------|-----------|
| **OpenAI** | Admin API | ✅ | 需要 OPENAI_ADMIN_KEY | ❌ 不支持 | ✅ 完整支持 |
| **Anthropic** | Admin API | ✅ | 需要 ANTHROPIC_ADMIN_KEY | ❌ 不支持 | ✅ 完整支持 |
| **Google** | API Key | ✅ | 需要 GOOGLE_API_KEY | ❌ 不支持 | ✅ 完整支持 |

### 🇨🇳 中国平台 (7)

| 平台 | 认证方式 | 状态 | 说明 | Token监控 | 支出追踪 |
|------|----------|------|------|-----------|-----------|
| **DeepSeek** | API Key | ✅ | 需要 DEEPSEEK_API_KEY | ❌ 不支持 | ❌ 不支持 |
| **Moonshot** | API Key | ✅ | 需要 MOONSHOT_API_KEY | ❌ 不支持 | ❌ 不支持 |
| **硅基流动** | API Key | ✅ | 需要 SILICONFLOW_API_KEY | ❌ 不支持 | ✅ 完整支持 |
| **火山引擎** | SDK/Cookie | ✅ | 需要 VOLCENGINE_ACCESS_KEY + SECRET_KEY 或浏览器登录 | ✅ 完整支持 | ✅ 完整支持 |
| **阿里云** | 官方SDK | ✅ | 需要 ALIYUN_ACCESS_KEY_ID + SECRET_KEY | ❌ 不支持 | ✅ 完整支持 |
| **腾讯云** | SDK | ✅ | 需要 TENCENT_API_KEY (SecretId:SecretKey) | ❌ 不支持 | ✅ 支持 |
| **智谱AI** | Cookie | ✅ | 需要登录 https://open.bigmodel.cn | ✅ 完整支持 | ✅ 完整支持 |

### 🔄 第三方中转平台 (2)

| 平台 | 认证方式 | 状态 | 说明 | Token监控 | 支出追踪 | 独立配置 |
|------|----------|------|------|-----------|-----------|-----------|
| **FoxCode** | Cookie | ✅ | 中转服务，支持控制台访问 | ✅ 完整支持 | ✅ 完整支持 | ❌ 不需要 |
| **DuckCoding** | Cookie | ✅ | 中转服务，支持Token套餐 | ✅ 完整支持 | ✅ 完整支持 | ✅ 需要 |

### 📊 平台状态总结

**生产就绪 (12个平台)**: 以上列出的所有平台均经过完整测试，可用于生产环境。

**独立配置**: DuckCoding 使用独立配置文件，避免污染全局配置。

**开发状态**: 其他平台 (Azure OpenAI、零一万物、MiniMax) 在 `dev` 分支中积极开发中。

### 认证方式说明

#### 🔑 API Key 认证
适用于提供API接口的平台：
```bash
export DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
# export OPENAI_ADMIN_KEY="sk-admin-xxxxxxxxxxxxxxxxxxxxxxxx"
export MOONSHOT_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
```

#### 🍪 Cookie 认证
适用于需要浏览器会话的平台：
1. 登录对应的平台网站
2. 工具会自动从浏览器获取认证cookie
3. 支持Chrome、Firefox、Arc、Brave等主流浏览器

#### 🌐 特殊服务
使用特殊访问方式的平台：
- 智谱AI使用浏览器Cookie认证
- 需要登录 https://open.bigmodel.cn

### 第三方中转：FoxCode

FoxCode 为基于浏览器 Cookie 的中转服务，支持从控制台页面读取套餐与支出信息。

- 认证：浏览器 Cookie（域名 `foxcode.rjj.cc`），读取 `auth_token`，以 `Authorization: Bearer <token>` 请求 `https://foxcode.rjj.cc/api/user/dashboard`。
- package：使用 `data.subscription.active`。
  - Total = 计划 `quotaLimit`
  - Remaining = `quotaRemaining`（缺失时回退 `plan.duration`）
  - Used = Total - Remaining
  - Package 列显示 `plan.name`
- cost：Balance 显示 `-`（中转站无充值），Spent = ∑ `data.subscription.history[*].plan.price`（单位 CNY）。

示例：
```bash
llm-balance package --platform=foxcode
llm-balance cost --platform=foxcode
# 如需指定浏览器
llm-balance package --platform=foxcode --browser=chrome
llm-balance cost --platform=foxcode --browser=chrome
```

### 第三方中转：DuckCoding

DuckCoding 为基于浏览器 Cookie 的中转服务，支持Token套餐和费用追踪，使用独立配置。

- 认证：浏览器 Cookie（域名 `duckcoding.com`），请求 `https://duckcoding.com/api/user/self` 并附带 `new-api-user` 头。
- 配置：需要通过环境变量或独立配置文件设置 `api_user_id`。
- package：使用 `data.quota` 和 `data.used_quota`。
  - 总计 = `quota`（token数量）
  - 已用 = `used_quota`（token数量）
  - 剩余 = 总计 - 已用
  - Package 列显示 "DuckCoding 按量计费(不到期)"
- cost：余额和支出通过配额数据计算。
  - 余额 = `quota / 500000`（CNY）
  - 支出 = `used_quota / 500000`（CNY）

配置选项：
```bash
# 方法1：环境变量
export DUCKCODING_API_USER_ID="your_user_id"

# 方法2：CLI命令
llm-balance platform_config duckcoding api_user_id your_user_id

# 方法3：手动配置文件
cat > ~/.llm_balance/duckcoding_config.yaml << EOF
api_user_id: your_user_id
EOF
```

示例：
```bash
# 检查余额和支出
llm-balance cost --platform=duckcoding
# 检查Token使用量
llm-balance package --platform=duckcoding
# 查看配置
llm-balance platform_config duckcoding
# 配置用户ID
llm-balance platform_config duckcoding api_user_id your_user_id
```

## 浏览器支持

### 🍪 Cookie 认证支持
- **Chrome** (推荐)
- **Firefox**
- **Arc** 
- **Brave**
- **Chromium**
- **Slack**

### 🔧 故障排除

#### 常见问题

**Q: Cookie 认证失败**
```bash
# 确保已登录对应平台
# 尝试指定浏览器
llm-balance cost --browser=chrome
```

**Q: API Key 无效**
```bash
# 检查环境变量是否设置
echo $DEEPSEEK_API_KEY
echo $OPENAI_ADMIN_KEY

# 重新设置环境变量
export DEEPSEEK_API_KEY="your_valid_api_key"
```

**Q: 特定平台超时**
```bash
# 单独测试问题平台
llm-balance cost --platform=deepseek

# 检查网络连接
curl -I https://api.deepseek.com
```

#### 配置文件位置
- 主配置：`~/.llm_balance/platforms.yaml`
- 可通过环境变量 `LLM_BALANCE_CONFIG_FILE` 自定义路径

## 安全说明

- 🔒 **本地处理**: 所有认证信息都在本地处理，不会上传到外部服务器
- 🍪 **Cookie 读取**: 仅从浏览器读取必要的认证cookie，不会获取其他敏感信息
- 🛡️ **环境变量**: API Key 通过环境变量管理，不会写入配置文件
- 🔄 **会话性质**: Cookie 认证具有时效性，需要定期重新登录平台

## 开发指南

### 项目结构

```
src/llm_balance/
├── __init__.py              # 包信息和版本
├── cli.py                  # CLI命令接口
├── balance_checker.py      # 主要业务逻辑
├── config.py              # 配置文件管理
├── utils.py               # 工具函数
└── platform_handlers/     # 平台处理器
    ├── __init__.py         # 处理器工厂
    ├── base.py            # 基础处理器类
    ├── aliyun.py          # 阿里云处理器
    ├── deepseek.py        # DeepSeek处理器
    ├── claude.py          # Claude处理器
    ├── openai.py          # OpenAI处理器
    ├── volcengine.py      # 火山引擎处理器
    └── generic.py         # 通用处理器
```

### 添加新平台

1. **配置平台**: 在 `~/.llm_balance/platforms.yaml` 添加新平台配置
2. **创建处理器**: 继承 `BasePlatformHandler` 类，实现必要的认证和解析逻辑
3. **注册处理器**: 在 `platform_handlers/__init__.py` 的 `create_handler` 函数中添加新平台
4. **测试验证**: 使用 `llm-balance cost --platform=<new_platform>` 测试

### 开发环境

```bash
# 安装开发依赖
pip install -e .

# 运行测试
llm-balance cost --format=json

# 调试特定平台
llm-balance cost --platform=deepseek --browser=chrome
```

## 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/new-platform`)
3. 提交更改 (`git commit -am 'Add new platform support'`)
4. 推送到分支 (`git push origin feature/new-platform`)
5. 创建 Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
