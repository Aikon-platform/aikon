from pathlib import Path
from vhsapp.utils.constants import APP_NAME

# absolute path to vhs-platform
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Media file paths
# TODO make path actual paths (from BASE_DIR) and other call them DIR
MEDIA_PATH = "mediafiles"
STATIC_PATH = "staticfiles"
IMG_PATH = f"{MEDIA_PATH}/img"
MS_PDF_PATH = "manuscripts/pdf"
MS_ANNO_PATH = "manuscripts/annotation"
VOL_PDF_PATH = "volumes/pdf"
VOL_ANNO_PATH = "volumes/annotation"
LOG_PATH = f"{BASE_DIR}/logs/{APP_NAME}.log"
