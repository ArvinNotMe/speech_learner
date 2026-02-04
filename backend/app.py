from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import os
import sys
import json
import uuid
import threading
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import Config
from backend.services.tts_service import TTSService
from backend.services.llm_service import LLMService

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

Config.init_app(app)

# 全局服务实例 - 从环境变量自动初始化
tts_service = None
llm_service = None

# 任务状态存储（简单内存存储，生产环境建议使用 Redis）
task_status = {}
task_status_lock = threading.Lock()

def update_task_status(task_id, status, progress=None, result=None, error=None):
    """更新任务状态"""
    with task_status_lock:
        task_status[task_id] = {
            'status': status,  # 'pending', 'running', 'completed', 'failed'
            'progress': progress or 0,
            'result': result,
            'error': error,
            'updated_at': datetime.now().isoformat()
        }

def cleanup_old_tasks():
    """清理超过1小时的旧任务"""
    with task_status_lock:
        current_time = datetime.now()
        to_remove = []
        for task_id, task in task_status.items():
            updated_at = datetime.fromisoformat(task['updated_at'])
            if (current_time - updated_at).total_seconds() > 3600:
                to_remove.append(task_id)
        for task_id in to_remove:
            del task_status[task_id]

def init_services():
    """从环境变量初始化服务"""
    global tts_service, llm_service
    api_key = Config.DASHSCOPE_API_KEY
    if api_key:
        try:
            tts_service = TTSService(api_key=api_key)
            llm_service = LLMService(api_key=api_key)
            print(f"✅ 服务初始化成功 (API Key: {api_key[:8]}...)")
            return True
        except Exception as e:
            print(f"❌ 服务初始化失败: {e}")
            return False
    else:
        print("⚠️ 未配置 DASHSCOPE_API_KEY，请在 .env 文件中设置")
        return False

# 应用启动时自动初始化
init_services()

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'ok'})

