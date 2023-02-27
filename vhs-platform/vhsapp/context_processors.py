from vhs.settings import SAS_APP_URL
from vhsapp.utils.constants import APP_NAME_UPPER


def global_variables(request):
    """
    A context processor that adds global variables to the context of all rendered templates
    """
    return {"APP_NAME_UPPER": APP_NAME_UPPER, "SAS_APP_URL": SAS_APP_URL}
