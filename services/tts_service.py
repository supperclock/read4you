import os
import azure.cognitiveservices.speech as speechsdk
from config.config import Config
import tempfile
import uuid
import time
import random

# 添加全局变量来跟踪请求
last_request_time = 0
min_request_interval = 1.0  # 最小请求间隔（秒）

def generate_speech(text, voice_name='zh-CN-XiaoxiaoNeural'):
    """使用微软Azure TTS服务将文本转换为语音，包含限流和重试机制"""
    global last_request_time
    
    # 检查文本长度，Azure TTS 有字符限制（通常为10000字符）
    MAX_TEXT_LENGTH = 1000  # 降低最大长度以减少错误
    
    if len(text) > MAX_TEXT_LENGTH:
        print(f"文本太长 ({len(text)} 字符)，将被截断为 {MAX_TEXT_LENGTH} 字符")
        text = text[:MAX_TEXT_LENGTH]
    
    # 限流：确保请求之间有足够的间隔
    current_time = time.time()
    time_since_last_request = current_time - last_request_time
    
    if time_since_last_request < min_request_interval:
        sleep_time = min_request_interval - time_since_last_request + random.uniform(0.1, 0.5)
        print(f"限流: 等待 {sleep_time:.2f} 秒")
        time.sleep(sleep_time)
    
    # 更新最后请求时间
    last_request_time = time.time()
    
    # 创建临时文件
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static/audio')
    os.makedirs(temp_dir, exist_ok=True)
    
    # 使用唯一文件名避免冲突
    unique_id = uuid.uuid4().hex
    temp_file = os.path.join(temp_dir, f'temp_{unique_id}.mp3')
    
    # 重试机制
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 配置语音服务
            speech_config = get_speech_config()
            
            # 设置语音
            speech_config.speech_synthesis_voice_name = voice_name
            
            # 配置音频输出
            audio_config = speechsdk.audio.AudioOutputConfig(filename=temp_file)
            
            # 创建语音合成器
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            # 合成语音
            result = speech_synthesizer.speak_text_async(text).get()
            
            # 检查结果
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # 返回相对URL路径而不是完整文件路径
                return f'/static/audio/temp_{unique_id}.mp3'
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                print(f"语音合成取消: {cancellation_details.reason}")
                
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    error_details = cancellation_details.error_details
                    print(f"错误详情: {error_details}")
                    
                    # 检查是否是速率限制错误
                    if "429" in error_details:
                        # 增加等待时间并重试
                        retry_count += 1
                        wait_time = min_request_interval * (2 ** retry_count) + random.uniform(0.5, 2.0)
                        print(f"遇到速率限制，等待 {wait_time:.2f} 秒后重试 ({retry_count}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                
                raise Exception(f"语音合成失败: {cancellation_details.reason}")
            
            # 如果执行到这里，说明没有成功也没有取消，这是一种异常情况
            raise Exception("语音合成未完成，也未取消")
            
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                # 指数退避策略
                wait_time = min_request_interval * (2 ** retry_count) + random.uniform(0.5, 2.0)
                print(f"合成失败，等待 {wait_time:.2f} 秒后重试 ({retry_count}/{max_retries}): {str(e)}")
                time.sleep(wait_time)
            else:
                print(f"语音合成异常，已达到最大重试次数: {str(e)}")
                raise 

def get_speech_config():
    """获取语音服务配置，如果主配置达到限制，则使用备用配置"""
    if Config.USE_BACKUP_SPEECH_SERVICE and hasattr(Config, 'MS_SPEECH_KEY_BACKUP'):
        print("使用备用语音服务")
        return speechsdk.SpeechConfig(
            subscription=Config.MS_SPEECH_KEY_BACKUP, 
            region=Config.MS_SPEECH_REGION_BACKUP
        )
    else:
        return speechsdk.SpeechConfig(
            subscription=Config.MS_SPEECH_KEY, 
            region=Config.MS_SPEECH_REGION
        ) 