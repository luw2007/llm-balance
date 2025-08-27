"""
优化的错误处理 - 减少重复代码
"""

import os
from typing import Dict, Any, List, Optional
from .platform_handlers.registry import registry

# 平台信息配置 - 现在与注册表同步
def get_platform_info(platform_name: str) -> Dict[str, Any]:
    """获取平台信息 - 从注册表中获取"""
    platform_info = registry.get_platform(platform_name)
    if not platform_info:
        return {}
    
    # 转换为旧格式以保持兼容性
    info = {
        'name': platform_info.display_name,
        'description': platform_info.description,
        'auth_type': platform_info.auth_type,
        'env_var': platform_info.env_var,
        'setup_steps': _get_setup_steps(platform_name),
        'notes': _get_platform_notes(platform_name),
        'url': _get_platform_url(platform_name),
        'api_url': _get_api_url(platform_name)
    }
    
    return info

def _get_setup_steps(platform_name: str) -> List[str]:
    """获取平台设置步骤"""
    steps_map = {
        'deepseek': [
            '访问 https://platform.deepseek.com 并注册/登录',
            '进入 "API Keys" 页面',
            '点击 "Create API Key" 创建新的API Key',
            '复制生成的API Key（格式：sk-xxxxxxxx）',
            '设置环境变量: export DEEPSEEK_API_KEY="your_api_key"'
        ],
        'moonshot': [
            '访问 https://www.kimi.com 并注册/登录',
            '进入 "设置" → "API Keys"',
            '点击 "创建新的API Key"',
            '复制API Key并设置环境变量: export MOONSHOT_API_KEY="your_api_key"'
        ],
        'volcengine': [
            '访问 https://console.volcengine.com 并注册/登录',
            '进入控制台后选择相应服务',
            '在 "访问控制" 中创建 Access Key 和 Secret Key',
            '设置环境变量:',
            '  export VOLCENGINE_ACCESS_KEY="your_access_key"',
            '  export VOLCENGINE_SECRET_KEY="your_secret_key"'
        ],
        'aliyun': [
            '访问 https://ram.console.aliyun.com/manage/ak',
            '使用阿里云账号登录',
            '创建用户并授权',
            '生成 AccessKey ID 和 AccessKey Secret',
            '设置环境变量:',
            '  export ALIYUN_ACCESS_KEY_ID="your_access_key_id"',
            '  export ALIYUN_ACCESS_KEY_SECRET="your_access_key_secret"'
        ],
        'tencent': [
            '访问 https://console.cloud.tencent.com/cam/capi',
            '使用腾讯云账号登录',
            '创建子用户并授权',
            '生成 SecretId 和 SecretKey',
            '设置环境变量: export TENCENT_API_KEY="SecretId:SecretKey"'
        ],
        'zhipu': [
            '访问 https://open.bigmodel.cn 并注册/登录',
            '完成实名认证',
            '在浏览器中保持登录状态',
            '工具会自动读取cookie进行认证'
        ]
    }
    return steps_map.get(platform_name, ['请参考平台官方文档进行配置'])

def _get_platform_notes(platform_name: str) -> List[str]:
    """获取平台注意事项"""
    notes_map = {
        'deepseek': [
            'API Key以 sk- 开头',
            '免费额度有限，超额需要付费',
            '支持多种模型：DeepSeek-V2, DeepSeek-Coder等'
        ],
        'moonshot': [
            'API Key以 sk- 开头',
            '有免费试用额度',
            '支持长文本处理'
        ],
        'volcengine': [
            '需要同时设置ACCESS_KEY和SECRET_KEY',
            '企业级服务，稳定性高',
            '支持多种AI模型'
        ],
        'aliyun': [
            '需要同时设置ACCESS_KEY_ID和ACCESS_KEY_SECRET',
            '使用阿里云官方SDK',
            '支持多种云服务'
        ],
        'tencent': [
            'API Key格式：SecretId:SecretKey',
            '需要腾讯云账号',
            '支持混元大模型'
        ],
        'zhipu': [
            '使用浏览器cookie认证',
            '需要保持浏览器登录状态',
            '支持GLM系列模型'
        ]
    }
    return notes_map.get(platform_name, ['请参考平台官方文档'])

def _get_platform_url(platform_name: str) -> str:
    """获取平台官网URL"""
    url_map = {
        'deepseek': 'https://platform.deepseek.com',
        'moonshot': 'https://www.kimi.com',
        'volcengine': 'https://console.volcengine.com',
        'aliyun': 'https://account.aliyun.com',
        'tencent': 'https://cloud.tencent.com',
        'zhipu': 'https://open.bigmodel.cn'
    }
    return url_map.get(platform_name, '')

def _get_api_url(platform_name: str) -> str:
    """获取平台API管理URL"""
    api_url_map = {
        'deepseek': 'https://platform.deepseek.com/api_keys',
        'moonshot': 'https://www.kimi.com/settings/apikeys',
        'volcengine': 'https://console.volcengine.com',
        'aliyun': 'https://ram.console.aliyun.com/manage/ak',
        'tencent': 'https://console.cloud.tencent.com/cam/capi',
        'zhipu': 'https://open.bigmodel.cn/console/apikey'
    }
    return api_url_map.get(platform_name, '')

