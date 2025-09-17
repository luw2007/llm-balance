# LLM Balance Checker 快速参考

**支持12个生产就绪的LLM平台 + 第三方中转（FoxCode、DuckCoding）**

## 基本命令

### 查看余额
```bash
# 查看所有平台余额（默认人民币）
llm-balance cost

# 查看特定平台（生产就绪）
llm-balance cost --platform=deepseek      # DeepSeek ✅
llm-balance cost --platform=moonshot     # Moonshot AI ✅
llm-balance cost --platform=openai       # OpenAI ✅
llm-balance cost --platform=anthropic    # Anthropic ✅
llm-balance cost --platform=google       # Gemini ✅
llm-balance cost --platform=volcengine   # 火山引擎 ✅
llm-balance cost --platform=aliyun       # 阿里云 ✅
llm-balance cost --platform=tencent      # 腾讯云 ✅
llm-balance cost --platform=zhipu        # 智谱AI ✅
llm-balance cost --platform=siliconflow # 硅基流动 ✅
llm-balance cost --platform=foxcode      # FoxCode 中转 ✅
llm-balance cost --platform=duckcoding   # DuckCoding 中转 ✅

# 同时查看多个平台（逗号分隔）
llm-balance cost --platform=volcengine,aliyun,deepseek
llm-balance cost --platform="deepseek, moonshot, tencent"

# 使用别名命令
llm-balance check
```

### 货币转换
```bash
# 美元显示
llm-balance cost --currency=USD

# 欧元显示
llm-balance cost --currency=EUR

# 仅显示总额
llm-balance cost --currency=USD --format=total
```

### 输出格式
```bash
# 表格格式（默认）
llm-balance cost --format=table

# JSON 格式
llm-balance cost --format=json

# Markdown 格式
llm-balance cost --format=markdown

# 仅显示总额
llm-balance cost --format=total
```

## 平台管理

### 查看平台
```bash
# 列出所有平台
llm-balance list
```

### 启用/禁用平台
```bash
# 启用平台
llm-balance enable moonshot

# 禁用平台
llm-balance disable moonshot
```

## 配置管理

### 查看配置
```bash
# 查看平台完整配置
llm-balance config deepseek

# 查看特定配置项
llm-balance config deepseek api_url
```

### 设置配置
```bash
# 启用/禁用平台
llm-balance config deepseek enabled true

# 设置超时时间
llm-balance config deepseek timeout 30

# 特殊平台的独立配置
llm-balance platform_config duckcoding api_user_id 10801
llm-balance platform_config duckcoding  # 查看配置
```

## 汇率管理

### 查看汇率
```bash
llm-balance rates
```

### 自定义汇率
```bash
# 设置美元汇率
LLM_BALANCE_RATES='{"USD": 7.5}' llm-balance cost

# 设置多个汇率
LLM_BALANCE_RATES='{"USD": 7.5, "EUR": 8.0}' llm-balance cost
```

> 💡 更多汇率功能详情请参考 README.md 的"汇率功能"部分

## 浏览器设置

### 指定浏览器
```bash
# Chrome（默认）
llm-balance cost --browser=chrome

# Firefox
llm-balance cost --browser=firefox

# Arc
llm-balance cost --browser=arc

# Brave
llm-balance cost --browser=brave
```

## 常用组合

```bash
# 查看美元总余额
llm-balance cost --currency=USD --format=total

# 特定平台的欧元余额详情
llm-balance cost --platform=deepseek --currency=EUR --format=table

# 同时检查多个平台并显示美元总计
llm-balance cost --platform=volcengine,aliyun,deepseek --currency=USD --format=total

# 使用自定义汇率和JSON输出
LLM_BALANCE_RATES='{"USD": 7.5}' llm-balance cost --currency=USD --format=json

# 完整参数示例
llm-balance cost --platform=openai --browser=chrome --currency=GBP --format=markdown
```

## 环境变量设置

