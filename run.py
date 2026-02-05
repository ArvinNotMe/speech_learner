#!/usr/bin/env python3
"""
英语口语练习程序启动脚本
支持开发环境和 PyInstaller 打包环境
"""
import os
import sys
import webbrowser
import time
import threading


def get_exe_dir():
    """获取程序运行目录（支持开发和打包环境）"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包后的环境
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))


def setup_environment():
    """设置运行环境"""
    exe_dir = get_exe_dir()
    
    # 设置工作目录为程序所在目录
    os.chdir(exe_dir)
    
    # 确保 .env 文件存在（仅打包环境需要检查）
    if hasattr(sys, '_MEIPASS'):
        env_file = os.path.join(exe_dir, '.env')
        env_example_file = os.path.join(exe_dir, '.env.example')
        
        if not os.path.exists(env_file) and os.path.exists(env_example_file):
            print("⚠️  未找到 .env 文件，正在从 .env.example 创建...")
            with open(env_example_file, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已创建 .env 文件，请编辑配置您的 API Key")
            print("📝 按回车键继续打开配置文件...")
            input()
            # 尝试用系统默认编辑器打开
            if sys.platform == 'win32':
                os.startfile(env_file)
            elif sys.platform == 'darwin':
                os.system(f'open "{env_file}"')
            else:
                os.system(f'xdg-open "{env_file}"')
            print("📝 请配置 API Key 后重新运行程序")
            input("按回车键退出...")
            sys.exit(0)


def start_server(port=5000):
    """启动 Flask 服务器"""
    # 添加项目路径
    exe_dir = get_exe_dir()
    sys.path.insert(0, exe_dir)
    
    from backend.app import app
    print(f"🚀 启动服务器... (端口: {port})")
    print(f"📂 工作目录: {os.getcwd()}")
    # 使用多线程模式，避免长请求阻塞其他请求
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)


def open_browser(port=5000):
    """自动打开浏览器"""
    time.sleep(2)
    url = f'http://localhost:{port}'
    print(f"🌐 正在打开浏览器: {url}")
    webbrowser.open(url)


def main():
    """主函数"""
    # 显示启动信息（打包环境）
    if hasattr(sys, '_MEIPASS'):
        print("=" * 50)
        print("🎯 英语口语练习程序")
        print("=" * 50)
    
    # 设置环境
    setup_environment()
    
    # 检查依赖
    try:
        import flask
        import dashscope
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        if hasattr(sys, '_MEIPASS'):
            input("按回车键退出...")
        sys.exit(1)
    
    # 解析参数
    import argparse
    parser = argparse.ArgumentParser(description='英语口语练习程序')
    parser.add_argument('-p', '--port', type=int, default=5000, help='服务器端口 (默认: 5000)')
    args = parser.parse_args()
    
    # 启动浏览器线程
    browser_thread = threading.Thread(target=open_browser, args=(args.port,))
    browser_thread.daemon = True
    browser_thread.start()
    
    # 启动服务器（打包环境显示额外信息）
    if hasattr(sys, '_MEIPASS'):
        print("\n✨ 服务启动成功！")
        print(f"🌐 请访问: http://localhost:{args.port}")
        print("⚠️  请勿关闭此窗口\n")
    
    start_server(args.port)


if __name__ == '__main__':
    main()
