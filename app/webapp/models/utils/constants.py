from app.config.settings import APP_LANG

#############################
#        MODEL NAMES        #
#############################

MODEL_NAMES = {
    "Work": {"en": "work", "fr": "œuvre"},
    "Witness": {"en": "witness", "fr": "témoin"},
    "Language": {"en": "language", "fr": "langue"},
    "ConservationPlace": {"en": "conservation place", "fr": "lieu de conservation"},
    "Manifest": {"en": "manifest", "fr": "manifest"},
    "Manuscript": {"en": "manuscript", "fr": "manuscrit"},
    "Volume": {"en": "volume", "fr": "tome"},
    "Print": {"en": "print", "fr": "imprimé"},
    "Person": {"en": "historical actor", "fr": "acteur historique"},
    "Series": {"en": "series", "fr": "série"},
    "Content": {"en": "content", "fr": "contenu"},
    "Tag": {"en": "tag", "fr": "tag"},
    "Place": {"en": "place", "fr": "lieu"},
    "Digitization": {"en": "digitization", "fr": "numérisation"},
    "Edition": {"en": "edition", "fr": "édition"},
    "Role": {"en": "role", "fr": "rôle"},
    "Image": {"en": "image", "fr": "image"},
    "Pdf": {"en": "PDF", "fr": "PDF"},
    "Annotation": {"en": "annotation", "fr": "annotation"},
}

MANIFEST = MODEL_NAMES["Manifest"][APP_LANG]
MS = MODEL_NAMES["Manuscript"][APP_LANG]
VOL = MODEL_NAMES["Volume"][APP_LANG]
WIT = MODEL_NAMES["Witness"][APP_LANG]
PR = MODEL_NAMES["Print"][APP_LANG]
SER = MODEL_NAMES["Series"][APP_LANG]
CONT = MODEL_NAMES["Content"][APP_LANG]
WORK = MODEL_NAMES["Work"][APP_LANG]
TAG = MODEL_NAMES["Tag"][APP_LANG]
PLA = MODEL_NAMES["Place"][APP_LANG]
CONS_PLA = MODEL_NAMES["ConservationPlace"][APP_LANG]
DIG = MODEL_NAMES["Digitization"][APP_LANG]
ED = MODEL_NAMES["Edition"][APP_LANG]
LANG = MODEL_NAMES["Language"][APP_LANG]
PERS = MODEL_NAMES["Person"][APP_LANG]
ROLE = MODEL_NAMES["Role"][APP_LANG]
IMG = MODEL_NAMES["Image"][APP_LANG]
PDF = MODEL_NAMES["Pdf"][APP_LANG]
ANNO = MODEL_NAMES["Annotation"][APP_LANG]


# ABBREVIATION
MS_ABBR = "ms"
WPR_ABBR = "wpr"
TPR_ABBR = "tpr"
VOL_ABBR = "vol"
WIT_ABBR = "wit"
IMG_ABBR = "img"
PDF_ABBR = "pdf"
MAN_ABBR = "man"
PAG_ABBR = "pag"
FOL_ABBR = "fol"
OTH_ABBR = "oth"
PUB_ABBR = "pub"
AUT_ABBR = "aut"
ILL_ABBR = "ill"
SEL_ABBR = "sel"

TPR = f"letterpress {PR}" if APP_LANG == "en" else "typographie"
WPR = f"woodblock {PR}" if APP_LANG == "en" else "bois gravés"

PAGE = "page" if APP_LANG == "en" else "paginé"
FOLIO = "folio" if APP_LANG == "en" else "folioté"
OTHER = "other" if APP_LANG == "en" else "autre"

PUBLI = "publisher" if APP_LANG == "en" else "éditeur/diffuseur"
AUTHOR = "author" if APP_LANG == "en" else "auteur"
ILLUM = "illuminator" if APP_LANG == "en" else "enlumineur"
SELLER = "bookseller" if APP_LANG == "en" else "libraire"

WIT_TYPE = (
    (MS_ABBR, MS.capitalize()),
    (TPR_ABBR, TPR.capitalize()),
    (WPR_ABBR, WPR.capitalize()),
)

DIGIT_TYPE = (
    (IMG_ABBR, IMG.capitalize()),
    (PDF_ABBR, PDF.capitalize()),
    (MAN_ABBR, MANIFEST.capitalize()),
)

DIGIT_ABBR = {
    IMG: IMG_ABBR,
    PDF: PDF_ABBR,
    MANIFEST: MAN_ABBR,
}

PAGE_TYPE = (
    (PAG_ABBR, PAGE.capitalize()),
    (FOL_ABBR, FOLIO.capitalize()),
    (OTH_ABBR, OTHER.capitalize()),
)

ROLES = (
    (PUB_ABBR, PUBLI),
    (AUT_ABBR, AUTHOR),
    (ILL_ABBR, ILLUM),
    (SEL_ABBR, SELLER),
)

#############################
#        HELP TEXTS         #
#############################
PUBLISHED_INFO = (
    "record details will be accessible to other users of the database"
    if APP_LANG == "en"
    else "Les informations seront accessibles aux autres utilisateurs de la base."
)
IMG_INFO = "" if APP_LANG == "en" else "Envoyez des images jusqu'à 2 Go."

MANIFEST_DESC = (
    "A manifest allow to describe and share scans with their metadata based on the IIIF standard."
    if APP_LANG == "en"
    else "Un manifeste permet de décrire et de partager des numérisations avec leurs métadonnées selon la norme IIIF."
)
MANIFEST_INFO = f"""<div class='tooltip'>
                 <i class='fa-solid fa-circle-info' title='Manifest'>{MANIFEST_DESC}</i>
                 <span class='tooltiptext'></span>
             </div>
             E.g.: <a href='https://gallica.bnf.fr/iiif/ark:/12148/btv1b60004321/manifest.json' target='_blank'>
             https://gallica.bnf.fr/iiif/ark:/12148/btv1b60004321/manifest.json</a>"""
