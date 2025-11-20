import environ
from pathlib import Path

# Absolute path to app
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables
ENV = environ.Env()
environ.Env.read_env(env_file=f"{BASE_DIR}/config/.env")

# Directory names
MEDIA_DIR = ENV(
    "MEDIA_DIR"
)  # NOTE: this is an absolute path, containing already BASE_DIR
STATIC_DIR = "staticfiles"
IMG_DIR = "img"
LOG_DIR = "logs"
PDF_DIR = "pdf"
REGIONS_DIR = "regions"
TMP_DIR = "tmp"

# Media file paths
MEDIA_PATH = Path(MEDIA_DIR)
IMG_PATH = MEDIA_PATH / IMG_DIR
REGIONS_PATH = MEDIA_PATH / REGIONS_DIR
LOG_PATH = MEDIA_PATH / LOG_DIR / "app_log.log"
DOWNLOAD_LOG_PATH = MEDIA_PATH / LOG_DIR / "download.log"
TMP_PATH = MEDIA_PATH / TMP_DIR
