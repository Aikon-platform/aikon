import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

from .base import ENV

# Load the appropriate settings file based on the TARGET environment variable

if ENV("TARGET", default="").strip() == "dev":
    from .dev import *
elif ENV("TARGET", default="").strip() == "prod":
    from .prod import *
else:
    raise ValueError("TARGET environment variable must be either 'dev' or 'prod'")
