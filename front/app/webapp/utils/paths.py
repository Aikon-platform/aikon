import environ
from pathlib import Path

# Absolute path to app
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables
ENV = environ.Env()
environ.Env.read_env(env_file=f"{BASE_DIR}/config/.env")

# Directory names
# TODO rename to MEDIA_PATH
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
IMG_PATH = Path(f"{MEDIA_DIR}/{IMG_DIR}")
REGIONS_PATH = Path(f"{MEDIA_DIR}/{REGIONS_DIR}")
LOG_PATH = Path(f"{BASE_DIR}/{LOG_DIR}/app_log.log")
DOWNLOAD_LOG_PATH = Path(f"{BASE_DIR}/{LOG_DIR}/download.log")
TMP_PATH = Path(f"{MEDIA_DIR}/{TMP_DIR}")
