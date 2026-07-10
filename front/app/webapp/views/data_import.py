from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from app.config.settings import ADDITIONAL_MODULES, APP_LANG
from app.webapp.models.treatment import Treatment


class ImportForm(forms.Form):
    source_url = forms.URLField(
        label="Source URL",
        widget=forms.URLInput(attrs={"class": "input"}),
        help_text="URL of a document set or witness JSON export from another AIKON instance "
        "(e.g. https://host/aikon/document-set/13/json)",
    )
    import_regions = forms.BooleanField(
        required=False, initial=True, label="Import region extractions"
    )
    import_similarities = forms.BooleanField(
        required=False, label="Import similarity pairs"
    )
    notify_email = forms.BooleanField(
        required=False, initial=True, label="Notify by email"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "similarity" not in ADDITIONAL_MODULES:
            del self.fields["import_similarities"]


@login_required
def import_records(request):
    form = ImportForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        Treatment.objects.create(
            task_type="import",
            requested_by=request.user,
            notify_email=data["notify_email"],
            api_parameters={
                "source_url": data["source_url"],
                "import_regions": data["import_regions"],
                "import_similarities": data.get("import_similarities", False),
            },
        )
        messages.info(
            request, "Import started" if APP_LANG == "en" else "Import lancé"
        )
        return redirect("webapp:treatment_list")
    return render(request, "webapp/import.html", {"form": form})
