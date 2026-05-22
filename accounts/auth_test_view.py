from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model, authenticate
from django.views.decorators.csrf import csrf_exempt
import json

User = get_user_model()


@csrf_exempt
@require_http_methods(["POST"])
def test_admin_auth(request):
    """Test authentication endpoint"""
    try:
        data = json.loads(request.body) if request.body else {}
    except:
        data = {}
    
    email = data.get('email') or request.POST.get('email', '')
    password = data.get('password') or request.POST.get('password', '')
    
    results = {
        'email_provided': bool(email),
        'password_provided': bool(password),
        'steps': []
    }
    
    # Step 1: Find user
    user = User.objects.filter(email__iexact=email).first()
    results['steps'].append({
        'step': 'Find user by email',
        'email': email,
        'found': bool(user),
        'user_id': user.id if user else None
    })
    
    if not user:
        return JsonResponse(results, status=400)
    
    # Step 2: Check is_active
    results['steps'].append({
        'step': 'Check is_active',
        'is_active': user.is_active
    })
    
    if not user.is_active:
        return JsonResponse(results, status=400)
    
    # Step 3: Check password
    password_valid = user.check_password(password)
    results['steps'].append({
        'step': 'Check password',
        'password_valid': password_valid
    })
    
    if not password_valid:
        return JsonResponse(results, status=400)
    
    # Step 4: Check admin flags
    results['steps'].append({
        'step': 'Check admin flags',
        'is_admin': user.is_admin,
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff
    })
    
    has_admin = user.is_admin or user.is_superuser
    if not has_admin:
        return JsonResponse(results, status=400)
    
    # Step 5: Try Django authenticate
    auth_user = authenticate(username=email, password=password)
    results['steps'].append({
        'step': 'Django authenticate()',
        'authenticated': bool(auth_user),
        'auth_user_id': auth_user.id if auth_user else None
    })
    
    # All checks passed!
    results['final_status'] = 'SUCCESS - All checks passed'
    results['user_data'] = {
        'id': user.id,
        'email': user.email,
        'is_admin': user.is_admin,
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff,
        'is_active': user.is_active
    }
    
    return JsonResponse(results)
