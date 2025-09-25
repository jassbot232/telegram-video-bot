import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# Use absolute path for Docker
TEMP_DIR = "/app/temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v']
SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.aac', '.m4a', '.ogg', '.flac']
SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
SUPPORTED_DOCUMENT_FORMATS = ['.pdf', '.doc', '.docx', '.txt', '.rtf']

# Conversion mappings
CONVERSION_MAP = {
    'video': {
        'mp4': SUPPORTED_VIDEO_FORMATS,
        'avi': SUPPORTED_VIDEO_FORMATS,
        'mov': SUPPORTED_VIDEO_FORMATS,
        'mkv': SUPPORTED_VIDEO_FORMATS
    },
    'document': {
        'pdf': ['.pdf', '.doc', '.docx', '.txt'],
        'docx': ['.pdf', '.doc', '.docx', '.txt'],
        'txt': ['.pdf', '.doc', '.docx', '.txt'],
        'jpg': SUPPORTED_IMAGE_FORMATS,
        'png': SUPPORTED_IMAGE_FORMATS
    }
}

# Bot configuration
MAX_QUEUE_SIZE = 5
PROCESS_TIMEOUT = 1800  # 30 minutes

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
