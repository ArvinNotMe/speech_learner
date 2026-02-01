import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # 阿里云配置
    DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY') or ''
    
    # TTS配置 (CosyVoice 模型)
    # 可选模型: cosyvoice-v2, cosyvoice-v3-flash, cosyvoice-v3-plus
    TTS_MODEL = 'cosyvoice-v2'
    
    # LLM配置
    LLM_MODEL = 'deepseek-v3.2'
    
    # Speaker Voice 配置 (CosyVoice 音色)
    # 为不同 speaker 配置不同的 voice
    SPEAKER_VOICES = {
        'A': 'loongava_v2',  # Speaker A 的音色
        'B': 'loongandy_v2',  # Speaker B 的音色
        'default': 'loongandy_v2'  # 默认音色
    }
    
    # 文件路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_DIR = os.path.dirname(BASE_DIR)
    AUDIO_DIR = os.path.join(PROJECT_DIR, 'static', 'audio')
    GENERATED_DIR = os.path.join(PROJECT_DIR, 'generated')
    
    @staticmethod
    def init_app(app):
        # 确保目录存在
        os.makedirs(Config.AUDIO_DIR, exist_ok=True)
        os.makedirs(Config.GENERATED_DIR, exist_ok=True)