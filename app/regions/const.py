from app.config.settings import WEBAPP_NAME
from app.webapp.utils.paths import BASE_DIR

MODULE_NAME = "extraction"
MODULE_DIR = BASE_DIR / WEBAPP_NAME / MODULE_NAME

EXTRACTOR_MODEL = "best_eida.pt"
