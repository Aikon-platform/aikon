from app.config.settings import APP_NAME, APP_LANG

# Application titles
APP_NAME_UPPER = APP_NAME.upper()
APP_NAME_CAPITALIZED = APP_NAME.capitalize()
APP_DESCRIPTION = (
    "Computer Vision and Historical Analysis of Scientific Illustration Circulation"
)
SITE_HEADER = (
    f"{APP_NAME_UPPER} administration"
    if APP_LANG == "en"
    else f"Administration de {APP_NAME_UPPER}"
)
SITE_TITLE = (
    f"{APP_NAME_UPPER} portal" if APP_LANG == "en" else f"Portail de {APP_NAME_UPPER}"
)
SITE_INDEX_TITLE = (
    "Welcome to the administration website"
    if APP_LANG == "en"
    else "Bienvenue sur le site d'administration"
)
COPYRIGHT = "All rights reserved" if APP_LANG == "en" else "Tous droits réservés"

# Manifest versions
MANIFEST_V1 = "auto"  # Used for the manifest with automatic annotation
MANIFEST_V2 = "v2"  # Used for the manifest with corrected annotations

# Maximum number of words to be kept in the truncated string
TRUNCATEWORDS = 3
TRUNCATEWORDS_SIM = 5

# Maximum number of selected items for action application
MAX_ITEMS = 5

# Maximum number of rows to retrieve from the Geonames API search
MAX_ROWS = 10

# Maximal size for image download
MAX_SIZE = 2500
MAX_RES = 500
