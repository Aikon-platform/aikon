from app.config.settings import APP_LANG
from app.webapp.models.utils.constants import MODEL_NAMES


common_fields = {
    "date_min": {"en": "Minimum date", "fr": "date minimale"},
    "date_max": {"en": "Maximum date", "fr": "date maximale"},
    "name": {"en": "name", "fr": "nom"},
    "title": {"en": "title", "fr": "titre"},
    "type": {"en": "type", "fr": "type"},
    "notes": {"en": "additional notes", "fr": "éléments descriptifs du contenu"},
    "languages": {"en": "language", "fr": "langue"},
    "is_public": {"en": "Make it public", "fr": "Rendre public"},
}


def no_info(field):
    if APP_LANG == "en":
        return f"unknown {field}"
    if APP_LANG == "fr":
        return f"{field} inconnu"
    return "???"


def get_fieldname(field, fields, plural=False, capitalize=False):
    # TODO add pluralize method

    if field in fields:
        return fields[field][APP_LANG].capitalize()

    if field[0].isupper():
        return f"{MODEL_NAMES[field][APP_LANG].capitalize()}{'s' if plural else ''}"

    if field in common_fields:
        return common_fields[field][APP_LANG].capitalize()

    if field.startswith("no_"):
        field = field[3:]
        if field in fields:
            return no_info(fields[field][APP_LANG]).capitalize()

    return "???"
