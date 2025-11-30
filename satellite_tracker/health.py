from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError


def health_status(request):
    """Return a simple JSON response describing application health."""
    status = {
        "app": "ok",
        "database": "ok",
    }
    try:
        connections["default"].cursor()
    except OperationalError:
        status["app"] = "degraded"
        status["database"] = "error"
        return JsonResponse(status, status=503)

    return JsonResponse(status)
