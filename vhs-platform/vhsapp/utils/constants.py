# Application titles
APP_NAME = "eida"
APP_NAME_UPPER = APP_NAME.upper()
SITE_HEADER = f"Administration de {APP_NAME_UPPER}"
SITE_TITLE = f"Portail de {APP_NAME_UPPER}"
SITE_INDEX_TITLE = "Bienvenue sur le site d'administration"

# Help texts
AUTHOR_INFO = (
    "<ul>"
    "<li>Indiquez [Anonyme] si auteur non identifié.</li>"
    "<li>Si nom auteur non trouvé, merci de chercher directement dans "
    "<a href='https://data.bnf.fr/' target='_blank'>Data BnF</a>."
    "</li>"
    "</ul>"
)
WORK_INFO = "Titre de l'oeuvre ou des oeuvres (même approximatif)."
PUBLISHED_INFO = (
    "Les informations seront accessibles aux autres utilisateurs de la base."
)
DIGITIZED_VERSION_MS_INFO = "Exemples : Gallica, Photos personnelles [Stavros Lazaris], Biblioteca Apostolica Vaticana."
DIGITIZED_VERSION_VOL_INFO = "Exemple : Gallica."
MANIFEST_FINAL_INFO = (
    "<i style='color:#efb80b' class='fa-solid fa-triangle-exclamation'></i> "
    "ATTENTION : la version en cours de vérification ne peut plus être modifiée."
)
PLACE_INFO = "Si différent de l'ensemble."
IMAGE_INFO = "Envoyez des images jusqu'à 2 Go."
MANIFEST_INFO = (
    "<div class='tooltip'>"
    "<i class='fa-solid fa-circle-info' title='Manifest'></i>"
    "<span class='tooltiptext'>"
    "A IIIF manifest is the package that contains all the information related to a particular digital object, "
    "including the image itself as well as the metadata."
    "</span>"
    "</div> "
    "Exemple : "
    "<a href='https://gallica.bnf.fr/iiif/ark:/12148/btv1b60004321/manifest.json' target='_blank'>"
    "https://gallica.bnf.fr/iiif/ark:/12148/btv1b60004321/manifest.json"
    "</a>"
)

# Dropdown options
CENTURY = (
    ("XIXe", "XIXe"),
    ("XVIIIe", "XVIIIe"),
    ("XVIIe", "XVIIe"),
    ("XVIe", "XVIe"),
    ("XVe", "XVe"),
    ("XIVe", "XIVe"),
    ("XIIIe", "XIIIe"),
    ("XIIe", "XIIe"),
    ("XIe", "XIe"),
    ("Xe", "Xe"),
    ("IXe", "IXe"),
    ("VIIIe", "VIIIe"),
    ("VIIe", "VIIe"),
    ("VIe", "VIe"),
    ("Ve", "Ve"),
    ("IVe", "IVe"),
    ("IIIe", "IIIe"),
    ("IIe", "IIe"),
    ("Ier", "Ier"),
)

# Works
MANUSCRIPT = "manuscript"
VOLUME = "volume"
MANUSCRIPT_PLURAL = "manuscripts"
VOLUME_plural = "volumes"

# Work abbreviations
MANUSCRIPT_ABBR = "ms"
VOLUME_ABBR = "vol"

# Manifest versions
MANIFEST_AUTO = "auto"
MANIFEST_V2 = "v2"

# Maximum number of words to be kept in the truncated string
TRUNCATEWORDS = 5

# Maximum number of selected items for action application
MAX_ITEMS = 5

# URLs
VHS_URL = "http://localhost:8000/"  # "http://iscd.huma-num.fr/"
SAS_URL = "http://localhost:8888/"  # "http://iscd.huma-num.fr/sas/"
VHS_URL_SECURE = ""  # "https://iscd.huma-num.fr/"
SAS_URL_SECURE = ""  # "https://iscd.huma-num.fr/sas/"
