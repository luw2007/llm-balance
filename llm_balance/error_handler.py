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
        'setup_steps': platform_info.setup_steps if platform_info.setup_steps else ['请参考平台官方文档进行配置'],
        'notes': platform_info.notes if platform_info.notes else ['请参考平台官方文档'],
        'url': platform_info.official_url,
        'api_url': platform_info.api_management_url
    }
    
    return info

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
    platform_names = registry.list_platforms()
    for name in platform_names:
        platform_info = registry.get_platform(name)
        if platform_info and platform_info.env_var and os.getenv(platform_info.env_var):
            enabled.append(name)
    return enabled

def get_setup_guide() -> str:
    """获取完整的设置指南"""
    guide = """
🚀 LLM Balance Checker 完整配置指南

====================================

📋 支持的平台:
====================================
"""
    
    platforms = registry.list_platforms()
    for platform in platforms:
        info = get_platform_info(platform)
        if info:
            env_var_display = info['env_var']
            if not env_var_display:
                if info['auth_type'] == 'sdk':
                    env_var_display = 'SDK配置 (见指南)'
                elif info['auth_type'] == 'cookie':
                    env_var_display = '自动读取Cookie'
                else:
                    env_var_display = '无需环境变量'
                    
            guide += f"""
   • {info['name']} ({platform})
     官网: {info['url']}
     认证方式: {info['auth_type']}
     环境变量: {env_var_display}
"""
    
    guide += """
🔧 详细配置指南:
====================================
"""
    
    # 仅针对几个主要平台显示详细指南
    featured_platforms = ['deepseek', 'moonshot', 'volcengine', 'zhipu']
    for platform in featured_platforms:
        info = get_platform_info(platform)
        if info:
            guide += f"\n🌟 {info['name']}:\n"
            guide += _format_list(info['setup_steps']) + "\n"
    
    guide += """
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