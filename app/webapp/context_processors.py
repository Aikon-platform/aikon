from app.config.settings import (
    SAS_APP_URL,
    APP_LANG,
    APP_URL,
    CANTALOUPE_APP_URL,
    APP_NAME,
    WEBAPP_NAME,
)
from app.webapp.utils.constants import APP_NAME_UPPER, COPYRIGHT
from app.webapp.models.utils.constants import (
    MS,
    VOL,
    WIT,
    MS_ABBR,
    VOL_ABBR,
    WIT_ABBR,
    IMG_ABBR,
    PDF_ABBR,
    MAN_ABBR,
    WIT_CHANGE,
    TPR,
    WPR,
    TPR_ABBR,
    WPR_ABBR,
)


def global_variables(request):
    """
    Add global variables to the context of all rendered templates
    """
    return {
        "APP_NAME": APP_NAME,
        "APP_LANG": APP_LANG,
        "APP_NAME_UPPER": APP_NAME_UPPER,
        "WEBAPP_NAME": WEBAPP_NAME,
        "COPYRIGHT": COPYRIGHT,
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
        "IMG_ABBR": IMG_ABBR,
        "PDF_ABBR": PDF_ABBR,
        "MAN_ABBR": MAN_ABBR,
        "WIT_CHANGE": WIT_CHANGE,
        "TPR": TPR,
        "WPR": WPR,
        "TPR_ABBR": TPR_ABBR,
        "WPR_ABBR": WPR_ABBR,
    }
