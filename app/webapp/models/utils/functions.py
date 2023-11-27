from app.config.settings import APP_LANG
from app.webapp.models.utils.constants import MODEL_NAMES
from app.webapp.utils.functions import pluralize

common_fields = {
    "date_min": {"en": "Minimum date", "fr": "date minimale"},
    "date_max": {"en": "Maximum date", "fr": "date maximale"},
    "name": {"en": "name", "fr": "nom"},
    "title": {"en": "title", "fr": "titre"},
    "type": {"en": "type", "fr": "type"},
    "notes": {"en": "additional notes", "fr": "notes complémentaires"},
    "languages": {"en": "language", "fr": "langue"},
    "is_public": {"en": "make it public", "fr": "rendre public"},
    "unknown": {"en": "unknown", "fr": "inconnu"},
}


def no_info(field):
    if APP_LANG == "en":
        return f"unknown {field}"
    if APP_LANG == "fr":
        return f"{field} inconnu"
    return "???"


def get_fieldname(field, fields, plural=False, capitalize=False):
    if field in fields:
        f = fields[field][APP_LANG].capitalize()
        return pluralize(f) if plural else f

    if field[0].isupper():
        model = f"{MODEL_NAMES[field][APP_LANG].capitalize()}"
        return pluralize(model) if plural else model

    if field in common_fields:
        f = common_fields[field][APP_LANG].capitalize()
        return pluralize(f) if plural else f

    if field.startswith("no_"):
        field = field[3:]
        if field in fields:
            return no_info(fields[field][APP_LANG]).capitalize()

    return "???"
