from app.webapp.utils.paths import MEDIA_PATH

def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    return path

MODULE_NAME = "similarity"
SCORE_DIR = "similarity"
SCORES_PATH = ensure_dir(MEDIA_PATH / SCORE_DIR)
