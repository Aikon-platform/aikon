from django.conf import settings


def login_url(request):
    return {"LOGIN_URL": settings.LOGIN_URL}
