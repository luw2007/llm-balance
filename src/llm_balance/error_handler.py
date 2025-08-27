"""
Improved error handling with helpful messages for LLM Balance Checker
"""

import os
from typing import Dict, Any

# Platform information with official names and URLs
PLATFORM_INFO = {
    'deepseek': {
        'name': 'DeepSeek',
        'url': 'https://platform.deepseek.com',
        'api_url': 'https://platform.deepseek.com/api_keys',
        'env_var': 'DEEPSEEK_API_KEY',
        'description': 'DeepSeek AI Platform',
        'auth_type': 'API Key',
        'setup_steps': [
            '访问 https://platform.deepseek.com 并注册/登录',
            '进入 "API Keys" 页面',
            '点击 "Create API Key" 创建新的API Key',
            '复制生成的API Key（格式：sk-xxxxxxxx）',
            '设置环境变量: export DEEPSEEK_API_KEY="your_api_key"'
        ],
        'notes': [
            'API Key以 sk- 开头',
            '免费额度有限，超额需要付费',
            '支持多种模型：DeepSeek-V2, DeepSeek-Coder等'
        ]
    },
    'openai': {
        'name': 'OpenAI',
        'url': 'https://platform.openai.com',
        'api_url': 'https://platform.openai.com/api-keys',
        'env_var': 'OPENAI_ADMIN_KEY',
        'description': 'OpenAI Platform',
        'auth_type': 'Admin API Key',
        'setup_steps': [
            '访问 https://platform.openai.com 并登录',
            '进入 "API keys" 页面',
            '点击 "Create new secret key"',
            '选择 "Admin" 权限（查看组织账单需要）',
            '复制API Key并设置环境变量: export OPENAI_ADMIN_KEY="your_admin_key"'
        ],
        'notes': [
            '查看组织账单需要Admin权限的API Key',
            '普通API Key无法查看费用信息',
            'API Key以 sk- 开头'
        ]
    },
        'moonshot': {
        'name': 'Moonshot',
        'url': 'https://kimi.moonshot.cn',
        'api_url': 'https://kimi.moonshot.cn/settings/apikeys',
        'env_var': 'MOONSHOT_API_KEY',
        'description': 'Moonshot AI (Kimi)',
        'auth_type': 'API Key',
        'setup_steps': [
            '访问 https://kimi.moonshot.cn 并注册/登录',
            '进入 "设置" → "API Keys"',
            '点击 "创建新的API Key"',
            '复制API Key并设置环境变量: export MOONSHOT_API_KEY="your_api_key"'
        ],
        'notes': [
            'API Key以 sk- 开头',
            '有免费试用额度',
            '支持长文本处理'
        ]
    },
    'volcengine': {
        'name': 'Volcengine',
        'url': 'https://console.volcengine.com',
        'api_url': 'https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey',
        'env_var': 'VOLCENGINE_ACCESS_KEY',
        'env_var_secret': 'VOLCENGINE_SECRET_KEY',
        'description': '字节跳动火山引擎 (企业级云服务)',
        'auth_type': 'SDK',
        'setup_steps': [
            '访问 https://console.volcengine.com 并注册/登录',
            '进入 "火山引擎方舟" 控制台',
            '选择 "API Key 管理"',
            '创建 Access Key 和 Secret Key',
            '设置环境变量:',
            '  export VOLCENGINE_ACCESS_KEY="your_access_key"',
            '  export VOLCENGINE_SECRET_KEY="your_secret_key"'
        ],
        'notes': [
            '需要同时设置ACCESS_KEY和SECRET_KEY',
            '企业级服务，稳定性高',
            '支持多种AI模型'
        ]
    },
    'aliyun': {
        'name': 'Aliyun',
        'url': 'https://account.aliyun.com',
        'api_url': 'https://ram.console.aliyun.com/manage/ak',
        'env_var': 'ALIYUN_ACCESS_KEY_ID',
        'env_var_secret': 'ALIYUN_ACCESS_KEY_SECRET',
        'description': '阿里云',
        'auth_type': 'SDK',
        'setup_steps': [
            '访问 https://ram.console.aliyun.com/manage/ak',
            '使用阿里云账号登录',
            '创建用户并授权',
            '生成 AccessKey ID 和 AccessKey Secret',
            '设置环境变量:',
            '  export ALIYUN_ACCESS_KEY_ID="your_access_key_id"',
            '  export ALIYUN_ACCESS_KEY_SECRET="your_access_key_secret"'
        ],
        'notes': [
            '需要同时设置ACCESS_KEY_ID和ACCESS_KEY_SECRET',
            '使用阿里云官方SDK',
            '支持多种云服务'
        ]
    },
    'tencent': {
        'name': 'Tencent Hunyuan',
        'url': 'https://cloud.tencent.com',
        'api_url': 'https://console.cloud.tencent.com/cam/capi',
        'env_var': 'TENCENT_API_KEY',
        'description': '腾讯混元大模型',
        'auth_type': 'SecretId+SecretKey',
        'setup_steps': [
            '访问 https://console.cloud.tencent.com/cam/capi',
            '使用腾讯云账号登录',
            '创建子用户并授权',
            '生成 SecretId 和 SecretKey',
            '设置环境变量: export TENCENT_API_KEY="SecretId:SecretKey"'
        ],
        'notes': [
            'API Key格式：SecretId:SecretKey',
            '需要腾讯云账号',
            '支持混元大模型'
        ]
    },
        'zhipu': {
        'name': 'Zhipu AI',
        'url': 'https://open.bigmodel.cn',
        'api_url': 'https://open.bigmodel.cn/console/apikey',
        'env_var': 'ZHIPU_API_KEY',
        'description': '智谱AI GLM',
        'auth_type': 'Cookie',
        'setup_steps': [
            '访问 https://open.bigmodel.cn 并注册/登录',
            '完成实名认证',
            '在浏览器中保持登录状态',
            '工具会自动读取cookie进行认证'
        ],
        'notes': [
            '使用浏览器cookie认证',
            '需要保持浏览器登录状态',
            '支持GLM系列模型'
        ]
    }
}

