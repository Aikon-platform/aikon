from app.config.settings import APP_LANG
from app.webapp.models.utils.constants import MODEL_NAMES


common_fields = {
    "date_min": {"en": "Minimum date", "fr": "Terminus Post Quem"},
    "date_max": {"en": "Maximum date", "fr": "Terminus Ante Quem"},
    "name": {"en": "name", "fr": "nom"},
    "title": {"en": "title", "fr": "titre"},
    "type": {"en": "type", "fr": "type"},
    "note": {"en": "additional notes", "fr": "notes complémentaires"},
    "is_public": {"en": "Make it public", "fr": "Rendre public"},
}


def get_fieldname(field, fields, plural=False):
    # add try / except
    # add pluralize method

    if field in fields:
        return fields[field][APP_LANG].capitalize()

    if field[0].isupper():
        return MODEL_NAMES[field][APP_LANG].capitalize()

    if field in common_fields:
        return common_fields[field][APP_LANG].capitalize()

    return "???"
