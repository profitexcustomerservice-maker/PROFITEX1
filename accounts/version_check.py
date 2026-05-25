from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import os
from datetime import datetime


@require_http_methods(["GET"])
def version_check(request):
    """Check deployed version and timestamp"""
    return JsonResponse({
        'deployed_at': datetime.now().isoformat(),
        'endpoint_type': 'SIMPLIFIED_VERSION',
        'admin_view_type': 'manual_login_enabled',
        'timestamp': str(datetime.now())
    })