@app.route('/api/test-long-request')
def test_long_request():
    """测试长请求是否正常"""
    import time
    time.sleep(5)  # 模拟5秒延迟
    return jsonify({'status': 'ok', 'message': '长请求测试成功'})

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取当前配置状态"""
    api_key_configured = bool(Config.DASHSCOPE_API_KEY)
    services_ready = tts_service is not None and llm_service is not None
    
    return jsonify({
        'success': True,
        'api_key_configured': api_key_configured,
        'services_ready': services_ready,
        'message': '服务已就绪' if services_ready else '请在 .env 文件中配置 DASHSCOPE_API_KEY'
    })

@app.route('/api/dialogue/generate', methods=['POST'])
def generate_dialogue():
    """生成对话内容"""
    global llm_service
    
    if llm_service is None:
        return jsonify({
            'success': False,
            'error': 'LLM service not initialized. Please set config first.'
        }), 400
    
    data = request.get_json()
    topic = data.get('topic', '')
    num_exchanges = data.get('num_exchanges', 5)
    
    if not topic:
        return jsonify({'success': False, 'error': 'Topic is required'}), 400
    
    result = llm_service.generate_dialogue(topic, num_exchanges)
    return jsonify(result)

@app.route('/api/translate', methods=['POST'])
def translate():
    """翻译中文到英文"""
    global llm_service
    
    if llm_service is None:
        return jsonify({
            'success': False,
            'error': 'LLM service not initialized. Please set config first.'
        }), 400
    
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'success': False, 'error': 'Text is required'}), 400
    
    result = llm_service.translate_to_english(text)
    return jsonify(result)

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """单文本语音合成"""
    global tts_service
    
    if tts_service is None:
        return jsonify({
            'success': False,
            'error': 'TTS service not initialized. Please set config first.'
        }), 400
    
    data = request.get_json()
    text = data.get('text', '')
    voice = data.get('voice', 'zhichu')
    
    if not text:
        return jsonify({'success': False, 'error': 'Text is required'}), 400
    
    result = tts_service.synthesize(text, voice=voice)
    return jsonify(result)

@app.route('/api/tts/dialogue', methods=['POST'])
def dialogue_to_speech():
    """对话语音合成"""
    global tts_service
    
    if tts_service is None:
        return jsonify({
            'success': False,
            'error': 'TTS service not initialized. Please set config first.'
        }), 400
    
    data = request.get_json()
    dialogue = data.get('dialogue', [])
    
    if not dialogue:
        return jsonify({'success': False, 'error': 'Dialogue list is required'}), 400
    
    results = tts_service.synthesize_dialogue(dialogue)
    return jsonify({
        'success': True,
        'results': results
    })

@app.route('/api/generate-full', methods=['POST'])
def generate_full_content():
    """生成完整的学习内容（对话+翻译+语音）"""
    global llm_service, tts_service
    
    if llm_service is None or tts_service is None:
        return jsonify({
            'success': False,
            'error': 'Services not initialized. Please set config first.'
        }), 400
    
    data = request.get_json()
    topic = data.get('topic', '')
    num_exchanges = data.get('num_exchanges', 5)
    
    if not topic:
        return jsonify({'success': False, 'error': 'Topic is required'}), 400
    
    print(f"\n{'='*60}")
    print(f"🚀 开始生成学习内容")
    print(f"{'='*60}")
    print(f"📌 话题: {topic}")
    print(f"📌 轮数: {num_exchanges}")
    print(f"{'='*60}\n")
    
    # 1. 生成对话
    print("[1/3] ⏳ 正在生成对话内容...")
    dialogue_result = llm_service.generate_dialogue(topic, num_exchanges)
    if not dialogue_result.get('success'):
        print(f"❌ 对话生成失败: {dialogue_result.get('error')}")
        return jsonify(dialogue_result)
    
    dialogue = dialogue_result.get('dialogue', [])
    keywords = dialogue_result.get('keywords', [])
    print(f"✅ 对话生成完成 ({len(dialogue)} 轮对话, {len(keywords)} 个关键词)")
    
    # 2. 为对话生成语音
    print(f"\n[2/3] ⏳ 正在生成语音 ({len(dialogue)} 段)...")
    dialogue_for_tts = [
        {'text': item.get('english', ''), 'speaker': item.get('speaker', 'A')}
        for item in dialogue
    ]
    
    tts_results = []
    success_count = 0
    for i, item in enumerate(dialogue_for_tts):
        speaker = item['speaker']
        text_preview = item['text'][:30] + '...' if len(item['text']) > 30 else item['text']
        print(f"  [{i+1}/{len(dialogue_for_tts)}] 合成 {speaker}: {text_preview}")
        
        voice = Config.SPEAKER_VOICES.get(speaker, Config.SPEAKER_VOICES['default'])
        result = tts_service.synthesize(item['text'], voice=voice)
        tts_results.append(result)
        
        if result.get('success'):
            success_count += 1
            print(f"       ✅ 完成 ({result.get('first_package_delay_ms', 0):.0f}ms)")
        else:
            print(f"       ❌ 失败: {result.get('error', '未知错误')}")
    
    print(f"\n✅ 语音生成完成 ({success_count}/{len(dialogue)} 成功)")
    
    # 3. 合并结果
    print(f"\n[3/3] ⏳ 正在合并结果...")
    for i, item in enumerate(dialogue):
        if i < len(tts_results) and tts_results[i].get('success'):
            item['audio_url'] = tts_results[i].get('url')
        # 清理可能存在的不可序列化数据
        item.pop('phonetic', None)
    print("✅ 结果合并完成")
    
    print(f"\n{'='*60}")
    print(f"🎉 学习内容生成完成!")
    print(f"{'='*60}\n")
    
    # 确保数据可以序列化为 JSON
    import json
    response_data = {
        'success': True,
        'topic': topic,
        'dialogue': dialogue,
        'keywords': keywords
    }
    
    # 验证 JSON 序列化
    try:
        json_str = json.dumps(response_data, ensure_ascii=False)
        print(f"📤 返回数据大小: {len(json_str)} bytes")
    except Exception as e:
        print(f"❌ JSON 序列化失败: {e}")
        return jsonify({'success': False, 'error': '数据序列化失败'}), 500
    
    # 直接返回 jsonify，让 Flask 处理
    print("📤 正在返回响应...")
    return jsonify(response_data)

def generate_content_async(task_id, topic, num_exchanges):
    """异步生成学习内容"""
    global tts_service, llm_service
    
    try:
        update_task_status(task_id, 'running', progress=10)
        
        # 1. 生成对话
        print(f"[Task {task_id}] 生成对话...")
        dialogue_result = llm_service.generate_dialogue(topic, num_exchanges)
        if not dialogue_result.get('success'):
            update_task_status(task_id, 'failed', error=dialogue_result.get('error'))
            return
        
        dialogue = dialogue_result.get('dialogue', [])
        keywords = dialogue_result.get('keywords', [])
        update_task_status(task_id, 'running', progress=40)
        
        # 2. 生成语音
        print(f"[Task {task_id}] 生成语音...")
        dialogue_for_tts = [
            {'text': item.get('english', ''), 'speaker': item.get('speaker', 'A')}
            for item in dialogue
        ]
        
        tts_results = []
        for i, item in enumerate(dialogue_for_tts):
            voice = Config.SPEAKER_VOICES.get(item['speaker'], Config.SPEAKER_VOICES['default'])
            result = tts_service.synthesize(item['text'], voice=voice)
            tts_results.append(result)
            progress = 40 + int((i + 1) / len(dialogue_for_tts) * 40)
            update_task_status(task_id, 'running', progress=progress)
        
        # 3. 合并结果
        print(f"[Task {task_id}] 合并结果...")
        for i, item in enumerate(dialogue):
            if i < len(tts_results) and tts_results[i].get('success'):
                item['audio_url'] = tts_results[i].get('url')
            item.pop('phonetic', None)
        
        # 4. 保存HTML
        html_content = generate_learn_html(topic, dialogue, keywords)
        filename = f"learn_{topic.replace(' ', '_').replace('/', '_')}.html"
        filepath = os.path.join(Config.GENERATED_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        update_task_status(task_id, 'completed', progress=100, result={
            'topic': topic,
            'dialogue': dialogue,
            'keywords': keywords,
            'filename': filename,
            'url': f'/generated/{filename}'
        })
        print(f"[Task {task_id}] 完成!")
        
    except Exception as e:
        print(f"[Task {task_id}] 错误: {e}")
        update_task_status(task_id, 'failed', error=str(e))

@app.route('/api/generate-async', methods=['POST'])
def generate_async():
    """启动异步生成任务"""
    global llm_service, tts_service
    
    if llm_service is None or tts_service is None:
        return jsonify({
            'success': False,
            'error': 'Services not initialized'
        }), 400
    
    data = request.get_json()
    topic = data.get('topic', '')
    num_exchanges = data.get('num_exchanges', 5)
    
    if not topic:
        return jsonify({'success': False, 'error': 'Topic is required'}), 400
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 初始化任务状态
    update_task_status(task_id, 'pending', progress=0)
    
    # 启动后台线程
    thread = threading.Thread(
        target=generate_content_async,
        args=(task_id, topic, num_exchanges)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': '任务已启动'
    })

@app.route('/api/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    with task_status_lock:
        task = task_status.get(task_id)
    
    if not task:
        return jsonify({
            'success': False,
            'error': 'Task not found'
        }), 404
    
    return jsonify({
        'success': True,
        'task': task
    })

@app.route('/api/save-html', methods=['POST'])
def save_html():
    """保存学习页面为静态HTML"""
    data = request.get_json()
    topic = data.get('topic', '英语学习')
    dialogue = data.get('dialogue', [])
    keywords = data.get('keywords', [])
    
    html_content = generate_learn_html(topic, dialogue, keywords)
    
    filename = f"learn_{topic.replace(' ', '_')}.html"
    filepath = os.path.join(Config.GENERATED_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return jsonify({
        'success': True,
        'filename': filename,
        'url': f'/generated/{filename}'
    })

@app.route('/generated/<path:filename>')
def serve_generated(filename):
    """提供生成的HTML文件"""
    return send_from_directory(Config.GENERATED_DIR, filename)

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    """提供音频文件"""
    return send_from_directory(Config.AUDIO_DIR, filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    return send_from_directory(os.path.join(Config.PROJECT_DIR, 'static'), filename)

@app.route('/api/history', methods=['GET'])
def get_history():
    """获取学习历史记录列表"""
    try:
        history_items = []
        if os.path.exists(Config.GENERATED_DIR):
            for filename in os.listdir(Config.GENERATED_DIR):
                if filename.startswith('learn_') and filename.endswith('.html'):
                    filepath = os.path.join(Config.GENERATED_DIR, filename)
                    stat = os.stat(filepath)
                    # 从文件名提取主题
                    topic = filename[6:-5].replace('_', ' ')  # 去掉 'learn_' 前缀和 '.html' 后缀
                    history_items.append({
                        'filename': filename,
                        'topic': topic,
                        'url': f'/generated/{filename}',
                        'created_at': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                        'size': stat.st_size
                    })
        # 按创建时间倒序排列
        history_items.sort(key=lambda x: x['created_at'], reverse=True)
        return jsonify({
            'success': True,
            'history': history_items,
            'total': len(history_items)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/history/<filename>', methods=['DELETE'])
def delete_history_item(filename):
    """删除指定的学习历史记录"""
    try:
        filepath = os.path.join(Config.GENERATED_DIR, filename)
        # 安全检查：确保文件在生成的目录中
        if not filepath.startswith(os.path.abspath(Config.GENERATED_DIR)):
            return jsonify({'success': False, 'error': 'Invalid filename'}), 400
        
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({
                'success': True,
                'message': f'{filename} 已删除'
            })
        else:
            return jsonify({
                'success': False,
                'error': '文件不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/history')
def history_page():
    """学习历史页面"""
    return render_template_string(HISTORY_HTML)

def generate_learn_html(topic, dialogue, keywords):
    """生成学习页面HTML"""
    keywords_html = ''
    for kw in keywords:
        keywords_html += f'''
        <div class="keyword-item">
            <span class="word">{kw.get('word', '')}</span>
            <span class="phonetic">{kw.get('phonetic', '')}</span>
            <span class="meaning">{kw.get('chinese', '')}</span>
        </div>
        '''
    
    dialogue_html = ''
    for item in dialogue:
        dialogue_html += f'''
        <div class="dialogue-row">
            <div class="col chinese">{item.get('chinese', '')}</div>
            <div class="col english">{item.get('english', '')}</div>
            <div class="col audio">
                {f'<audio controls src="{item.get("audio_url", "")}"></audio>' if item.get('audio_url') else '无音频'}
            </div>
        </div>
        '''
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic} - 英语口语练习</title>
    <style>
        :root {{
            --primary: #0d9488;
            --primary-dark: #0f766e;
            --primary-light: #ccfbf1;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --bg-page: #f0fdfa;
            --bg-card: #ffffff;
            --bg-muted: #f0fdfa;
            --border: #cbd5e1;
            --success: #22c55e;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f0fdfa 0%, #e0f2fe 50%, #f0f9ff 100%);
            padding: 20px;
            color: var(--text-primary);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.98);
            padding: 40px;
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(13, 148, 136, 0.1), 0 8px 25px rgba(0,0,0,0.06);
            border: 1px solid rgba(255, 255, 255, 0.5);
        }}
        h1 {{
            text-align: center;
            color: var(--text-primary);
            margin-bottom: 32px;
            font-size: 28px;
            font-weight: 700;
        }}
        .keywords {{
            background: var(--bg-muted);
            padding: 24px;
            border-radius: 16px;
            margin-bottom: 32px;
        }}
        .keywords h2 {{
            color: var(--text-primary);
            margin-bottom: 16px;
            font-size: 16px;
            font-weight: 600;
        }}
        .keyword-list {{ display: flex; flex-wrap: wrap; gap: 12px; }}
        .keyword-item {{
            background: var(--bg-card);
            padding: 12px 18px;
            border-radius: 12px;
            border: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        .keyword-item .word {{
            font-weight: 600;
            color: var(--primary);
            font-size: 15px;
        }}
        .keyword-item .phonetic {{
            color: var(--text-secondary);
            font-size: 13px;
        }}
        .keyword-item .meaning {{
            color: var(--text-secondary);
            font-size: 14px;
            border-left: 1px solid var(--border);
            padding-left: 10px;
        }}
        .dialogue-table {{
            width: 100%;
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid var(--border);
        }}
        .dialogue-header {{
            display: grid;
            grid-template-columns: 1fr 1fr 200px;
            gap: 0;
            padding: 16px 20px;
            background: var(--primary);
            color: white;
            font-weight: 600;
            font-size: 14px;
        }}
        .dialogue-row {{
            display: grid;
            grid-template-columns: 1fr 1fr 200px;
            gap: 0;
            padding: 0;
            border-bottom: 1px solid var(--border);
            align-items: stretch;
        }}
        .dialogue-row:last-child {{ border-bottom: none; }}
        .dialogue-row:nth-child(even) {{ background: var(--bg-muted); }}
        .col {{
            padding: 16px 20px;
            display: flex;
            align-items: center;
        }}
        .col:not(:last-child) {{ border-right: 1px solid var(--border); }}
        .chinese {{
            color: var(--text-primary);
            font-size: 15px;
        }}
        .english {{
            color: var(--primary);
            font-weight: 500;
            font-size: 15px;
        }}
        .audio {{
            justify-content: center;
        }}
        .audio audio {{
            width: 100%;
            height: 36px;
        }}
        .back-btn {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 24px;
            padding: 12px 24px;
            background: var(--primary);
            color: white;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 500;
            font-size: 14px;
            transition: all 0.2s;
        }}
        .back-btn:hover {{
            background: var(--primary-dark);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }}
        @media (max-width: 768px) {{
            .container {{ padding: 20px; }}
            .dialogue-header,
            .dialogue-row {{
                grid-template-columns: 1fr;
            }}
            .col:not(:last-child) {{
                border-right: none;
                border-bottom: 1px solid var(--border);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 {topic}</h1>

        <div class="keywords">
            <h2>🎯 关键词汇</h2>
            <div class="keyword-list">
                {keywords_html}
            </div>
        </div>

        <div class="dialogue-table">
            <div class="dialogue-header">
                <div>中文</div>
                <div>英文</div>
                <div>读音</div>
            </div>
            {dialogue_html}
        </div>

        <a href="/" class="back-btn">← 返回首页</a>
    </div>
</body>
</html>'''

# 配置页面HTML
INDEX_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>英语口语练习 - 配置</title>
    <style>
        :root {
            --primary: #0d9488;
            --primary-dark: #0f766e;
            --primary-light: #ccfbf1;
            --primary-soft: #5eead4;
            --success: #22c55e;
            --success-light: #dcfce7;
            --error: #ef4444;
            --error-light: #fee2e2;
            --warning: #f59e0b;
            --warning-light: #fef3c7;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --bg-page: #f0fdfa;
            --bg-card: #ffffff;
            --border: #cbd5e1;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f0fdfa 0%, #e0f2fe 50%, #f0f9ff 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }
        /* 背景装饰元素 */
        .bg-decoration {
            position: fixed;
            border-radius: 50%;
            opacity: 0.6;
            filter: blur(40px);
            z-index: 0;
            pointer-events: none;
        }
        .bg-decoration-1 {
            width: 300px;
            height: 300px;
            background: linear-gradient(135deg, #5eead4 0%, #0d9488 100%);
            top: -100px;
            right: -100px;
            animation: float 8s ease-in-out infinite;
        }
        .bg-decoration-2 {
            width: 200px;
            height: 200px;
            background: linear-gradient(135deg, #a5f3fc 0%, #22d3ee 100%);
            bottom: 10%;
            left: -50px;
            animation: float 10s ease-in-out infinite reverse;
        }
        .bg-decoration-3 {
            width: 150px;
            height: 150px;
            background: linear-gradient(135deg, #c4b5fd 0%, #8b5cf6 100%);
            top: 40%;
            right: 5%;
            animation: float 12s ease-in-out infinite;
        }
        .bg-decoration-4 {
            width: 100px;
            height: 100px;
            background: linear-gradient(135deg, #fbcfe8 0%, #f472b6 100%);
            bottom: 20%;
            right: 10%;
            animation: float 6s ease-in-out infinite reverse;
        }
        @keyframes float {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(5deg); }
        }
        .container {
            background: rgba(255, 255, 255, 0.95);
            padding: 48px;
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(13, 148, 136, 0.15), 0 8px 25px rgba(0,0,0,0.08);
            width: 100%;
            max-width: 480px;
            border: 1px solid rgba(255, 255, 255, 0.5);
            position: relative;
            z-index: 1;
            backdrop-filter: blur(10px);
        }
        h1 {
            text-align: center;
            color: var(--text-primary);
            margin-bottom: 8px;
            font-size: 32px;
            font-weight: 700;
        }
        .subtitle {
            text-align: center;
            color: var(--text-secondary);
            margin-bottom: 32px;
            font-size: 15px;
        }
        .form-group { margin-bottom: 24px; }
        label {
            display: block;
            margin-bottom: 8px;
            color: var(--text-primary);
            font-weight: 500;
            font-size: 14px;
        }
        input[type="text"], input[type="password"], input[type="number"] {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid var(--border);
            border-radius: 12px;
            font-size: 15px;
            transition: all 0.2s;
            background: var(--bg-card);
            color: var(--text-primary);
        }
        input[type="text"]:focus, input[type="password"]:focus, input[type="number"]:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px var(--primary-light);
        }
        input::placeholder {
            color: #9ca3af;
        }
        .btn {
            width: 100%;
            padding: 14px 24px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn:hover:not(:disabled) {
            background: var(--primary-dark);
            transform: translateY(-1px);
            box-shadow: 0 10px 20px -5px rgba(37, 99, 235, 0.3);
        }
        .btn:disabled {
            background: #d1d5db;
            cursor: not-allowed;
        }
        .status {
            margin-top: 20px;
            padding: 12px 16px;
            border-radius: 10px;
            text-align: center;
            display: none;
            font-size: 14px;
            font-weight: 500;
        }
        .status.success {
            background: var(--success-light);
            color: #065f46;
            display: block;
            border: 1px solid #a7f3d0;
        }
        .status.error {
            background: var(--error-light);
            color: #991b1b;
            display: block;
            border: 1px solid #fecaca;
        }
        .status.loading {
            background: var(--warning-light);
            color: #92400e;
            display: block;
            border: 1px solid #fde68a;
        }
        .link-btn {
            display: block;
            text-align: center;
            margin-top: 20px;
            color: var(--primary);
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            padding: 12px;
            border-radius: 10px;
            transition: all 0.2s;
        }
        .link-btn:hover {
            background: var(--primary-light);
            text-decoration: none;
        }
    </style>
</head>
<body>
    <!-- 背景装饰元素 -->
    <div class="bg-decoration bg-decoration-1"></div>
    <div class="bg-decoration bg-decoration-2"></div>
    <div class="bg-decoration bg-decoration-3"></div>
    <div class="bg-decoration bg-decoration-4"></div>
    
    <div class="container">
        <h1>🎓 英语口语练习</h1>
        <p class="subtitle">配置学习参数，生成专属对话内容</p>
        
        <div id="configStatus" class="status" style="display: block; margin-bottom: 20px;">
            ⏳ 正在检查配置...
        </div>
        
        <form id="configForm">
            <div class="form-group">
                <label for="topic">学习话题</label>
                <input type="text" id="topic" placeholder="例如：餐厅点餐、机场登机、酒店入住..." required>
            </div>
            
            <div class="form-group">
                <label for="exchanges">对话轮数</label>
                <input type="number" id="exchanges" value="5" min="3" max="10">
            </div>
            
            <button type="submit" class="btn" id="submitBtn" disabled>🚀 生成学习内容</button>
        </form>
        
        <div id="status" class="status"></div>
        <a href="/history" class="link-btn">📚 查看学习历史</a>
    </div>

    <script>
        // 页面加载时检查配置
        async function checkConfig() {
            const configStatus = document.getElementById('configStatus');
            const submitBtn = document.getElementById('submitBtn');
            
            try {
                const res = await fetch('/api/config');
                const data = await res.json();
                
                if (data.success && data.services_ready) {
                    configStatus.className = 'status success';
                    configStatus.innerHTML = '✅ ' + data.message;
                    submitBtn.disabled = false;
                } else {
                    configStatus.className = 'status error';
                    configStatus.innerHTML = '❌ ' + data.message + '<br><small>请在 .env 文件中配置 DASHSCOPE_API_KEY</small>';
                }
            } catch (error) {
                configStatus.className = 'status error';
                configStatus.textContent = '❌ 无法连接到服务器';
            }
        }
        
        // 页面加载时检查配置
        checkConfig();
        
        document.getElementById('configForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const topic = document.getElementById('topic').value;
            const exchanges = document.getElementById('exchanges').value;
            const statusDiv = document.getElementById('status');
            const submitBtn = document.getElementById('submitBtn');
            
            submitBtn.disabled = true;
            statusDiv.className = 'status loading';
            statusDiv.textContent = '⏳ 正在启动生成任务...';
            
            try {
                // 1. 启动异步生成任务
                console.log('Step 1: 启动异步任务, topic:', topic);
                const startRes = await fetch('/api/generate-async', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ topic: topic, num_exchanges: parseInt(exchanges) })
                });
                
                if (!startRes.ok) {
                    throw new Error('启动任务失败');
                }
                
                const startData = await startRes.json();
                if (!startData.success) {
                    throw new Error(startData.error || '启动任务失败');
                }
                
                const taskId = startData.task_id;
                console.log('任务已启动:', taskId);
                
                // 2. 轮询任务状态
                statusDiv.textContent = '⏳ 正在生成内容，请稍候...';
                
                let completed = false;
                let attempts = 0;
                const maxAttempts = 120; // 最多轮询120次（2分钟）
                
                while (!completed && attempts < maxAttempts) {
                    await new Promise(resolve => setTimeout(resolve, 1000)); // 每秒查询一次
                    attempts++;
                    
                    const statusRes = await fetch(`/api/task/${taskId}`);
                    if (!statusRes.ok) continue;
                    
                    const statusData = await statusRes.json();
                    if (!statusData.success) continue;
                    
                    const task = statusData.task;
                    console.log(`任务状态: ${task.status}, 进度: ${task.progress}%`);
                    
                    if (task.status === 'running') {
                        statusDiv.textContent = `⏳ 正在生成内容... (${task.progress}%)`;
                    } else if (task.status === 'completed') {
                        completed = true;
                        const result = task.result;
                        statusDiv.className = 'status success';
                        statusDiv.innerHTML = `✅ 生成成功！<br><a href="${result.url}" target="_blank">点击打开学习页面</a>`;
                    } else if (task.status === 'failed') {
                        throw new Error(task.error || '生成失败');
                    }
                }
                
                if (!completed) {
                    throw new Error('生成超时，请稍后重试');
                }
            } catch (error) {
                console.error('Error:', error);
                statusDiv.className = 'status error';
                let errorMsg = error.message;
                statusDiv.innerHTML = '❌ ' + errorMsg + '<br><small>请查看浏览器控制台(F12)获取详细信息</small>';
            } finally {
                submitBtn.disabled = false;
            }
        });
    </script>
</body>
</html>'''

# 学习历史页面HTML
HISTORY_HTML = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>学习历史 - 英语口语练习</title>
    <style>
        :root {
            --primary: #0d9488;
            --primary-dark: #0f766e;
            --primary-light: #ccfbf1;
            --primary-soft: #5eead4;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --bg-page: #f0fdfa;
            --bg-card: #ffffff;
            --bg-muted: #f0fdfa;
            --border: #cbd5e1;
            --error: #ef4444;
            --error-light: #fee2e2;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f0fdfa 0%, #e0f2fe 50%, #f0f9ff 100%);
            min-height: 100vh;
            padding: 20px;
            color: var(--text-primary);
            position: relative;
            overflow-x: hidden;
        }
        /* 背景装饰元素 */
        .bg-decoration {
            position: fixed;
            border-radius: 50%;
            opacity: 0.5;
            filter: blur(50px);
            z-index: 0;
            pointer-events: none;
        }
        .bg-decoration-1 {
            width: 250px;
            height: 250px;
            background: linear-gradient(135deg, #5eead4 0%, #0d9488 100%);
            top: -80px;
            left: -80px;
            animation: float 9s ease-in-out infinite;
        }
        .bg-decoration-2 {
            width: 180px;
            height: 180px;
            background: linear-gradient(135deg, #a5f3fc 0%, #22d3ee 100%);
            bottom: 15%;
            right: -40px;
            animation: float 11s ease-in-out infinite reverse;
        }
        .bg-decoration-3 {
            width: 120px;
            height: 120px;
            background: linear-gradient(135deg, #c4b5fd 0%, #8b5cf6 100%);
            top: 30%;
            left: 5%;
            animation: float 7s ease-in-out infinite;
        }
        @keyframes float {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-15px) rotate(3deg); }
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            padding: 40px;
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(13, 148, 136, 0.12), 0 8px 25px rgba(0,0,0,0.06);
            border: 1px solid rgba(255, 255, 255, 0.5);
            position: relative;
            z-index: 1;
            backdrop-filter: blur(10px);
        }
        h1 {
            text-align: center;
            color: var(--text-primary);
            margin-bottom: 8px;
            font-size: 28px;
            font-weight: 700;
        }
        .subtitle {
            text-align: center;
            color: var(--text-secondary);
            margin-bottom: 32px;
        }
        .header-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border);
        }
        .back-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: var(--bg-muted);
            color: var(--text-secondary);
            text-decoration: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .back-btn:hover {
            background: var(--border);
            color: var(--text-primary);
        }
        .refresh-btn {
            padding: 10px 20px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .refresh-btn:hover {
            background: var(--primary-dark);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }
        .history-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .history-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px;
            background: var(--bg-muted);
            border-radius: 12px;
            border: 1px solid var(--border);
            transition: all 0.2s;
        }
        .history-item:hover {
            background: var(--bg-card);
            border-color: var(--primary-light);
            box-shadow: 0 2px 8px rgba(37, 99, 235, 0.08);
        }
        .history-info {
            flex: 1;
        }
        .history-topic {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 6px;
        }
        .history-meta {
            font-size: 13px;
            color: var(--text-secondary);
        }
        .history-actions {
            display: flex;
            gap: 8px;
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            text-decoration: none;
            transition: all 0.2s;
        }
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        .btn-primary:hover {
            background: var(--primary-dark);
            box-shadow: 0 2px 8px rgba(13, 148, 136, 0.3);
        }
        .btn-danger {
            background: transparent;
            color: var(--error);
            border: 1px solid var(--error);
        }
        .btn-danger:hover {
            background: var(--error-light);
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-secondary);
        }
        .empty-state .icon {
            font-size: 48px;
            margin-bottom: 16px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: var(--text-secondary);
        }
        .error {
            text-align: center;
            padding: 40px;
            color: var(--error);
        }
    </style>
</head>
<body>
    <!-- 背景装饰元素 -->
    <div class="bg-decoration bg-decoration-1"></div>
    <div class="bg-decoration bg-decoration-2"></div>
    <div class="bg-decoration bg-decoration-3"></div>
    
    <div class="container">
        <h1>📚 学习历史</h1>
        <p class="subtitle">查看和管理您的学习记录</p>
        
        <div class="header-actions">
            <a href="/" class="back-btn">← 返回首页</a>
            <button class="refresh-btn" onclick="loadHistory()">🔄 刷新列表</button>
        </div>
        
        <div id="historyList" class="history-list">
            <div class="loading">⏳ 加载中...</div>
        </div>
    </div>

    <script>
        async function loadHistory() {
            const listContainer = document.getElementById('historyList');
            listContainer.innerHTML = '<div class="loading">⏳ 加载中...</div>';
            
            try {
                const response = await fetch('/api/history');
                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(data.error || '加载失败');
                }
                
                if (data.history.length === 0) {
                    listContainer.innerHTML = `
                        <div class="empty-state">
                            <div class="icon">📝</div>
                            <p>暂无学习记录</p>
                            <p style="font-size: 14px; margin-top: 10px;">去首页生成您的第一个学习内容吧！</p>
                        </div>
                    `;
                    return;
                }
                
                listContainer.innerHTML = data.history.map(item => `
                    <div class="history-item" data-filename="${item.filename}">
                        <div class="history-info">
                            <div class="history-topic">${escapeHtml(item.topic)}</div>
                            <div class="history-meta">
                                📅 ${item.created_at} · 📄 ${formatSize(item.size)}
                            </div>
                        </div>
                        <div class="history-actions">
                            <a href="${item.url}" class="btn btn-primary" target="_blank">开始学习</a>
                            <button class="btn btn-danger" onclick="deleteItem('${item.filename}', this)">删除</button>
                        </div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error:', error);
                listContainer.innerHTML = `<div class="error">❌ 加载失败: ${error.message}</div>`;
            }
        }
        
        async function deleteItem(filename, btn) {
            if (!confirm(`确定要删除 "${filename}" 吗？`)) {
                return;
            }
            
            btn.disabled = true;
            btn.textContent = '删除中...';
            
            try {
                const response = await fetch(`/api/history/${filename}`, {
                    method: 'DELETE'
                });
                const data = await response.json();
                
                if (data.success) {
                    // 移除该项
                    const item = btn.closest('.history-item');
                    item.style.opacity = '0';
                    item.style.transform = 'translateX(-100%)';
                    setTimeout(() => item.remove(), 300);
                } else {
                    throw new Error(data.error || '删除失败');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('删除失败: ' + error.message);
                btn.disabled = false;
                btn.textContent = '删除';
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }
        
        // 页面加载时自动加载历史记录
        loadHistory();
    </script>
</body>
</html>'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)