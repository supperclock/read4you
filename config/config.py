import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///audiobook.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 上传文件配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static/uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB 最大上传限制
    ALLOWED_EXTENSIONS = {'pdf', 'epub', 'docx', 'txt'}
    
    # 微软Azure TTS配置
    MS_SPEECH_KEY = 'EOkNbfsAH9aBUJSKocbBwovl31ZM86ajoTUWwedwOcfX9KrIyq4RJQQJ99BCAC3pKaRXJ3w3AAAYACOGuEoJ'
    MS_SPEECH_REGION = 'eastasia'
    
    # 备用语音服务配置
    MS_SPEECH_KEY_BACKUP = '2SorcPMXUwCyBEgY7f0zdvMr6OBN0zSiUsXrnUJXtz8vmzdVzjG8JQQJ99BCAC3pKaRXJ3w3AAAYACOGfX0k'
    MS_SPEECH_REGION_BACKUP = 'eastasia'
    
    # 是否使用备用密钥
    USE_BACKUP_SPEECH_SERVICE = False
    
    # 可用的语音列表
    AVAILABLE_VOICES = [
        {'id': 'zh-CN-XiaoxiaoNeural', 'name': '晓晓 (女声)'},
        {'id': 'zh-CN-YunxiNeural', 'name': '云希 (男声)'},
        {'id': 'zh-CN-YunyangNeural', 'name': '云扬 (男声)'},
        {'id': 'zh-CN-XiaohanNeural', 'name': '晓涵 (女声)'},
        {'id': 'zh-CN-XiaomoNeural', 'name': '晓墨 (女声)'},
        {'id': 'zh-CN-XiaoxuanNeural', 'name': '晓萱 (女声)'},
        {'id': 'en-US-AriaNeural', 'name': 'Aria (英语女声)'},
        {'id': 'en-US-GuyNeural', 'name': 'Guy (英语男声)'}
    ] 