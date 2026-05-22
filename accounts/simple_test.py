from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model

User = get_user_model()


@require_http_methods(["GET"])
def simple_admin_test(request):
    """Simple endpoint to test admin user"""
    try:
        user = User.objects.get(email='josuekabalisa@gmail.com')
        return JsonResponse({
            'found': True,
            'email': user.email,
            'is_active': user.is_active,
            'is_admin': user.is_admin,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'password_correct': user.check_password('Uwamahor12345@@'),
            'can_login': user.is_active and (user.is_admin or user.is_superuser),
            'total_users': User.objects.count()
        })
    except User.DoesNotExist:
        return JsonResponse({'found': False, 'total_users': User.objects.count()})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
