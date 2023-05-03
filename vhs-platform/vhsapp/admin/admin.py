from django.contrib import admin

from vhsapp.utils.constants import (
    SITE_HEADER,
    SITE_TITLE,
    SITE_INDEX_TITLE,
)


admin.site.site_header = SITE_HEADER
admin.site.site_title = SITE_TITLE
admin.site.index_title = SITE_INDEX_TITLE
