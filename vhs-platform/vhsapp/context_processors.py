from vhs.settings import SAS_APP_URL, APP_LANG
from vhsapp.utils.constants import APP_NAME_UPPER, APP_NAME


def global_variables(request):
    """
    A context processor that adds global variables to the context of all rendered templates
    """
    return {
        "APP_NAME": APP_NAME,
        "APP_LANG": APP_LANG,
        "APP_NAME_UPPER": APP_NAME_UPPER,
        "SAS_APP_URL": SAS_APP_URL,
    }
