from app.config.settings import APP_NAME

# Application titles
APP_NAME_UPPER = APP_NAME.upper()
APP_NAME_CAPITALIZED = APP_NAME.capitalize()
APP_DESCRIPTION = (
    "Computer Vision and Historical Analysis of Scientific Illustration Circulation"
)
SITE_HEADER = f"Administration de {APP_NAME_UPPER}"
SITE_TITLE = f"Portail de {APP_NAME_UPPER}"
SITE_INDEX_TITLE = "Bienvenue sur le site d'administration"

# Manifest versions
MANIFEST_V1 = "auto"  # Used for the manifest with automatic annotation
MANIFEST_V2 = "v2"  # Used for the manifest with corrected annotations

# Maximum number of words to be kept in the truncated string
TRUNCATEWORDS = 5

# Maximum number of selected items for action application
MAX_ITEMS = 5

# Maximal size for image download
MAX_SIZE = 2500
MAX_RES = 500
