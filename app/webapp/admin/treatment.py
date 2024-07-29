from django.contrib import admin, messages

from app.config.settings import APP_LANG
from app.webapp.admin import UnregisteredAdmin
from app.webapp.models.series import Series
from app.webapp.models.treatment import Treatment
from app.webapp.models.witness import Witness
from app.webapp.models.work import Work


@admin.register(Treatment)
class TreatmentAdmin(UnregisteredAdmin):
    search_fields = (
        "task_type",
        "set_id",
    )
    list_filter = ("task_type",)

    change_form_template = "admin/form.html"
    list_per_page = 100

    def save_model(self, request, obj, form, change):
        # called on submission of form
        if not obj.requested_by:
            obj.requested_by = request.user
        obj.save()

        witnesses = []

        for object, value in obj.treated_objects.items():
            if object == "witnesses" and value["ids"]:
                for id in value["ids"]:
                    try:
                        witness = Witness.objects.filter(id=id).all()
                        witnesses.extend(witness)
                    except:
                        pass
            elif object == "series" and value["ids"]:
                for id in value["ids"]:
                    try:
                        witness = Series.objects.filter(id=id).first().get_witnesses()
                        witnesses.extend(witness)
                    except:
                        pass
            elif object == "works" and value["ids"]:
                for id in value["ids"]:
                    try:
                        witness = Work.objects.filter(id=id).first().get_witnesses()
                        witnesses.extend(witness)
                    except:
                        pass
            # elif object == "digitizations":

        obj.start_task(request, witnesses)
