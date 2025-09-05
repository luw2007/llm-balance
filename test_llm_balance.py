#!/usr/bin/env python3
"""
llm-balance 自动化测试脚本
测试 cost 和 package 功能，确保各平台正常工作
"""

import subprocess
import json
import sys
import os
import re
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any
import argparse

class TestResult:
    """测试结果类"""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.success = False
        self.error_message = ""
        self.execution_time = 0
        self.output = ""
        self.platforms_tested = []
        self.platforms_passed = []
        self.platforms_failed = []
    
    def add_platform_result(self, platform: str, success: bool, error: str = ""):
        """添加平台测试结果"""
        if success:
            self.platforms_passed.append(platform)
        else:
            self.platforms_failed.append((platform, error))
        self.platforms_tested.append(platform)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'test_name': self.test_name,
            'success': self.success,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'platforms_tested': len(self.platforms_tested),
            'platforms_passed': len(self.platforms_passed),
            'platforms_failed': len(self.platforms_failed),
            'failed_platforms': self.platforms_failed,
            'output_summary': self.output[:200] + "..." if len(self.output) > 200 else self.output
        }

class LLMBalanceTester:
    """llm-balance 自动化测试器"""
    
    def __init__(self, verbose: bool = False, fail_fast: bool = False):
        self.verbose = verbose
        self.fail_fast = fail_fast
        self.test_results = []
        self.start_time = datetime.now()
        
        # 支持的输出格式
        self.output_formats = ['table', 'json', 'total', 'markdown']
        
        # 需要测试的平台
        self.expected_platforms = [
            'volcengine', 'zhipu', 'deepseek', 'moonshot', 
            'siliconflow', 'tencent', 'aliyun'
        ]
        
        # 环境变量检查
        self.required_env_vars = {
            'volcengine': ['VOLCENGINE_ACCESS_KEY', 'VOLCENGINE_SECRET_KEY'],
            'zhipu': [],
            'deepseek': ['DEEPSEEK_API_KEY'],
            'moonshot': ['MOONSHOT_API_KEY'],
            'siliconflow': ['SILICONFLOW_API_KEY'],
            'tencent': ['TENCENT_API_KEY'],
            'aliyun': ['ALIYUN_ACCESS_KEY_ID', 'ALIYUN_ACCESS_KEY_SECRET']
        }
    
    def log(self, message: str):
        """日志输出"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def run_command(self, command: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
        """运行命令并返回结果"""
        try:
            start_time = time.time()
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8'
            )
            execution_time = time.time() - start_time
            
            success = result.returncode == 0
            output = result.stdout
            error = result.stderr
            
            return success, output, error
            
        except subprocess.TimeoutExpired:
            return False, "", f"命令超时 ({timeout}秒)"
        except Exception as e:
            return False, "", f"命令执行失败: {str(e)}"
    
    def check_environment(self) -> TestResult:
        """检查测试环境"""
        result = TestResult("环境检查")
        start_time = time.time()
        
        try:
            # 检查 llm-balance 命令是否可用
            success, output, error = self.run_command(['llm-balance', '--help'])
            if not success:
                result.error_message = f"llm-balance 命令不可用: {error}"
                result.execution_time = time.time() - start_time
                return result
            
            # 检查环境变量
            missing_env_vars = []
            for platform, env_vars in self.required_env_vars.items():
                for env_var in env_vars:
                    if not os.getenv(env_var):
                        missing_env_vars.append(f"{platform}: {env_var}")
            
            if missing_env_vars:
                result.error_message = f"缺少环境变量: {', '.join(missing_env_vars)}"
                if self.verbose:
                    self.log(f"警告: 缺少环境变量 - {missing_env_vars}")
                # 不标记为失败，只记录警告
            
            result.success = True
            result.output = output
            
        except Exception as e:
            result.error_message = f"环境检查失败: {str(e)}"
        
        result.execution_time = time.time() - start_time
        return result
    
    def test_cost_command(self, format_type: str = 'table') -> TestResult:
        """测试 cost 命令"""
        result = TestResult(f"cost 命令测试 ({format_type})")
        start_time = time.time()
        
        try:
            command = ['llm-balance', 'cost', '--format', format_type]
            success, output, error = self.run_command(command)
            
            if not success:
                result.error_message = f"cost 命令失败: {error}"
                result.execution_time = time.time() - start_time
                return result
            
            result.output = output
            
            # 解析输出，检查平台
            if format_type == 'json':
                self._parse_cost_json_output(result, output)
            elif format_type == 'table':
                self._parse_cost_table_output(result, output)
            elif format_type == 'total':
                self._parse_cost_total_output(result, output)
            elif format_type == 'markdown':
                self._parse_cost_markdown_output(result, output)
            
            result.success = len(result.platforms_failed) == 0
            
            if self.verbose:
                self.log(f"cost ({format_type}): 通过 {len(result.platforms_passed)}/{len(result.platforms_tested)} 个平台")
            
        except Exception as e:
            result.error_message = f"cost 命令测试异常: {str(e)}"
        
        result.execution_time = time.time() - start_time
        return result
    
    def test_package_command(self, format_type: str = 'table') -> TestResult:
        """测试 package 命令"""
        result = TestResult(f"package 命令测试 ({format_type})")
        start_time = time.time()
        
        try:
            command = ['llm-balance', 'package', '--format', format_type]
            success, output, error = self.run_command(command)
            
            if not success:
                result.error_message = f"package 命令失败: {error}"
                result.execution_time = time.time() - start_time
                return result
            
            result.output = output
            
            # 解析输出，检查平台
            if format_type == 'json':
                self._parse_package_json_output(result, output)
            elif format_type == 'table':
                self._parse_package_table_output(result, output)
            elif format_type == 'total':
                self._parse_package_total_output(result, output)
            elif format_type == 'markdown':
                self._parse_package_markdown_output(result, output)
            
            result.success = len(result.platforms_failed) == 0
            
            if self.verbose:
                self.log(f"package ({format_type}): 通过 {len(result.platforms_passed)}/{len(result.platforms_tested)} 个平台")
            
        except Exception as e:
            result.error_message = f"package 命令测试异常: {str(e)}"
        
        result.execution_time = time.time() - start_time
        return result
    
    def test_specific_platform(self, platform: str) -> TestResult:
        """测试特定平台"""
        result = TestResult(f"平台测试: {platform}")
        start_time = time.time()
        
        try:
            # 测试 cost 命令
            success, output, error = self.run_command(['llm-balance', 'cost', '--platform', platform])
            if success:
                result.add_platform_result(platform, True)
                result.output += f"cost: {output}\n"
            else:
                result.add_platform_result(platform, False, f"cost 失败: {error}")
                result.output += f"cost: {error}\n"
            
            # 测试 package 命令
            success, output, error = self.run_command(['llm-balance', 'package', '--platform', platform])
            if success:
                result.add_platform_result(platform, True)
                result.output += f"package: {output}\n"
            else:
                result.add_platform_result(platform, False, f"package 失败: {error}")
                result.output += f"package: {error}\n"
            
            result.success = len(result.platforms_failed) == 0
            
            if self.verbose:
                status = "通过" if result.success else "失败"
                self.log(f"平台 {platform}: {status}")
            
        except Exception as e:
            result.error_message = f"平台 {platform} 测试异常: {str(e)}"
        
        result.execution_time = time.time() - start_time
        return result
    
    def _parse_cost_json_output(self, result: TestResult, output: str):
        """解析 cost JSON 输出"""
        try:
            data = json.loads(output)
            if isinstance(data, list):
                for item in data:
                    platform = item.get('platform', 'unknown')
                    if item.get('balance') is not None:
                        result.add_platform_result(platform, True)
                    else:
                        result.add_platform_result(platform, False, "余额为空")
        except json.JSONDecodeError:
            result.error_message = "JSON 解析失败"
    
    def _parse_cost_table_output(self, result: TestResult, output: str):
        """解析 cost 表格输出"""
        lines = output.strip().split('\n')
        for line in lines:
            if line.strip() and not line.startswith('-') and not line.startswith('Platform'):
                # 简单的行解析，查找平台名称
                for platform in self.expected_platforms:
                    if platform.lower() in line.lower():
                        if 'No data' not in line and 'error' not in line.lower():
                            result.add_platform_result(platform, True)
                        else:
                            result.add_platform_result(platform, False, "无数据或错误")
                        break
    
    def _parse_cost_total_output(self, result: TestResult, output: str):
        """解析 cost 总计输出"""
        # total 格式只显示总计，假设成功就是通过
        result.add_platform_result('total', True)
    
    def _parse_cost_markdown_output(self, result: TestResult, output: str):
        """解析 cost markdown 输出"""
        # 与表格输出类似
        self._parse_cost_table_output(result, output)
    
    def _parse_package_json_output(self, result: TestResult, output: str):
        """解析 package JSON 输出"""
        try:
            data = json.loads(output)
            if isinstance(data, dict) and 'platform' in data:
                platform = data['platform']
                models = data.get('models', [])
                if models:
                    result.add_platform_result(platform, True)
                else:
                    result.add_platform_result(platform, False, "无模型数据")
        except json.JSONDecodeError:
            result.error_message = "JSON 解析失败"
    
    def _parse_package_table_output(self, result: TestResult, output: str):
        """解析 package 表格输出"""
        lines = output.strip().split('\n')
        for line in lines:
            if line.strip() and not line.startswith('-') and not line.startswith('Platform'):
                for platform in self.expected_platforms:
                    if platform.lower() in line.lower():
                        if 'No data' not in line:
                            result.add_platform_result(platform, True)
                        else:
                            result.add_platform_result(platform, False, "无数据")
                        break
    
    def _parse_package_total_output(self, result: TestResult, output: str):
        """解析 package 总计输出"""
        # total 格式只显示总计，假设成功就是通过
        result.add_platform_result('total', True)
    
    def _parse_package_markdown_output(self, result: TestResult, output: str):
        """解析 package markdown 输出"""
        # 与表格输出类似
        self._parse_package_table_output(result, output)
    
    def run_all_tests(self) -> List[TestResult]:
        """运行所有测试"""
        self.log("开始运行 llm-balance 自动化测试...")
        
        # 环境检查
        env_result = self.check_environment()
        self.test_results.append(env_result)
        
        if not env_result.success and "命令不可用" in env_result.error_message:
            self.log("❌ 环境检查失败，停止测试")
            return self.test_results
        
        # 测试 cost 命令
        for format_type in self.output_formats:
            cost_result = self.test_cost_command(format_type)
            self.test_results.append(cost_result)
            
            if self.fail_fast and not cost_result.success:
                self.log(f"❌ cost ({format_type}) 测试失败，停止测试")
                break
        
        # 测试 package 命令
        for format_type in self.output_formats:
            package_result = self.test_package_command(format_type)
            self.test_results.append(package_result)
            
            if self.fail_fast and not package_result.success:
                self.log(f"❌ package ({format_type}) 测试失败，停止测试")
                break
        
        # 测试特定平台（如果前面的测试都通过）
        if all(r.success for r in self.test_results[1:]):  # 跳过环境检查
            self.log("测试特定平台...")
            for platform in self.expected_platforms:
                platform_result = self.test_specific_platform(platform)
                self.test_results.append(platform_result)
                
                if self.fail_fast and not platform_result.success:
                    self.log(f"❌ 平台 {platform} 测试失败，停止测试")
                    break
        
        return self.test_results
    
    def generate_report(self) -> str:
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        
        total_time = sum(r.execution_time for r in self.test_results)
        
        report = []
        report.append("=" * 60)
        report.append("🧪 llm-balance 自动化测试报告")
        report.append("=" * 60)
        report.append(f"测试时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"总测试数: {total_tests}")
        report.append(f"通过: {passed_tests}")
        report.append(f"失败: {failed_tests}")
        report.append(f"总耗时: {total_time:.2f} 秒")
        report.append(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        report.append("")
        
        # 详细结果
        report.append("📋 详细测试结果:")
        report.append("-" * 40)
        
        for result in self.test_results:
            status = "✅ 通过" if result.success else "❌ 失败"
            report.append(f"{status} {result.test_name}")
            report.append(f"   耗时: {result.execution_time:.2f}s")
            
            if result.error_message:
                report.append(f"   错误: {result.error_message}")
            
            if result.platforms_tested:
                report.append(f"   平台: {len(result.platforms_passed)}/{len(result.platforms_tested)} 通过")
                
                if result.platforms_failed:
                    for platform, error in result.platforms_failed:
                        report.append(f"   ❌ {platform}: {error}")
            
            report.append("")
        
        # 建议
        if failed_tests > 0:
            report.append("💡 建议:")
            report.append("- 检查环境变量配置")
            report.append("- 确认网络连接正常")
            report.append("- 验证 API 密钥有效性")
            report.append("- 查看详细错误信息进行针对性修复")
        
        return "\n".join(report)
    
    def save_json_report(self, filename: str = None):
        """保存 JSON 格式报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"llm_balance_test_report_{timestamp}.json"
        
        report_data = {
            'test_run_info': {
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_tests': len(self.test_results),
                'passed_tests': sum(1 for r in self.test_results if r.success),
                'failed_tests': len(self.test_results) - sum(1 for r in self.test_results if r.success)
            },
            'test_results': [r.to_dict() for r in self.test_results]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        self.log(f"📄 JSON 报告已保存: {filename}")
        return filename

def main():
    parser = argparse.ArgumentParser(description='llm-balance 自动化测试脚本')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--fail-fast', '-f', action='store_true', help='遇到失败立即停止')
    parser.add_argument('--json-report', action='store_true', help='生成 JSON 报告')
    parser.add_argument('--platforms', nargs='+', help='只测试指定平台')
    
    args = parser.parse_args()
    
    # 创建测试器
    tester = LLMBalanceTester(verbose=args.verbose, fail_fast=args.fail_fast)
    
    # 运行测试
    results = tester.run_all_tests()
    
    # 生成报告
    report = tester.generate_report()
    print(report)
    
    # 保存 JSON 报告
    if args.json_report:
        tester.save_json_report()
    
    # 返回适当的退出码
    success_count = sum(1 for r in results if r.success)
    total_count = len(results)
    
    if success_count == total_count:
        print("🎉 所有测试通过！")
        sys.exit(0)
    else:
        print(f"⚠️  {total_count - success_count} 个测试失败")
        sys.exit(1)

if __name__ == "__main__":
    main()