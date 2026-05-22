from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from accounts.models import User


@require_http_methods(["GET"])
def debug_admin_status(request):
    """Debug endpoint to check admin user status"""
    try:
        user = User.objects.filter(email='josuekabalisa@gmail.com').first()
        
        if not user:
            return JsonResponse({
                'exists': False,
                'message': 'User not found',
                'total_users': User.objects.count()
            })
        
        return JsonResponse({
            'exists': True,
            'email': user.email,
            'is_active': user.is_active,
            'is_admin': user.is_admin,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'password_valid': user.check_password('Uwamahor12345@@'),
            'total_users': User.objects.count()
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
