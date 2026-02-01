from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import Config
from backend.services.tts_service import TTSService
from backend.services.llm_service import LLMService

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

Config.init_app(app)

# 全局服务实例
tts_service = None
llm_service = None

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'ok'})

@app.route('/api/config', methods=['POST'])
def set_config():
    """设置API配置"""
    global tts_service, llm_service
    
    data = request.get_json()
    api_key = data.get('api_key', '')
    
    if not api_key:
        return jsonify({'success': False, 'error': 'API key is required'}), 400
    
    try:
        tts_service = TTSService(api_key=api_key)
        llm_service = LLMService(api_key=api_key)
        return jsonify({
            'success': True,
            'message': 'Configuration updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
    print("✅ 结果合并完成")
    
    print(f"\n{'='*60}")
    print(f"🎉 学习内容生成完成!")
    print(f"{'='*60}\n")
    
    return jsonify({
        'success': True,
        'topic': topic,
        'dialogue': dialogue,
        'keywords': keywords
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
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5; 
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ text-align: center; color: #333; margin-bottom: 30px; }}
        .keywords {{ 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            margin-bottom: 30px;
        }}
        .keywords h2 {{ color: #555; margin-bottom: 15px; font-size: 18px; }}
        .keyword-list {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .keyword-item {{ 
            background: white; 
            padding: 10px 15px; 
            border-radius: 20px; 
            border: 1px solid #e0e0e0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .keyword-item .word {{ font-weight: bold; color: #2196F3; }}
        .keyword-item .phonetic {{ color: #999; font-size: 12px; }}
        .keyword-item .meaning {{ color: #666; font-size: 14px; }}
        .dialogue-table {{ width: 100%; }}
        .dialogue-header {{ 
            display: grid; 
            grid-template-columns: 1fr 1fr 200px; 
            gap: 15px; 
            padding: 15px; 
            background: #2196F3; 
            color: white;
            font-weight: bold;
            border-radius: 8px 8px 0 0;
        }}
        .dialogue-row {{ 
            display: grid; 
            grid-template-columns: 1fr 1fr 200px; 
            gap: 15px; 
            padding: 15px; 
            border-bottom: 1px solid #eee;
            align-items: center;
        }}
        .dialogue-row:nth-child(even) {{ background: #f8f9fa; }}
        .col {{ padding: 10px; }}
        .chinese {{ color: #333; }}
        .english {{ color: #2196F3; font-weight: 500; }}
        .audio audio {{ width: 100%; height: 30px; }}
        .back-btn {{ 
            display: inline-block; 
            margin-top: 20px; 
            padding: 10px 20px; 
            background: #2196F3; 
            color: white; 
            text-decoration: none; 
            border-radius: 5px;
        }}
        .back-btn:hover {{ background: #1976D2; }}
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
        
        <a href="/" class="back-btn">← 返回配置</a>
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
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container { 
            max-width: 600px; 
            width: 100%;
            background: white; 
            padding: 40px; 
            border-radius: 20px; 
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { 
            text-align: center; 
            color: #333; 
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .form-group { margin-bottom: 20px; }
        label { 
            display: block; 
            margin-bottom: 8px; 
            color: #555; 
            font-weight: 500;
        }
        input[type="text"], input[type="password"], input[type="number"] {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus, input[type="password"]:focus, input[type="number"]:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            display: none;
        }
        .status.success { background: #d4edda; color: #155724; display: block; }
        .status.error { background: #f8d7da; color: #721c24; display: block; }
        .status.loading { background: #fff3cd; color: #856404; display: block; }
        .link-btn {
            display: block;
            text-align: center;
            margin-top: 15px;
            color: #667eea;
            text-decoration: none;
        }
        .link-btn:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 英语口语练习</h1>
        <p class="subtitle">配置学习参数，生成专属对话内容</p>
        
        <form id="configForm">
            <div class="form-group">
                <label for="apiKey">阿里云 DashScope API Key</label>
                <input type="password" id="apiKey" placeholder="请输入您的API Key" required>
            </div>
            
            <div class="form-group">
                <label for="topic">学习话题</label>
                <input type="text" id="topic" placeholder="例如：餐厅点餐、机场登机、酒店入住..." required>
            </div>
            
            <div class="form-group">
                <label for="exchanges">对话轮数</label>
                <input type="number" id="exchanges" value="5" min="3" max="10">
            </div>
            
            <button type="submit" class="btn" id="submitBtn">🚀 生成学习内容</button>
        </form>
        
        <div id="status" class="status"></div>
        <a href="/frontend/config.html" class="link-btn">使用高级配置界面 →</a>
        <a href="/history" class="link-btn">📚 查看学习历史</a>
    </div>

    <script>
        document.getElementById('configForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const apiKey = document.getElementById('apiKey').value;
            const topic = document.getElementById('topic').value;
            const exchanges = document.getElementById('exchanges').value;
            const statusDiv = document.getElementById('status');
            const submitBtn = document.getElementById('submitBtn');
            
            submitBtn.disabled = true;
            statusDiv.className = 'status loading';
            statusDiv.textContent = '⏳ 正在生成内容，请稍候...';
            
            try {
                // 1. 配置API
                console.log('Step 1: 配置API...');
                const configRes = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ api_key: apiKey })
                });
                
                if (!configRes.ok) {
                    const errorData = await configRes.json().catch(() => ({}));
                    throw new Error(errorData.error || `API配置失败: ${configRes.status}`);
                }
                console.log('Step 1: API配置成功');
                
                // 2. 生成完整内容
                console.log('Step 2: 生成对话内容...');
                const generateRes = await fetch('/api/generate-full', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ topic, num_exchanges: parseInt(exchanges) })
                });
                
                if (!generateRes.ok) {
                    const errorData = await generateRes.json().catch(() => ({}));
                    throw new Error(errorData.error || `生成失败: ${generateRes.status}`);
                }
                
                const data = await generateRes.json();
                console.log('Step 2: 生成结果:', data);
                
                if (!data.success) {
                    throw new Error(data.error || '生成失败');
                }
                
                // 3. 保存HTML
                console.log('Step 3: 保存HTML...');
                const saveRes = await fetch('/api/save-html', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        topic: data.topic,
                        dialogue: data.dialogue,
                        keywords: data.keywords
                    })
                });
                
                if (!saveRes.ok) {
                    const errorData = await saveRes.json().catch(() => ({}));
                    throw new Error(errorData.error || `保存失败: ${saveRes.status}`);
                }
                
                const saveData = await saveRes.json();
                console.log('Step 3: 保存结果:', saveData);
                
                if (saveData.success) {
                    statusDiv.className = 'status success';
                    statusDiv.innerHTML = `✅ 生成成功！<br><a href="${saveData.url}" target="_blank">点击打开学习页面</a>`;
                } else {
                    throw new Error(saveData.error || '保存失败');
                }
            } catch (error) {
                console.error('Error:', error);
                statusDiv.className = 'status error';
                statusDiv.innerHTML = '❌ ' + error.message + '<br><small>请查看浏览器控制台获取详细信息</small>';
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
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 900px; 
            margin: 0 auto;
            background: white; 
            padding: 40px; 
            border-radius: 20px; 
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { 
            text-align: center; 
            color: #333; 
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
        .header-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #f0f0f0;
        }
        .back-btn {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 10px 20px;
            background: #f5f5f5;
            color: #666;
            text-decoration: none;
            border-radius: 10px;
            transition: all 0.3s;
        }
        .back-btn:hover {
            background: #e0e0e0;
            color: #333;
        }
        .refresh-btn {
            padding: 10px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .history-list {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .history-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 12px;
            border: 1px solid #e0e0e0;
            transition: all 0.3s;
        }
        .history-item:hover {
            background: #f0f0f0;
            transform: translateX(5px);
        }
        .history-info {
            flex: 1;
        }
        .history-topic {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }
        .history-meta {
            font-size: 13px;
            color: #999;
        }
        .history-actions {
            display: flex;
            gap: 10px;
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            text-decoration: none;
            transition: all 0.3s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        .btn-danger {
            background: #ff4757;
            color: white;
        }
        .btn-danger:hover {
            background: #ff3838;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }
        .empty-state .icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .error {
            text-align: center;
            padding: 40px;
            color: #ff4757;
        }
    </style>
</head>
<body>
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