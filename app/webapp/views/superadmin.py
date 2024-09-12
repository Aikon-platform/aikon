"""
VIEWS THAT SERVE AS ENDPOINTS
TO PERFORM ACTIONS ON THE DATABASE OR THE APP
TO BE USED ONLY BY SUPER ADMINS FOR MANAGING PURPOSES
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from app.webapp.views import is_superuser

from app.webapp.models.work import Work


@user_passes_test(is_superuser)
def list_empty_works(request):
    # List all works that have no witnesses
    empty_works = []
    works = Work.objects.all()
    for w in works:
        if w.get_witnesses().count() == 0:
            wjson = w.json
            try:
                w.delete()
                empty_works.append(wjson)
            except Exception as e:
                print(e)

    return JsonResponse(
        {
            "deleted works": empty_works,
            "count": len(empty_works),
        }
    )
