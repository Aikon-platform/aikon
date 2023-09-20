from pathlib import Path

# absolute path to app
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Directory names
MEDIA_DIR = "mediafiles"
STATIC_DIR = "staticfiles"
IMG_DIR = "img"
MS_DIR = "manuscripts"
VOL_DIR = "volumes"
LOG_DIR = "logs"
PDF_DIR = "pdf"
ANNO_DIR = "annotation"

# Media file paths
IMG_PATH = f"{MEDIA_DIR}/{IMG_DIR}"
ANNO_PATH = f"{MEDIA_DIR}/{ANNO_DIR}"
LOG_PATH = f"{BASE_DIR}/{LOG_DIR}/app_log.log"
IIIF_LOG_PATH = f"{BASE_DIR}/{LOG_DIR}/iiif.log"
