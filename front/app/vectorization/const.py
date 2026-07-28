from app.webapp.utils.paths import MEDIA_PATH

MODULE_NAME = "vectorization"

def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    return path

SVG_DIR = "svg"
SVG_PATH = ensure_dir(MEDIA_PATH / SVG_DIR)

VECTO_MODEL_EPOCH = "0045"
