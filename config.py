import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Bot token
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logging.warning("BOT_TOKEN not found in environment variables")

# File handling
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# Use absolute path for Docker
TEMP_DIR = "/app/temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

# Supported formats
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.aac', '.m4a', '.ogg', '.flac']
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
SUPPORTED_DOCUMENT_FORMATS = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt']

# Bot configuration
MAX_QUEUE_SIZE = 5
PROCESS_TIMEOUT = 1800  # 30 minutes
MAX_CONCURRENT_PROCESSES = 3

# Docker specific settings
IS_DOCKER = os.path.exists('/.dockerenv')

def get_temp_path(filename: str) -> str:
    """Get absolute path for temporary files"""
    return os.path.join(TEMP_DIR, filename)

def get_file_type(filename: str) -> str:
    """Determine file type from extension"""
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in SUPPORTED_VIDEO_FORMATS:
        return 'video'
    elif ext in SUPPORTED_AUDIO_FORMATS:
        return 'audio'
    elif ext in SUPPORTED_IMAGE_FORMATS:
        return 'image'
    elif ext in SUPPORTED_DOCUMENT_FORMATS:
        return 'document'
    else:
        return 'unknown'

def cleanup_old_files(max_age_hours: int = 24):
    """Clean up files older than specified hours"""
    import time
    import glob
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for file_pattern in ['*.mp4', '*.mp3', '*.jpg', '*.png', '*.pdf', '*.docx']:
        for file_path in glob.glob(get_temp_path(file_pattern)):
            try:
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.unlink(file_path)
                        logging.info(f"Cleaned up old file: {file_path}")
            except Exception as e:
                logging.error(f"Error cleaning up file {file_path}: {e}")
