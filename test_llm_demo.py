#!/usr/bin/env python3
"""
LLM 服务测试 Demo
用于测试对话生成和翻译功能
"""
import os
import sys
import argparse
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.services.llm_service import LLMService


def test_dialogue(topic, num_exchanges=5):
    """
    测试对话生成功能
    
    Args:
        topic: 对话话题
        num_exchanges: 对话轮数
    """
    # 获取 API Key
    api_key = os.environ.get('DASHSCOPE_API_KEY', '')
    if not api_key:
        print("❌ 错误: 请设置 DASHSCOPE_API_KEY 环境变量或在 .env 文件中配置")
        return
    
    print(f"\n{'='*70}")
    print(f"💬 对话生成测试")
    print(f"{'='*70}")
    print(f"话题: {topic}")
    print(f"轮数: {num_exchanges}")
    print(f"API:  {api_key[:10]}...{api_key[-4:]}")
    print(f"{'='*70}\n")
    
    # 创建 LLM 服务
    llm_service = LLMService(api_key=api_key)
    
    # 执行生成
    print("⏳ 正在生成对话...")
    result = llm_service.generate_dialogue(topic, num_exchanges)
    
    # 显示结果
    print(f"\n{'='*70}")
    if result.get('success'):
        print("✅ 生成成功!\n")
        
        # 显示对话
        print("📖 对话内容:")
        print("-" * 70)
        for item in result['dialogue']:
            speaker = item.get('speaker', 'A')
            chinese = item.get('chinese', '')
            english = item.get('english', '')
            
            print(f"\n[{speaker}]")
            print(f"  中文: {chinese}")
            print(f"  英文: {english}")
        
        # 显示关键词
        print("\n" + "-" * 70)
        print("🎯 关键词汇:")
        print("-" * 70)
        for kw in result['keywords']:
            word = kw.get('word', '')
            chinese = kw.get('chinese', '')
            print(f"  • {word} - {chinese}")
        
        # 保存到文件
        save_option = input("\n💾 是否保存到文件? (y/n): ").strip().lower()
        if save_option == 'y':
            filename = f"dialogue_{topic.replace(' ', '_')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"✅ 已保存到: {filename}")
    else:
        print("❌ 生成失败!")
        print(f"错误: {result.get('error', '未知错误')}")
    
    print(f"{'='*70}\n")


def test_translate(text):
    """
    测试翻译功能
    
    Args:
        text: 要翻译的中文文本
    """
    # 获取 API Key
    api_key = os.environ.get('DASHSCOPE_API_KEY', '')
    if not api_key:
        print("❌ 错误: 请设置 DASHSCOPE_API_KEY 环境变量或在 .env 文件中配置")
        return
    
    print(f"\n{'='*70}")
    print(f"🌐 翻译测试")
    print(f"{'='*70}")
    print(f"原文: {text}")
    print(f"API:  {api_key[:10]}...{api_key[-4:]}")
    print(f"{'='*70}\n")
    
    # 创建 LLM 服务
    llm_service = LLMService(api_key=api_key)
    
    # 执行翻译
    print("⏳ 正在翻译...")
    result = llm_service.translate_to_english(text)
    
    # 显示结果
    print(f"\n{'='*70}")
    if result.get('success'):
        print("✅ 翻译成功!\n")
        
        translations = result.get('translations', {})
        
        print("📖 翻译结果:")
        print("-" * 70)
        if 'standard' in translations:
            print(f"  标准翻译: {translations['standard']}")
        if 'colloquial' in translations:
            print(f"  口语翻译: {translations['colloquial']}")
        if 'alternatives' in translations:
            print(f"  其他表达:")
            for alt in translations['alternatives']:
                print(f"    - {alt}")
    else:
        print("❌ 翻译失败!")
        print(f"错误: {result.get('error', '未知错误')}")
    
    print(f"{'='*70}\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='LLM 服务测试工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 生成对话
  python3 test_llm_demo.py -d "餐厅点餐"
  python3 test_llm_demo.py -d "机场登机" -n 3
  
  # 翻译文本
  python3 test_llm_demo.py -t "你好，很高兴见到你"
  python3 test_llm_demo.py -t "请问附近有什么好吃的？"
        '''
    )
    
    parser.add_argument('-d', '--dialogue', metavar='TOPIC',
                        help='生成对话，指定话题')
    parser.add_argument('-n', '--num-exchanges', type=int, default=5,
                        help='对话轮数 (默认: 5)')
    parser.add_argument('-t', '--translate', metavar='TEXT',
                        help='翻译中文到英文')
    
    args = parser.parse_args()
    
    # 加载 .env 文件
    from dotenv import load_dotenv
    load_dotenv()
    
    # 根据参数执行相应功能
    if args.dialogue:
        test_dialogue(args.dialogue, args.num_exchanges)
    elif args.translate:
        test_translate(args.translate)
    else:
        parser.print_help()
        print("\n💡 提示: 请使用 -d 生成对话 或 -t 翻译文本")


if __name__ == '__main__':
    main()
