# 🎓 英语口语练习程序

一个基于 AI 的英语口语学习应用，使用阿里云 DashScope API 生成对话内容并合成语音。

## ✨ 功能特点

- **AI 对话生成**：使用大语言模型生成场景化的英语对话
- **语音合成**：使用 CosyVoice 模型合成自然流畅的英语发音
- **学习历史**：保存学习记录，方便复习回顾
- **清新界面**：现代化的 UI 设计，支持毛玻璃效果和动画

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- 阿里云 DashScope API Key

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

复制 `.env.example` 为 `.env`，并填入你的 API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
DASHSCOPE_API_KEY=your_api_key_here
```

> 从 [阿里云 DashScope](https://dashscope.aliyun.com/) 获取 API Key

### 4. 启动服务

```bash
python run.py
```

或使用自定义端口：

```bash
python run.py -p 5003
```

### 5. 访问应用

打开浏览器访问：http://localhost:5000

## 📁 项目结构

```
speech_learner/
├── backend/
│   ├── app.py              # Flask 主应用
│   ├── config.py           # 配置文件
│   └── services/
│       ├── tts_service.py  # TTS 语音合成服务
│       └── llm_service.py  # LLM 对话生成服务
├── generated/              # 生成的学习页面
├── static/audio/           # 音频文件
├── .env                    # 环境变量配置
├── requirements.txt        # Python 依赖
└── run.py                  # 启动脚本
```

## ⚙️ 配置说明

在 `backend/config.py` 中可以修改以下配置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `TTS_MODEL` | TTS 模型 | `cosyvoice-v2` |
| `LLM_MODEL` | LLM 模型 | `deepseek-v3.2` |
| `SPEAKER_VOICES` | 说话人音色 | A: loongava_v2, B: loongandy_v2 |

## 📝 使用方法

1. **生成学习内容**
   - 在首页输入学习话题（如：餐厅点餐、机场登机等）
   - 设置对话轮数
   - 点击"生成学习内容"

2. **学习对话**
   - 查看关键词汇
   - 播放音频学习发音
   - 对照中英文练习

3. **查看历史**
   - 点击"查看学习历史"
   - 管理已生成的学习内容

## 📦 打包

使用 PyInstaller 将应用打包为可执行文件：

### 1. 安装 PyInstaller

```bash
pip install pyinstaller
```

### 2. 执行打包

```bash
python build_exe.py
```

### 3. 运行打包后的程序

打包完成后，可执行文件位于 `release/speech_learner.exe`：

```bash
cd release
speech_learner.exe
```

> 首次运行时，程序会自动创建 `.env` 文件，请配置 API Key 后重新运行

## 🧪 测试

运行单元测试：

```bash
python -m pytest backend/tests/ -v
```

或单独测试服务：

```bash
# 测试 TTS
python test_tts_demo.py

# 测试 LLM
python test_llm_demo.py
```

## 🔧 技术栈

- **后端**：Flask + Flask-CORS
- **AI 服务**：阿里云 DashScope (CosyVoice + Qwen)
- **前端**：原生 HTML + CSS + JavaScript

## 📄 许可证

MIT License
