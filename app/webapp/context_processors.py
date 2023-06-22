from app.config.settings import (
    SAS_APP_URL,
    APP_LANG,
    APP_URL,
    CANTALOUPE_APP_URL,
    APP_NAME,
)
from app.webapp.utils.constants import APP_NAME_UPPER
from app.webapp.models.utils.constants import MS, VOL, WIT, MS_ABBR, VOL_ABBR, WIT_ABBR


def global_variables(request):
    """
    A context processor that adds global variables to the context of all rendered templates
    platform
    """
    return {
        "APP_NAME": APP_NAME,
        "APP_LANG": APP_LANG,
        "APP_NAME_UPPER": APP_NAME_UPPER,
        "SAS_APP_URL": SAS_APP_URL,
        "APP_URL": APP_URL,
        "CANTALOUPE_APP_URL": CANTALOUPE_APP_URL,
        # TODO: add model names and abbreviation
        "MS": MS,
        "VOL": VOL,
        "WIT": WIT,
        "MS_ABBR": MS_ABBR,
        "VOL_ABBR": VOL_ABBR,
        "WIT_ABBR": WIT_ABBR,
    }
