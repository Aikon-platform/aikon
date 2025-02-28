from django.http import JsonResponse


def test(request, wit_ref=None):
    from app.webapp.tasks import test

    test.delay("Hello world.")
    return JsonResponse({"response": "OK"}, status=200)


def test_error(request):
    """
    This view will raise an exception to test the error email notification.
    """
    raise Exception("Test exception to verify error emails are working.")
