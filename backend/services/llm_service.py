import json
import dashscope
from dashscope import Generation
from backend.config import Config

class LLMService:
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.DASHSCOPE_API_KEY
        dashscope.api_key = self.api_key
        self.model = Config.LLM_MODEL
    
    def generate_dialogue(self, topic, num_exchanges=5):
        """
        生成中英对照对话
        
        Args:
            topic: 对话话题
            num_exchanges: 对话轮数
            
        Returns:
            dict: 包含对话列表和关键词
        """
        prompt = f"""请生成一个关于"{topic}"的英语对话，包含{num_exchanges}轮对话。

要求：
1. 对话发生在两个角色之间（A和B）
2. 每句对话提供：中文、英文
3. 对话内容实用、自然，适合口语练习
4. 在对话结束后，列出5-8个重要词汇和短语，包含：英文、中文释义

请以JSON格式返回，格式如下：
{{
    "dialogue": [
        {{
            "speaker": "A",
            "chinese": "中文内容",
            "english": "English content"
        }}
    ],
    "keywords": [
        {{
            "word": "english word",
            "chinese": "中文释义"
        }}
    ]
}}

请确保返回的是有效的JSON格式。"""

        try:
            response = Generation.call(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': '你是一个专业的英语口语教学助手，擅长生成实用的英语对话和词汇讲解。'},
                    {'role': 'user', 'content': prompt}
                ],
                result_format='message'
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                # 提取JSON内容
                json_str = self._extract_json(content)
                data = json.loads(json_str)
                return {
                    'success': True,
                    'topic': topic,
                    'dialogue': data.get('dialogue', []),
                    'keywords': data.get('keywords', [])
                }
            else:
                return {
                    'success': False,
                    'error': f'API调用失败: {response.message}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def translate_to_english(self, chinese_text):
        """
        将中文翻译成地道英文
        
        Args:
            chinese_text: 中文文本
            
        Returns:
            dict: 包含英文翻译
        """
        prompt = f"""请将以下中文翻译成地道、自然的英文口语表达：

中文：{chinese_text}

请提供：
1. 标准翻译（适合正式场合）
2. 口语化翻译（适合日常对话）
3. 如果有多种表达方式，请列出2-3种

请以JSON格式返回：
{{
    "standard": "Standard English translation",
    "colloquial": "Colloquial English translation",
    "alternatives": ["Alternative 1", "Alternative 2"]
}}"""

        try:
            response = Generation.call(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': '你是一个专业的中英翻译专家，擅长将中文翻译成地道、自然的英文。'},
                    {'role': 'user', 'content': prompt}
                ],
                result_format='message'
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                json_str = self._extract_json(content)
                data = json.loads(json_str)
                return {
                    'success': True,
                    'chinese': chinese_text,
                    'translations': data
                }
            else:
                return {
                    'success': False,
                    'error': f'API调用失败: {response.message}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_json(self, text):
        """从文本中提取JSON内容"""
        # 尝试找到JSON块
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            return text[start_idx:end_idx + 1]
        
        return text