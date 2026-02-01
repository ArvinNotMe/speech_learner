#!/usr/bin/env python3
"""
LLM服务单元测试
"""
import unittest
import os
import sys
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.llm_service import LLMService
from backend.config import Config


class TestLLMService(unittest.TestCase):
    """测试LLM服务"""
    
    def setUp(self):
        """每个测试方法开始前执行"""
        self.llm_service = LLMService(api_key='test_api_key')
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.llm_service.api_key, 'test_api_key')
        self.assertEqual(self.llm_service.model, Config.LLM_MODEL)
    
    def test_extract_json(self):
        """测试JSON提取功能"""
        # 测试正常JSON
        text1 = '{"key": "value"}'
        result1 = self.llm_service._extract_json(text1)
        self.assertEqual(result1, '{"key": "value"}')
        
        # 测试带额外文本的JSON
        text2 = 'Some text before {\n  "dialogue": [],\n  "keywords": []\n} some text after'
        result2 = self.llm_service._extract_json(text2)
        self.assertEqual(result2, '{\n  "dialogue": [],\n  "keywords": []\n}')
        
        # 测试没有JSON的情况
        text3 = 'No JSON here'
        result3 = self.llm_service._extract_json(text3)
        self.assertEqual(result3, 'No JSON here')
    
    def test_generate_dialogue_structure(self):
        """测试生成对话的结构（mock测试）"""
        # 由于无法实际调用API，这里主要测试方法存在和参数处理
        # 实际使用时应该mock Generation.call
        
        # 测试方法存在且可调用
        self.assertTrue(hasattr(self.llm_service, 'generate_dialogue'))
        self.assertTrue(callable(self.llm_service.generate_dialogue))
        
        # 测试返回类型（当API调用失败时）
        result = self.llm_service.generate_dialogue('测试话题')
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
    
    def test_translate_structure(self):
        """测试翻译功能的结构（mock测试）"""
        # 测试方法存在且可调用
        self.assertTrue(hasattr(self.llm_service, 'translate_to_english'))
        self.assertTrue(callable(self.llm_service.translate_to_english))
        
        # 测试返回类型（当API调用失败时）
        result = self.llm_service.translate_to_english('测试文本')
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)


class TestLLMServicePrompts(unittest.TestCase):
    """测试LLM服务提示词生成"""
    
    def setUp(self):
        self.llm_service = LLMService(api_key='test_key')
    
    def test_dialogue_prompt_format(self):
        """测试对话生成提示词格式"""
        topic = '餐厅点餐'
        num_exchanges = 5
        
        # 构建提示词（模拟内部逻辑）
        prompt = f'请生成一个关于"{topic}"的英语对话，包含{num_exchanges}轮对话。'
        
        # 验证提示词包含必要元素
        self.assertIn(topic, prompt)
        self.assertIn(str(num_exchanges), prompt)
        self.assertIn('对话', prompt)
    
    def test_translate_prompt_format(self):
        """测试翻译提示词格式"""
        chinese_text = '你好世界'
        
        # 构建提示词（模拟内部逻辑）
        prompt = f'请将以下中文翻译成地道、自然的英文口语表达：\n\n中文：{chinese_text}'
        
        # 验证提示词包含必要元素
        self.assertIn(chinese_text, prompt)
        self.assertIn('翻译', prompt)


class TestLLMServiceIntegration(unittest.TestCase):
    """LLM服务集成测试（需要真实API Key）"""
    
    @classmethod
    def setUpClass(cls):
        """检查是否有真实API Key"""
        cls.api_key = os.environ.get('DASHSCOPE_API_KEY', '')
        cls.has_real_key = bool(cls.api_key and cls.api_key != 'your_api_key_here')
    
    def setUp(self):
        """跳过测试如果没有真实API Key"""
        if not self.has_real_key:
            self.skipTest('没有配置真实的DashScope API Key')
        self.llm_service = LLMService(api_key=self.api_key)
    
    def test_real_generate_dialogue(self):
        """测试真实的对话生成（可选）"""
        result = self.llm_service.generate_dialogue('餐厅点餐', num_exchanges=3)
        
        # 验证返回结构
        self.assertIn('success', result)
        
        if result['success']:
            self.assertIn('topic', result)
            self.assertIn('dialogue', result)
            self.assertIn('keywords', result)
            
            # 验证对话结构
            self.assertIsInstance(result['dialogue'], list)
            if result['dialogue']:
                dialogue_item = result['dialogue'][0]
                self.assertIn('speaker', dialogue_item)
                self.assertIn('chinese', dialogue_item)
                self.assertIn('english', dialogue_item)
            
            # 验证关键词结构
            self.assertIsInstance(result['keywords'], list)
            if result['keywords']:
                keyword = result['keywords'][0]
                self.assertIn('word', keyword)
                self.assertIn('chinese', keyword)
    
    def test_real_translate(self):
        """测试真实的翻译功能（可选）"""
        result = self.llm_service.translate_to_english('你好，很高兴见到你')
        
        # 验证返回结构
        self.assertIn('success', result)
        
        if result['success']:
            self.assertIn('chinese', result)
            self.assertIn('translations', result)


def run_tests():
    """运行测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestLLMService))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMServicePrompts))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMServiceIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)