# 错误消息模板
ERROR_TEMPLATES = {
    'api_key': """❌ {platform_name} API Key 未配置

📋 平台信息:
   • 名称: {name}
   • 官网: {url}
   • 认证方式: {auth_type}
   • API管理: {api_url}

🔧 配置步骤:
{setup_steps}

{env_vars_section}

💡 注意事项:
{notes}

🔄 配置完成后重新运行命令即可""",
    
    'auth': """❌ {platform_name} 认证失败

📋 平台: {name}
🔗 官网: {url}
🔧 认证方式: {auth_type}

🔍 错误详情: {error_details}

💡 解决方案:
   1. 检查环境变量 {env_var} 是否正确设置
   2. 确认 API Key/Token 是否有效且未过期
   3. 验证账户余额是否充足
   4. 检查是否有权限访问相关API
   5. 访问 {api_url} 重新获取认证信息

📝 环境变量检查:
   • echo ${env_var}  # 检查是否已设置
   • export {env_var}="your_api_key"  # 重新设置

🔗 快速链接:
   • API管理: {api_url}
   • 官网: {url}""",
    
    'network': """❌ {platform_name} 网络连接失败

📋 平台: {name}
🔗 官网: {url}

🔍 错误详情: {error_details}

💡 解决方案:
   1. 检查网络连接
   2. 确认 {url} 可以访问
   3. 检查防火墙设置
   4. 稍后重试

⏱️  超时设置: 10秒"""
}


def _format_list(items: List[str], prefix: str = "   ") -> str:
    """格式化列表为字符串"""
    return '\n'.join(f"{prefix}{i+1}. {item}" for i, item in enumerate(items))

def _format_env_vars(info: Dict[str, Any]) -> str:
    """格式化环境变量部分"""
    if 'env_var_secret' in info:
        return f"""
   必要的环境变量:
   • export {info['env_var']}="your_value"
   • export {info['env_var_secret']}="your_secret_value\""""
    else:
        return f"""
   必要的环境变量:
   • export {info['env_var']}="your_api_key_here\""""

def _format_notes(notes: List[str]) -> str:
    """格式化注意事项"""
    return '\n'.join(f"   • {note}" for note in notes)

def _format_error_message(template_key: str, platform_name: str, **kwargs) -> str:
    """统一的错误消息格式化函数"""
    info = get_platform_info(platform_name)
    
    if not info:
        return f"❌ {platform_name}: Error occurred - {kwargs.get('error_details', 'Unknown error')}"
    
    # 准备模板变量
    template_vars = {
        'platform_name': info['name'],
        'name': info['name'],
        'url': info['url'],
        'auth_type': info['auth_type'],
        'api_url': info['api_url'],
        'env_var': info['env_var'],
        'setup_steps': _format_list(info['setup_steps']),
        'env_vars_section': _format_env_vars(info),
        'notes': _format_notes(info['notes']),
        **kwargs
    }
    
    return ERROR_TEMPLATES[template_key].format(**template_vars)

def format_api_key_error(platform_name: str, env_var: str) -> str:
    """格式化API密钥错误消息"""
    return _format_error_message('api_key', platform_name)

def format_auth_error(platform_name: str, error_details: str) -> str:
    """格式化认证错误消息"""
    return _format_error_message('auth', platform_name, error_details=error_details)

def format_network_error(platform_name: str, error_details: str) -> str:
    """格式化网络错误消息"""
    return _format_error_message('network', platform_name, error_details=error_details)

def _format_platform_list(platforms: List[str], title: str = "平台列表") -> str:
    """格式化平台列表"""
    if not platforms:
        return f"   暂无{title}"
    
    result = []
    for platform in platforms:
        info = get_platform_info(platform)
        if info:
            result.append(f"   • {info['name']} ({platform})")
    
    return '\n'.join(result)

def _get_enabled_platforms() -> List[str]:
    """获取已启用的平台列表"""
    enabled = []
    platforms = registry.list_platforms()
    for platform_name, platform_info in platforms.items():
        if platform_info.env_var and os.getenv(platform_info.env_var):
            enabled.append(platform_name)
    return enabled

def get_setup_guide() -> str:
    """获取完整的设置指南"""
    guide = """
🚀 LLM Balance Checker 完整配置指南

====================================

📋 支持的平台:
====================================

🌍 国际平台:
"""
    
    # 国际平台
    international_platforms = ['openai']
    for platform in international_platforms:
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
    
    # 中国平台
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


🌟 Moonshot (Kimi):
   1. 访问: https://www.kimi.com
   2. 注册并登录
   3. 进入设置 → API Keys
   4. 创建新的API Key
   5. 设置: export MOONSHOT_API_KEY="sk-your-key"

🇨🇳 火山引擎 (企业级):
   1. 访问: https://console.volcengine.com
   2. 进入控制台后选择相应服务
   3. 在访问控制中创建 Access Key 和 Secret Key
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
    """格式化平台概览"""
    enabled_platforms = _get_enabled_platforms()
    
    summary = f"""
📊 LLM Balance Checker 平台概览

====================================

✅ 已启用平台:
{_format_platform_list(enabled_platforms, "已启用平台")}

🔧 快速配置命令:
"""
    
    # 显示推荐平台的配置命令
    for platform in ['deepseek']:
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