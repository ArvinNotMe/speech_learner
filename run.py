#!/usr/bin/env python3
"""
英语口语练习程序启动脚本
"""
import os
import sys
import webbrowser
import time
import threading

def start_server(port=5000):
    """启动Flask服务器"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from backend.app import app
    print(f"🚀 启动服务器... (端口: {port})")
    # 使用多线程模式，避免长请求阻塞其他请求
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

def open_browser(port=5000):
    """自动打开浏览器"""
    time.sleep(2)
    url = f'http://localhost:{port}'
    print(f"🌐 正在打开浏览器: {url}")
    webbrowser.open(url)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='英语口语练习程序')
    parser.add_argument('-p', '--port', type=int, default=5000, help='服务器端口 (默认: 5000)')
    args = parser.parse_args()
    
    # 检查依赖
    try:
        import flask
        import dashscope
    except ImportError:
        print("❌ 缺少依赖，请先安装: pip install -r backend/requirements.txt")
        sys.exit(1)
    
    # 启动浏览器线程
    browser_thread = threading.Thread(target=open_browser, args=(args.port,))
    browser_thread.daemon = True
    browser_thread.start()
    
    # 启动服务器
    start_server(args.port)