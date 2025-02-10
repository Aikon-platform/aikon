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

# Media file paths
IMG_PATH = f"{MEDIA_DIR}/{IMG_DIR}"
REGIONS_PATH = f"{MEDIA_DIR}/{REGIONS_DIR}"
LOG_PATH = f"{BASE_DIR}/{LOG_DIR}/app_log.log"
IIIF_LOG_PATH = f"{BASE_DIR}/{LOG_DIR}/iiif.log"
DOWNLOAD_LOG_PATH = f"{BASE_DIR}/{LOG_DIR}/download.log"
