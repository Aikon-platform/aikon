from vhs.settings import SAS_APP_URL, APP_NAME


def global_variables(request):
    """
    A context processor that adds global variables to the context of all rendered templates
    """
    return {
        "APP_NAME": APP_NAME,
        "APP_NAME_UPPER": APP_NAME.upper(),
        "SAS_APP_URL": SAS_APP_URL,
    }
