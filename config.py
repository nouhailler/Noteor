from pathlib import Path

APP_NAME = "Noteor"
VERSION = "1.0.0"

# Répertoires de données
DATA_DIR = Path.home() / ".local" / "share" / "Noteor"
DB_PATH = DATA_DIR / "notes.db"
MEDIA_DIR = DATA_DIR / "media"
AUDIO_DIR = MEDIA_DIR / "audio"
IMAGE_DIR = MEDIA_DIR / "images"
THUMB_DIR = MEDIA_DIR / "thumbnails"

# Images
THUMBNAIL_SIZE = (220, 160)

# Audio
SAMPLE_RATE = 44100
CHANNELS = 1
AUDIO_DTYPE = "int16"

# UI
WINDOW_TITLE = f"{APP_NAME} v{VERSION}"
LEFT_PANEL_MIN_WIDTH = 200
LEFT_PANEL_MAX_WIDTH = 280
CENTER_PANEL_MIN_WIDTH = 220
CENTER_PANEL_MAX_WIDTH = 360
