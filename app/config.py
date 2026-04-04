import sys
from pathlib import Path


if getattr(sys, "frozen", False):
	BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
	APP_DIR = Path(sys.executable).resolve().parent
else:
	BASE_DIR = Path(__file__).resolve().parent.parent
	APP_DIR = BASE_DIR

RUNTIME_DIR = APP_DIR / "runtime_data"
UPLOAD_DIR = RUNTIME_DIR / "uploads"

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8765
MAX_UPLOAD_MB = 20

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".webp"}