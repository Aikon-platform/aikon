from pathlib import Path
from vhsapp.utils.constants import APP_NAME

# absolute path to vhs-platform
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Media file paths
MEDIA_PATH = "mediafiles/"
IMG_PATH = "img/"
MS_PDF_PATH = "manuscripts/pdf/"
MS_ANNO_PATH = "manuscripts/annotation/"
VOL_PDF_PATH = "volumes/pdf/"
VOL_ANNO_PATH = "volumes/annotation/"
LOG_PATH = f"{BASE_DIR}/logs/{APP_NAME}.log"
