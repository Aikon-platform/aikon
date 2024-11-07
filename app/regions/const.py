from app.config.settings import WEBAPP_NAME, APP_NAME
from app.webapp.utils.paths import BASE_DIR

MODULE_NAME = "regions"
MODULE_DIR = BASE_DIR / WEBAPP_NAME / MODULE_NAME

# TODO retrieve api model instead
EXTRACTOR_MODEL = f"best_{APP_NAME.lower()}.pt"
