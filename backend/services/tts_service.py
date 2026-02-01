import os
import uuid
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer
from backend.config import Config


class TTSService:
    """TTS语音合成服务 - 使用 CosyVoice 模型"""
    
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or Config.DASHSCOPE_API_KEY
        dashscope.api_key = self.api_key
        self.model = model or Config.TTS_MODEL
        self.audio_dir = Config.AUDIO_DIR
        
    def synthesize(self, text, voice='longxiaochun_v2', output_filename=None):
        """
        将文本转换为语音
        
        Args:
            text: 要合成的文本
            voice: 音色名称 (默认: longxiaochun_v2)
                   支持任意阿里云CosyVoice音色，如：
                   - cosyvoice-v2: longxiaochun_v2, longxiaocheng_v2 等
                   - cosyvoice-v3: longanyang, longmoxin 等
            output_filename: 输出文件名（可选）
            
        Returns:
            dict: 包含音频文件路径和URL的信息
        """
        if not output_filename:
            output_filename = f"{uuid.uuid4().hex}.mp3"
        
        output_path = os.path.join(self.audio_dir, output_filename)
        
        # 直接使用用户提供的音色名称
        voice_code = voice
        
        try:
            # 实例化 SpeechSynthesizer
            synthesizer = SpeechSynthesizer(
                model=self.model,
                voice=voice_code
            )
            
            # 发送待合成文本，获取二进制音频
            audio = synthesizer.call(text)
            
            if audio:
                # 将音频保存至本地
                with open(output_path, 'wb') as f:
                    f.write(audio)
                
                # 获取性能指标
                request_id = synthesizer.get_last_request_id()
                first_package_delay = synthesizer.get_first_package_delay()
                
                return {
                    'success': True,
                    'filename': output_filename,
                    'filepath': output_path,
                    'url': f'/audio/{output_filename}',
                    'text': text,
                    'voice': voice,
                    'voice_code': voice_code,
                    'model': self.model,
                    'request_id': request_id,
                    'first_package_delay_ms': first_package_delay
                }
            else:
                return {
                    'success': False,
                    'error': 'TTS synthesis failed: no audio data returned'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def synthesize_dialogue(self, dialogue_list, voice_a='longxiaochun_v2', voice_b='longxiaocheng_v2'):
        """
        为对话列表生成语音
        
        Args:
            dialogue_list: 对话列表，每项包含text和speaker
            voice_a: 说话人A的音色 (默认: longxiaochun_v2)
            voice_b: 说话人B的音色 (默认: longxiaocheng_v2)
            
        Returns:
            list: 每个对话项的语音信息
        """
        results = []
        
        for i, item in enumerate(dialogue_list):
            text = item.get('text', '')
            speaker = item.get('speaker', 'A')
            
            # 根据说话人选择音色
            voice = voice_a if speaker == 'A' else voice_b
            
            filename = f"dialogue_{i:03d}_{speaker}.mp3"
            result = self.synthesize(text, voice=voice, output_filename=filename)
            result['index'] = i
            result['speaker'] = speaker
            results.append(result)
            
        return results
    
    def get_audio_url(self, filename):
        """获取音频文件的URL"""
        return f'/audio/{filename}'
    
    def delete_audio(self, filename):
        """删除音频文件"""
        filepath = os.path.join(self.audio_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
