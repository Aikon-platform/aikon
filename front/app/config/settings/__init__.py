import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

from .base import ENV

# Load the appropriate settings file based on the TARGET environment variable

tgt = ENV("TARGET", default="").strip()

if tgt == "dev":
    from .dev import *
elif tgt == "docker_local":
    from .docker_local import *
elif tgt == "prod":
    from .prod import *
else:
    raise ValueError("TARGET environment variable must be either 'dev' or 'prod'")