```bash
# 国际平台
# export OPENAI_ADMIN_KEY="your_openai_admin_key"      # OpenAI (当前不支持)
export ANTHROPIC_API_KEY="your_anthropic_api_key"   # Anthropic Claude
export GEMINI_API_KEY="your_google_api_key"         # Google Gemini
export AZURE_ACCESS_TOKEN="your_azure_token"        # Azure OpenAI

# 中国平台
export DEEPSEEK_API_KEY="your_deepseek_api_key"     # DeepSeek
export MOONSHOT_API_KEY="your_moonshot_api_key"     # Moonshot AI
export VOLCENGINE_ACCESS_KEY="your_access_key"      # 火山引擎
export VOLCENGINE_SECRET_KEY="your_secret_key"      # 火山引擎
export ALIYUN_ACCESS_KEY_ID="your_access_key_id"    # 阿里云
export ALIYUN_ACCESS_KEY_SECRET="your_secret_key"  # 阿里云
export TENCENT_API_KEY="your_tencent_api_key"       # 腾讯云
export LINGYI_API_KEY="your_lingyi_api_key"         # 零一万物
export MINIMAX_API_KEY="your_minimax_api_key"       # MiniMax
export SILICONFLOW_API_KEY="your_siliconflow_api_key" # 硅基流动

# 配置文件路径
export LLM_BALANCE_CONFIG_FILE="/path/to/config.yaml"
```

## 支持的货币

- CNY (人民币)
- USD (美元)
- EUR (欧元)
- GBP (英镑)
- JPY (日元)
- KRW (韩元)
- Points (积分)

## 支持的浏览器

- Chrome (推荐)
- Firefox
- Arc
- Brave
- Chromium
- Slack

> 💡 **说明**: 智谱AI需要在浏览器中登录 open.bigmodel.cn

## 第三方中转：FoxCode

- 认证：浏览器 Cookie（域名 `foxcode.rjj.cc`），从 Cookie 中读取 `auth_token`，以 `Authorization: Bearer <auth_token>` 请求 `https://foxcode.rjj.cc/api/user/dashboard`。
- 模型：标注为 `claude,gpt-5`。
- package：解析 `data.subscription.active`，Total=计划 `quotaLimit`，Remaining=`quotaRemaining`（缺失时回退 `plan.duration`），Used=Total-Remaining，Package 显示 `plan.name`。
- cost：Balance 显示为 `-`（该平台无充值），Spent=∑ `data.subscription.history[*].plan.price`（CNY）。

示例：
```bash
# 仅检查 FoxCode 的包/额度
llm-balance package --platform=foxcode

# 查看 FoxCode 的支出（Balance 显示为 -，Spent 累加 history.plan.price）
llm-balance cost --platform=foxcode

# 如需指定浏览器（默认 chrome）
llm-balance package --platform=foxcode --browser=chrome
llm-balance cost --platform=foxcode --browser=chrome
```

## 快速平台参考

### 🌍 国际平台 (3个)
| 平台 | 认证方式 | 环境变量 |
|------|----------|----------|
| OpenAI | 管理员API | 当前不支持 |
| Claude | API密钥 | `ANTHROPIC_API_KEY` |
| Gemini | API密钥 | `GEMINI_API_KEY` |
| Azure OpenAI | 访问令牌 | `AZURE_ACCESS_TOKEN` |

### 🇨🇳 中国平台 (9个)
| 平台 | 认证方式 | 环境变量 |
|------|----------|----------|
| DeepSeek | API密钥 | `DEEPSEEK_API_KEY` |
| Moonshot | API密钥 | `MOONSHOT_API_KEY` |
| 火山引擎 | SDK | `VOLCENGINE_ACCESS_KEY`, `VOLCENGINE_SECRET_KEY` |
| 阿里云 | SDK | `ALIYUN_ACCESS_KEY_ID`, `ALIYUN_ACCESS_KEY_SECRET` |
| 腾讯云 | SDK | `TENCENT_API_KEY` |
| 零一万物 | API密钥 | `LINGYI_API_KEY` |
| MiniMax | API密钥 | `MINIMAX_API_KEY` |
| 智谱AI | Cookie认证 | 需要浏览器登录 |
| 硅基流动 | API密钥 | `SILICONFLOW_API_KEY` |

### 最常用命令
```bash
# 检查所有平台
llm-balance cost

# 设置Cookie认证平台的浏览器
llm-balance set-browser chrome

# 检查特定平台
llm-balance cost --platform=deepseek

# 查看美元金额
llm-balance cost --currency=USD

# JSON格式输出
llm-balance cost --format=json
```
