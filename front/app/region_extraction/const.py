from app.config.settings import WEBAPP_NAME
from app.webapp.utils.paths import BASE_DIR, MEDIA_PATH

def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    return path

MODULE_NAME = "region_extraction"
MODULE_DIR = BASE_DIR / WEBAPP_NAME / MODULE_NAME
REGIONS_DIR = ensure_dir(MEDIA_PATH / MODULE_NAME)

EXTRACTOR_MODEL = "illustration_extraction.pt"
