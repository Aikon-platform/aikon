from django.contrib import admin

from vhsapp.utils.constants import (
    SITE_HEADER,
    SITE_TITLE,
    SITE_INDEX_TITLE,
)


admin.site.site_header = SITE_HEADER
admin.site.site_title = SITE_TITLE
admin.site.index_title = SITE_INDEX_TITLE


class UnregisteredAdmin(admin.ModelAdmin):
    """
    Abstract class used for models that don't have a form accessible from the admin index
    But that exists as sub-forms within main forms (i.e. Witness & Series)
    """

    class Meta:
        abstract = True

    list_per_page = 5

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index
        """
        return {}
