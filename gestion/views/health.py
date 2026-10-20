from django.http import HttpResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    """Return a minimal response for the load balancer without touching the database."""
    return HttpResponse("ok", content_type="text/plain")
