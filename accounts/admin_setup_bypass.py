from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model, login
from django.test import RequestFactory
import os

User = get_user_model()


@require_http_methods(["GET", "POST"])
def admin_setup_bypass(request):
    """
    EMERGENCY ENDPOINT: Sets up admin user with all flags
    Use: GET /accounts/admin-setup-bypass/?token=<password>
    """
    provided_token = request.GET.get('token') or request.POST.get('token', '')
    expected_token = os.environ.get('SUPERUSER_PASSWORD', 'Uwamahor12345@@')
    
    if provided_token != expected_token:
        return JsonResponse({'error': 'Invalid token'}, status=403)
    
    try:
        admin_email = 'josuekabalisa@gmail.com'
        admin_password = 'Uwamahor12345@@'
        
        # Ensure user exists
        user = User.objects.filter(email=admin_email).first()
        if not user:
            user = User.objects.create_superuser(
                email=admin_email,
                password=admin_password,
                first_name='Admin',
                last_name='User'
            )
            created = True
        else:
            created = False
        
        # Ensure all flags are set
        updated = False
        if not user.is_active:
            user.is_active = True
            updated = True
        if not user.is_admin:
            user.is_admin = True
            updated = True
        if not user.is_staff:
            user.is_staff = True
            updated = True
        if not user.is_superuser:
            user.is_superuser = True
            updated = True
        
        if updated:
            user.save()
        
        # If POST, also log the user in
        if request.method == 'POST':
            login(request, user)
            return JsonResponse({
                'status': 'SUCCESS',
                'action': 'setup_and_login',
                'user_created': created,
                'flags_updated': updated,
                'user_id': user.id,
                'email': user.email,
                'user_logged_in': True
            })
        
        return JsonResponse({
            'status': 'SUCCESS',
            'action': 'setup_only',
            'user_created': created,
            'flags_updated': updated,
            'user_id': user.id,
            'email': user.email,
            'flags': {
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser
            }
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
