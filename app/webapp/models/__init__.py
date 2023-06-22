from app.webapp.models.utils.constants import MS, VOL, MS_ABBR, VOL_ABBR


def get_wit_abbr(wit=MS):
    return MS_ABBR if wit == MS else VOL_ABBR


def get_wit_type(wit=MS_ABBR):
    return MS if wit == MS_ABBR else VOL
