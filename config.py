import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'xiaohongshu-bot-secret-key-2024')
    
    SELENIUM_HEADLESS = os.getenv('SELENIUM_HEADLESS', 'false').lower() == 'true'
    SELENIUM_WAIT_TIME = int(os.getenv('SELENIUM_WAIT_TIME', '10'))
    
    MAX_REPLIES_PER_NOTE = int(os.getenv('MAX_REPLIES_PER_NOTE', '5'))
    MIN_DELAY_BETWEEN_REPLIES = float(os.getenv('MIN_DELAY_BETWEEN_REPLIES', '2.0'))
    MAX_DELAY_BETWEEN_REPLIES = float(os.getenv('MAX_DELAY_BETWEEN_REPLIES', '4.0'))
    
    DEFAULT_REPLY_TEMPLATE = os.getenv('DEFAULT_REPLY_TEMPLATE', 
        '感谢您的留言！{author}，关于"{content}"的问题，我会尽快回复您的~')