def get_platform_info(platform_name: str) -> Dict[str, Any]:
    """Get platform information"""
    return PLATFORM_INFO.get(platform_name, {})

def format_api_key_error(platform_name: str, env_var: str) -> str:
    """Format helpful API key error message"""
    info = get_platform_info(platform_name)
    
    if not info:
        return f"❌ {platform_name}: API key required. Set {env_var} environment variable."
    
    error_msg = f"""
❌ {info['name']} API Key 未配置

📋 平台信息:
   • 名称: {info['name']}
   • 官网: {info['url']}
   • 认证方式: {info['auth_type']}
   • API管理: {info['api_url']}

🔧 配置步骤:
"""
    
    for i, step in enumerate(info['setup_steps'], 1):
        error_msg += f"   {i}. {step}\n"
    
    # 添加特殊环境变量说明
    if 'env_var_secret' in info:
        error_msg += f"""
   必要的环境变量:
   • export {info['env_var']}="your_value"
   • export {info['env_var_secret']}="your_secret_value"
"""
    else:
        error_msg += f"""
   必要的环境变量:
   • export {info['env_var']}="your_api_key_here"
"""
    
    error_msg += f"""
💡 注意事项:
"""
    for note in info['notes']:
        error_msg += f"   • {note}\n"
    
    error_msg += """
🔄 配置完成后重新运行命令即可
"""
    return error_msg

def format_auth_error(platform_name: str, error_details: str) -> str:
    """Format helpful authentication error message"""
    info = get_platform_info(platform_name)
    
    if not info:
        return f"❌ {platform_name}: Authentication failed - {error_details}"
    
    error_msg = f"""
❌ {info['name']} 认证失败

📋 平台: {info['name']}
🔗 官网: {info['url']}
🔧 认证方式: {info['auth_type']}

🔍 错误详情: {error_details}

💡 解决方案:
   1. 检查环境变量 {info['env_var']} 是否正确设置
   2. 确认 API Key/Token 是否有效且未过期
   3. 验证账户余额是否充足
   4. 检查是否有权限访问相关API
   5. 访问 {info['api_url']} 重新获取认证信息

📝 环境变量检查:
   • echo ${info['env_var']}  # 检查是否已设置
   • export {info['env_var']}="your_api_key"  # 重新设置

🔗 快速链接:
   • API管理: {info['api_url']}
   • 官网: {info['url']}
"""
    return error_msg

def format_network_error(platform_name: str, error_details: str) -> str:
    """Format helpful network error message"""
    info = get_platform_info(platform_name)
    
    if not info:
        return f"❌ {platform_name}: Network error - {error_details}"
    
    error_msg = f"""
❌ {info['name']} 网络连接失败

📋 平台: {info['name']}
🔗 官网: {info['url']}

🔍 错误详情: {error_details}

💡 解决方案:
   1. 检查网络连接
   2. 确认 {info['url']} 可以访问
   3. 检查防火墙设置
   4. 稍后重试

⏱️  超时设置: 10秒
"""
    return error_msg

