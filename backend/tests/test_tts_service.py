#!/usr/bin/env python3
"""
TTS服务单元测试
"""
import unittest
import os
import sys
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.tts_service import TTSService
from backend.config import Config


class TestTTSService(unittest.TestCase):
    """测试TTS服务"""
    
    @classmethod
    def setUpClass(cls):
        """测试类开始前执行"""
        # 创建临时目录用于测试
        cls.test_dir = tempfile.mkdtemp()
        cls.original_audio_dir = Config.AUDIO_DIR
        Config.AUDIO_DIR = cls.test_dir
    
    @classmethod
    def tearDownClass(cls):
        """测试类结束后执行"""
        # 恢复原始配置并清理临时目录
        Config.AUDIO_DIR = cls.original_audio_dir
        shutil.rmtree(cls.test_dir, ignore_errors=True)
    
    def setUp(self):
        """每个测试方法开始前执行"""
        # 使用测试API Key（实际测试中会被mock）
        self.tts_service = TTSService(api_key='test_api_key')
    
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.tts_service.api_key, 'test_api_key')
        self.assertEqual(self.tts_service.model, Config.TTS_MODEL)
        self.assertEqual(self.tts_service.sample_rate, Config.TTS_SAMPLE_RATE)
        self.assertEqual(self.tts_service.audio_dir, self.test_dir)
    
    def test_get_audio_url(self):
        """测试获取音频URL"""
        url = self.tts_service.get_audio_url('test.mp3')
        self.assertEqual(url, '/audio/test.mp3')
    
    def test_synthesize_dialogue(self):
        """测试对话语音合成（使用mock）"""
        dialogue = [
            {'text': 'Hello', 'speaker': 'A'},
            {'text': 'Hi there', 'speaker': 'B'},
            {'text': 'How are you?', 'speaker': 'A'}
        ]
        
        # 由于无法实际调用API，这里测试方法结构和返回值类型
        # 实际使用时应该mock SpeechSynthesizer.call
        results = self.tts_service.synthesize_dialogue(dialogue)
        
        # 验证返回的是列表
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), len(dialogue))
        
        # 验证每个结果包含必要的字段
        for i, result in enumerate(results):
            self.assertIn('index', result)
            self.assertIn('speaker', result)
            self.assertEqual(result['index'], i)
            self.assertEqual(result['speaker'], dialogue[i]['speaker'])
    
    def test_delete_audio(self):
        """测试删除音频文件"""
        # 创建一个测试文件
        test_file = os.path.join(self.test_dir, 'test_delete.mp3')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        # 测试删除存在的文件
        result = self.tts_service.delete_audio('test_delete.mp3')
        self.assertTrue(result)
        self.assertFalse(os.path.exists(test_file))
        
        # 测试删除不存在的文件
        result = self.tts_service.delete_audio('nonexistent.mp3')
        self.assertFalse(result)


class TestTTSServiceIntegration(unittest.TestCase):
    """TTS服务集成测试（需要真实API Key）"""
    
    @classmethod
    def setUpClass(cls):
        """检查是否有真实API Key并创建debug目录"""
        cls.api_key = os.environ.get('DASHSCOPE_API_KEY', '')
        cls.has_real_key = bool(cls.api_key and cls.api_key != 'your_api_key_here')
        
        # 创建debug目录用于保存测试音频
        cls.debug_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'debug', 'audio')
        os.makedirs(cls.debug_dir, exist_ok=True)
        print(f"\n调试音频将保存到: {cls.debug_dir}")
    
    def setUp(self):
        """跳过测试如果没有真实API Key"""
        if not self.has_real_key:
            self.skipTest('没有配置真实的DashScope API Key')
        self.tts_service = TTSService(api_key=self.api_key)
    
    def save_debug_audio(self, source_path, test_name):
        """保存音频到debug目录用于验证"""
        if not os.path.exists(source_path):
            return None
        
        import shutil
        from datetime import datetime
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{test_name}_{timestamp}.mp3"
        debug_path = os.path.join(self.debug_dir, filename)
        
        # 复制文件到debug目录
        shutil.copy2(source_path, debug_path)
        print(f"  [调试] 音频已保存: {debug_path}")
        return debug_path
    
    def test_real_synthesize(self):
        """测试真实的语音合成（可选）"""
        # 这个测试只有在配置了真实API Key时才会运行
        result = self.tts_service.synthesize('Hello, world!', voice='loongava_v2')
        
        # 无论成功失败，都保存音频文件用于调试
        if result.get('filepath') and os.path.exists(result['filepath']):
            debug_path = self.save_debug_audio(result['filepath'], 'test_real_synthesize')
            if debug_path:
                print(f"  [调试] 文件大小: {os.path.getsize(debug_path)} bytes")
        
        # 验证调用成功
        self.assertTrue(result.get('success'), f"TTS合成失败: {result.get('error', '未知错误')}")
        
        # 验证返回结构
        self.assertIn('filename', result)
        self.assertIn('filepath', result)
        self.assertIn('url', result)
        self.assertTrue(os.path.exists(result['filepath']), "音频文件未生成")
        
        # 清理原始文件（debug目录的保留）
        self.tts_service.delete_audio(result['filename'])
    
    def test_real_synthesize_chinese(self):
        """测试中文语音合成"""
        result = self.tts_service.synthesize('你好，这是一个测试。', voice='zhichu')
        
        # 保存调试文件
        if result.get('filepath') and os.path.exists(result['filepath']):
            self.save_debug_audio(result['filepath'], 'test_chinese')
        
        # 验证
        self.assertTrue(result.get('success'), f"中文合成失败: {result.get('error')}")
        if result.get('success'):
            self.tts_service.delete_audio(result['filename'])


def run_tests():
    """运行测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestTTSService))
    suite.addTests(loader.loadTestsFromTestCase(TestTTSServiceIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)