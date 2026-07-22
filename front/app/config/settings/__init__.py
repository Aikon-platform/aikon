import warnings

warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

from .base import MODE

if MODE in ("local", "dev"):
    from .dev import *
elif MODE == "prod":
    from .prod import *
else:
    raise ValueError(f"MODE must be 'local', 'dev' or 'prod' (got '{MODE}')")
