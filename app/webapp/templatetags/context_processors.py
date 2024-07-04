from app.config.settings import (
    SAS_APP_URL,
    APP_LANG,
    APP_URL,
    CANTALOUPE_APP_URL,
    APP_NAME,
    WEBAPP_NAME,
    CONTACT_MAIL,
    ADDITIONAL_MODULES,
)
from app.webapp.utils.constants import (
    APP_NAME_UPPER,
    COPYRIGHT,
    MANIFEST_V1,
    MANIFEST_V2,
)
from app.webapp.models.utils.constants import (
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
    CATEGORY_INFO,
    ENTITY_NAMES,
)


def global_variables(request):
    """
    Add global variables to the context of all rendered templates
    """
    constants = {
        "APP_NAME": APP_NAME,
        "APP_LANG": APP_LANG,
        "APP_NAME_UPPER": APP_NAME_UPPER,
        "ADDITIONAL_MODULES": ADDITIONAL_MODULES,
        "CONTACT_MAIL": CONTACT_MAIL,
        "WEBAPP_NAME": WEBAPP_NAME,
        "COPYRIGHT": COPYRIGHT,
        "SAS_APP_URL": SAS_APP_URL,
        "APP_URL": APP_URL,
        "CANTALOUPE_APP_URL": CANTALOUPE_APP_URL,
        "MS_ABBR": MS_ABBR,
        "VOL_ABBR": VOL_ABBR,
        "WIT_ABBR": WIT_ABBR,
        "IMG_ABBR": IMG_ABBR,
        "PDF_ABBR": PDF_ABBR,
        "MAN_ABBR": MAN_ABBR,
        "TPR_ABBR": TPR_ABBR,
        "WPR_ABBR": WPR_ABBR,
        "TPR": TPR,
        "WPR": WPR,
        "WIT_CHANGE": WIT_CHANGE,
        "MANIFEST_V1": MANIFEST_V1,
        "MANIFEST_V2": MANIFEST_V2,
        "CATEGORY_INFO": CATEGORY_INFO,
    }
    return {**constants, **ENTITY_NAMES}
