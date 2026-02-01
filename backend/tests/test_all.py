#!/usr/bin/env python3
"""
运行所有单元测试
"""
import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入测试模块
from backend.tests.test_tts_service import TestTTSService, TestTTSServiceIntegration
from backend.tests.test_llm_service import TestLLMService, TestLLMServicePrompts, TestLLMServiceIntegration


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestTTSService))
    suite.addTests(loader.loadTestsFromTestCase(TestTTSServiceIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMService))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMServicePrompts))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMServiceIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    print('\n' + '='*70)
    print('测试总结')
    print('='*70)
    print(f'运行测试数: {result.testsRun}')
    print(f'成功: {result.testsRun - len(result.failures) - len(result.errors)}')
    print(f'失败: {len(result.failures)}')
    print(f'错误: {len(result.errors)}')
    print('='*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)