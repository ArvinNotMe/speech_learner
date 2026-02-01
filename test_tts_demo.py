#!/usr/bin/env python3
"""
TTS 单次测试 Demo - CosyVoice 版本
用于测试不同 voice 和文本的语音合成效果
"""
import os
import sys
import argparse
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.tts_service import TTSService
from backend.config import Config


def test_tts(text, voice='longxiaochun_v2', model=None, save_debug=True):
    """
    测试单次 TTS 合成
    
    Args:
        text: 要合成的文本
        voice: 音色名称 (默认: longxiaochun_v2)
               支持任意阿里云CosyVoice音色，如：
               - cosyvoice-v2: longxiaochun_v2, longxiaocheng_v2, longxiaobai_v2, longxiaowei_v2
               - cosyvoice-v3: longanyang, longmoxin, longshuo 等
        model: 模型名称 (默认使用配置文件中的模型)
        save_debug: 是否保存到 debug 目录
    """
    # 获取 API Key
    api_key = os.environ.get('DASHSCOPE_API_KEY', '')
    if not api_key:
        print("❌ 错误: 请设置 DASHSCOPE_API_KEY 环境变量或在 .env 文件中配置")
        return
    
    # 使用指定模型或默认模型
    use_model = model or Config.TTS_MODEL
    
    print(f"\n{'='*70}")
    print(f"🎙️  TTS 测试 (CosyVoice)")
    print(f"{'='*70}")
    print(f"文本:  {text}")
    print(f"模型:  {use_model}")
    print(f"音色:  {voice}")
    print(f"API:   {api_key[:10]}...{api_key[-4:]}")
    print(f"{'='*70}\n")
    
    # 创建 TTS 服务
    tts_service = TTSService(api_key=api_key, model=use_model)
    
    # 执行合成
    print("⏳ 正在合成...")
    result = tts_service.synthesize(text, voice=voice)
    
    # 显示结果
    print(f"\n{'='*70}")
    if result.get('success'):
        print("✅ 合成成功!")
        print(f"\n📄 文件信息:")
        print(f"   文件名: {result['filename']}")
        print(f"   文件路径: {result['filepath']}")
        print(f"   文件大小: {os.path.getsize(result['filepath'])} bytes")
        
        print(f"\n🔊 音频信息:")
        print(f"   音色代码: {result['voice_code']}")
        print(f"   模型: {result['model']}")
        print(f"   Request ID: {result['request_id']}")
        print(f"   首包延迟: {result['first_package_delay_ms']} ms")
        
        # 保存到 debug 目录
        if save_debug:
            debug_dir = os.path.join(os.path.dirname(__file__), 'debug', 'audio')
            os.makedirs(debug_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            debug_filename = f"demo_{use_model}_{voice}_{timestamp}.mp3"
            debug_path = os.path.join(debug_dir, debug_filename)
            
            import shutil
            shutil.copy2(result['filepath'], debug_path)
            print(f"\n💾 调试文件已保存: {debug_path}")
        
        # 播放提示
        print(f"\n🎵 播放命令:")
        print(f"   ffplay {result['filepath']}")
        
        # 是否删除原文件
        response = input("\n🗑️  是否删除原文件? (y/n): ").strip().lower()
        if response == 'y':
            tts_service.delete_audio(result['filename'])
            print("✅ 已删除")
        else:
            print(f"📁 文件保留在: {result['filepath']}")
    else:
        print("❌ 合成失败!")
        print(f"错误: {result.get('error', '未知错误')}")
        if 'message' in result:
            print(f"详情: {result['message']}")
    
    print(f"{'='*70}\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='TTS 测试工具 (CosyVoice)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 使用 cosyvoice-v2 默认音色
  python3 test_tts_demo.py "你好"
  
  # 使用指定音色
  python3 test_tts_demo.py "你好" -v longxiaocheng_v2
  
  # 使用 cosyvoice-v3 模型
  python3 test_tts_demo.py "你好" -v longanyang -m cosyvoice-v3-flash
  
常用音色 (cosyvoice-v2):
  longxiaochun_v2, longxiaocheng_v2, longxiaobai_v2, longxiaowei_v2

常用音色 (cosyvoice-v3):
  longanyang, longmoxin, longshuo, longjing, longyue
        '''
    )
    parser.add_argument('text', nargs='?', default='你好，这是一个测试。', 
                        help='要合成的文本 (默认: 你好，这是一个测试。)')
    parser.add_argument('-v', '--voice', default='longxiaochun_v2',
                        help='音色名称 (默认: longxiaochun_v2)')
    parser.add_argument('-m', '--model', default=None,
                        choices=['cosyvoice-v2', 'cosyvoice-v3-flash', 'cosyvoice-v3-plus'],
                        help='模型选择 (默认: cosyvoice-v2)')
    parser.add_argument('--no-debug', action='store_true',
                        help='不保存调试文件')
    
    args = parser.parse_args()
    
    # 加载 .env 文件
    from dotenv import load_dotenv
    load_dotenv()
    
    test_tts(args.text, voice=args.voice, model=args.model, save_debug=not args.no_debug)


if __name__ == '__main__':
    main()
