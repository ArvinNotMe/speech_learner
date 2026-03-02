import os
import sys
from dotenv import load_dotenv

# 确保从正确的目录加载 .env 文件
if hasattr(sys, '_MEIPASS'):
    # PyInstaller 打包后的环境：使用 exe 所在目录
    env_dir = os.path.dirname(sys.executable)
else:
    # 开发环境：使用项目根目录
    env_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 尝试加载 .env 文件
env_path = os.path.join(env_dir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # 如果 .env 不存在，尝试从当前目录加载（向后兼容）
    load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'

    # 阿里云配置
    DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY') or ''

    # TTS 模型配置 (CosyVoice)
    # 可选模型: cosyvoice-v2, cosyvoice-v3-flash, cosyvoice-v3-plus
    TTS_MODEL = os.environ.get('TTS_MODEL') or 'cosyvoice-v2'

    # LLM 模型配置
    # 可选模型: deepseek-v3.2, qwen-max, qwen-plus, qwen-turbo
    LLM_MODEL = os.environ.get('LLM_MODEL') or 'deepseek-v3.2'

    # Speaker Voice 配置 (CosyVoice 音色)
    # 为不同 speaker 配置不同的 voice
    SPEAKER_VOICES = {
        'A': os.environ.get('SPEAKER_A_VOICE') or 'loongava_v2',
        'B': os.environ.get('SPEAKER_B_VOICE') or 'loongandy_v2',
        'default': os.environ.get('SPEAKER_B_VOICE') or 'loongandy_v2'
    }

    # 文件路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 获取项目根目录（支持开发和打包环境）
    # 注意：在类定义时无法确定是否在打包环境，因此使用当前目录
    # 在 init_app 中会重新计算正确的 PROJECT_DIR
    PROJECT_DIR = os.path.dirname(BASE_DIR)
    
    AUDIO_DIR = os.path.join(PROJECT_DIR, 'static', 'audio')
    GENERATED_DIR = os.path.join(PROJECT_DIR, 'generated')

    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 重新计算 PROJECT_DIR（此时 sys._MEIPASS 已经设置）
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller 打包后的环境：使用 exe 所在目录
            Config.PROJECT_DIR = os.path.dirname(sys.executable)
        else:
            # 开发环境：使用项目根目录
            Config.PROJECT_DIR = os.path.dirname(Config.BASE_DIR)
        
        # 更新目录路径
        Config.AUDIO_DIR = os.path.join(Config.PROJECT_DIR, 'static', 'audio')
        Config.GENERATED_DIR = os.path.join(Config.PROJECT_DIR, 'generated')
        
        # 确保目录存在
        os.makedirs(Config.AUDIO_DIR, exist_ok=True)
        os.makedirs(Config.GENERATED_DIR, exist_ok=True)
        
        print(f"📁 PROJECT_DIR: {Config.PROJECT_DIR}")
        print(f"📁 GENERATED_DIR: {Config.GENERATED_DIR}")
