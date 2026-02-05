#!/usr/bin/env python3
"""
PyInstaller 打包脚本
打包英语口语练习程序为 exe
"""
import os
import sys
import subprocess
import shutil


def clean_build():
    """清理旧的构建文件"""
    dirs_to_remove = ['build', 'dist']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"🗑️  清理 {dir_name}/")
            shutil.rmtree(dir_name)


def build_exe():
    """构建 exe"""
    print("=" * 50)
    print("🚀 开始打包英语口语练习程序")
    print("=" * 50)
    
    # 检查 PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller 已安装")
    except ImportError:
        print("❌ PyInstaller 未安装，正在安装...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("✅ PyInstaller 安装完成")
    
    # 清理旧构建
    clean_build()
    
    # 使用 spec 文件打包
    print("\n📦 执行打包命令...")
    cmd = ['pyinstaller', 'speech_learner.spec']
    
    try:
        subprocess.run(cmd, check=True, capture_output=False)
        print("\n" + "=" * 50)
        print("✅ 打包成功！")
        print("=" * 50)
        
        # 创建发布目录
        dist_dir = 'release'
        if os.path.exists(dist_dir):
            shutil.rmtree(dist_dir)
        os.makedirs(dist_dir)
        
        # 复制 exe 到发布目录
        exe_name = 'speech_learner.exe' if sys.platform == 'win32' else 'speech_learner'
        exe_path = os.path.join('dist', exe_name)
        if os.path.exists(exe_path):
            shutil.copy2(exe_path, dist_dir)
        
        # 复制 .env.example 到发布目录
        shutil.copy2('.env.example', os.path.join(dist_dir, '.env.example'))
        
        # 创建使用说明
        with open(os.path.join(dist_dir, 'README.txt'), 'w', encoding='utf-8') as f:
            f.write("""Speech Learner - 英语口语练习程序
====================================

1. 首次使用
   - 复制 .env.example 文件，重命名为 .env
   - 编辑 .env 文件，填入您的阿里云 DashScope API Key
   - API Key 获取地址: https://dashscope.aliyun.com/

2. 运行程序
   - 双击 "speech_learner.exe" 运行
   - 程序会自动打开浏览器访问 http://localhost:5000
   - 请勿关闭黑色命令行窗口，否则服务会停止

3. 配置说明（.env 文件）
   - DASHSCOPE_API_KEY: 阿里云 DashScope API Key（必填）
   - TTS_MODEL: TTS 模型，默认 cosyvoice-v2
   - LLM_MODEL: LLM 模型，默认 deepseek-v3.2
   - SPEAKER_A_VOICE: Speaker A 音色，默认 loongava_v2
   - SPEAKER_B_VOICE: Speaker B 音色，默认 loongandy_v2

4. 注意事项
   - 确保网络连接正常
   - 确保 5000 端口未被占用
   - 首次生成语音可能需要较长时间

====================================
""")
        
        print(f"\n📁 发布文件已创建: {dist_dir}/")
        print(f"   - speech_learner.exe")
        print(f"   - .env.example")
        print(f"   - README.txt")
        print("\n✨ 打包完成！请将 release 目录压缩后分发给用户。")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    build_exe()