def get_setup_guide() -> str:
    """Get complete setup guide for all platforms"""
    guide = """
🚀 LLM Balance Checker 完整配置指南

====================================

📋 支持的平台 (13个):
====================================

🌍 国际平台:
"""
    
    # Popular platforms first
    popular_platforms = ['openai']
    
    for platform in popular_platforms:
        info = get_platform_info(platform)
        if info:
            guide += f"""
   • {info['name']} ({platform})
     官网: {info['url']}
     认证方式: {info['auth_type']}
     环境变量: {info['env_var']}
"""
    
    guide += """

🇨🇳 中国平台:
"""
    
    chinese_platforms = ['deepseek', 'moonshot', 'volcengine', 'aliyun', 'tencent', 'zhipu']
    
    for platform in chinese_platforms:
        info = get_platform_info(platform)
        if info:
            guide += f"""
   • {info['name']} ({platform})
     官网: {info['url']}
     认证方式: {info['auth_type']}
     环境变量: {info['env_var']}
"""
    
    guide += """

🔧 详细配置指南:
====================================

🌟 DeepSeek (推荐新手):
   1. 访问: https://platform.deepseek.com
   2. 注册并完成邮箱验证
   3. 进入 API Keys 页面
   4. 点击 "Create API Key"
   5. 复制 sk- 开头的密钥
   6. 设置: export DEEPSEEK_API_KEY="sk-your-key"

🌟 OpenAI (需要Admin权限):
   1. 访问: https://platform.openai.com
   2. 进入 API Keys 页面
   3. 创建新的 secret key
   4. 选择 Admin 权限（查看账单需要）
   5. 设置: export OPENAI_ADMIN_KEY="sk-your-key"

🌟 Moonshot (Kimi):
   1. 访问: https://kimi.moonshot.cn
   2. 注册并登录
   3. 进入设置 → API Keys
   4. 创建新的API Key
   5. 设置: export MOONSHOT_API_KEY="sk-your-key"

🇨🇳 火山引擎 (企业级):
   1. 访问: https://console.volcengine.com
   2. 进入火山引擎方舟控制台
   3. 创建 Access Key 和 Secret Key
   4. 设置: 
      export VOLCENGINE_ACCESS_KEY="your_access_key"
      export VOLCENGINE_SECRET_KEY="your_secret_key"

🇨🇳 智谱AI (Cookie认证):
   1. 访问: https://open.bigmodel.cn
   2. 注册并完成实名认证
   3. 在浏览器中保持登录状态
   4. 工具会自动读取cookie

🔧 常用命令:
====================================
• llm-balance list              # 查看所有平台
• llm-balance enable <platform> # 启用平台
• llm-balance disable <platform> # 禁用平台
• llm-balance cost              # 检查所有平台余额
• llm-balance cost --platform=<platform> # 检查指定平台
• llm-balance rates             # 查看汇率信息
• llm-balance set-browser <browser> # 设置全局浏览器

💡 使用技巧:
====================================
• 支持多货币显示 (USD, EUR, CNY等)
• 自动汇率转换
• 错误信息包含详细的解决方案
• 支持浏览器cookie认证
• 企业级SDK认证支持

🔗 故障排除:
====================================
• 网络问题: 检查防火墙和代理设置
• 认证失败: 重新获取API Key
• 权限问题: 确认API Key权限
• 余额问题: 检查账户余额和充值

📝 完整文档:
• GitHub: https://github.com/your-repo/llm-balance
• Issues: https://github.com/your-repo/llm-balance/issues
"""
    
    return guide

def format_platform_summary() -> str:
    """Format platform summary with quick setup commands"""
    summary = """
📊 LLM Balance Checker 平台概览

====================================

✅ 已启用平台:
"""
    
    # Check enabled platforms
    enabled_platforms = []
    for platform_name, info in PLATFORM_INFO.items():
        env_var = info['env_var']
        if os.getenv(env_var):
            enabled_platforms.append(platform_name)
    
    if enabled_platforms:
        for platform in enabled_platforms:
            info = get_platform_info(platform)
            summary += f"   • {info['name']} ({platform})\n"
    else:
        summary += "   暂无已启用平台\n"
    
    summary += """

🔧 快速配置命令:
"""
    
    # Show setup commands for popular platforms
    for platform in ['deepseek', 'openai']:
        info = get_platform_info(platform)
        if info and not os.getenv(info['env_var']):
            summary += f"""
   # {info['name']}
   export {info['env_var']}="your_api_key"
   llm-balance enable {platform}
"""
    
    summary += """

📝 完整配置指南:
   llm-balance setup-guide

🔗 相关命令:
   llm-balance list     # 查看所有平台
   llm-balance cost     # 检查余额
   llm-balance rates    # 查看汇率
"""
    
    return summary