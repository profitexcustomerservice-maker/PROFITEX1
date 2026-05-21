from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User
from .serializers import RegisterSerializer, UserSerializer
from .otp_utils import create_and_send_otp, verify_otp
import logging

logger = logging.getLogger(__name__)


class IsAdminUserCustom(permissions.BasePermission):
    """Checks the custom is_admin flag on the User model."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)

# --- DRF Views for API ---

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

class CurrentUserView(generics.RetrieveUpdateAPIView):
    """View to get or update current user profile including profile image"""
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def get_object(self):
        return self.request.user

class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAdminUserCustom,)
    queryset = User.objects.all().order_by("-created_at")

class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAdminUserCustom,)
    queryset = User.objects.all()

class ToggleUserStatusView(APIView):
    permission_classes = (IsAdminUserCustom,)

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()
        return Response({"is_active": user.is_active})

# --- Template Views ---

def home_page(request):
    """Public landing page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, "home.html")

@login_required
def dashboard(request):
    """User dashboard view"""
    # Get user wallet balance
    from wallet.models import Wallet
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    balance = wallet.balance
    
    # Get current plan
    from core.models import UserPlan
    current_plan = UserPlan.objects.filter(user=request.user).first()
    
    # Get completed tasks count
    from core.models import UserTask
    completed_tasks = UserTask.objects.filter(user=request.user).count()
    
    # Get unread notifications
    from notifications.models import Notification
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    
    # Get recent transactions
    from wallet.models import Transaction
    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'balance': balance,
        'current_plan': current_plan,
        'completed_tasks': completed_tasks,
        'unread_notifications': unread_notifications,
        'recent_transactions': recent_transactions,
    }
    return render(request, "dashboard.html", context)

@login_required
def wallet_page(request):
    """User wallet and deposit/withdrawal management"""
    from wallet.models import Wallet, Transaction, Withdrawal, CryptoDeposit
    from core.models import UserPlan
    
    # Get user's wallet balance - create if doesn't exist
    try:
        wallet = Wallet.objects.get(user=request.user)
        balance = wallet.balance
    except Wallet.DoesNotExist:
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        balance = wallet.balance
    
    # Get user's current plan
    current_plan = UserPlan.objects.filter(user=request.user).first()
    
    # Get pending crypto deposits and withdrawals
    # We define 'deposits' as an empty list to satisfy old template logic
    deposits = []
    crypto_deposits = CryptoDeposit.objects.filter(user=request.user, status=CryptoDeposit.Status.PENDING).order_by('-created_at')
    withdrawals = Withdrawal.objects.filter(user=request.user, status=Withdrawal.Status.PENDING).order_by('-requested_at')
    
    # Get transactions
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    from wallet.models import PaymentMethod
    payment_methods = PaymentMethod.objects.filter(is_active=True).order_by('name')
    
    context = {
        'balance': balance,
        'current_plan': current_plan,
        'deposits': deposits,
        'crypto_deposits': crypto_deposits,
        'withdrawals': withdrawals,
        'transactions': transactions,
        'payment_methods': payment_methods,
    }

    return render(request, "wallet.html", context)

@login_required
def profile_page(request):
    return render(request, "profile.html")

def register_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        logger.info(f"SIGNUP DATA: email={email}, first_name={first_name}, last_name={last_name}")
        
        error = None
        if not first_name or len(first_name) < 2:
            error = 'First name must be at least 2 characters.'
        elif not last_name or len(last_name) < 2:
            error = 'Last name must be at least 2 characters.'
        elif not email or '@' not in email:
            error = 'Please enter a valid email address.'
        elif not password or len(password) < 8:
            error = 'Password must be at least 8 characters.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif User.objects.filter(email=email).exists():
            error = 'An account with this email already exists.'

        if error:
            return render(request, "accounts/register.html", {
                'error': error,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
            })

        try:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            logger.info(f"USER CREATED: {user.email}")
            
            # Create wallet for user
            from wallet.models import Wallet
            Wallet.objects.create(user=user)
            logger.info(f"WALLET CREATED for {user.email}")

            authenticated_user = authenticate(request, username=email, password=password)
            if authenticated_user:
                login(request, authenticated_user)
                logger.info(f"USER LOGGED IN after signup: {authenticated_user.email}")
                return redirect('dashboard')

            return render(request, "accounts/register.html", {
                'error': 'Account created but automatic login failed',
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
            })
        except Exception as e:
            logger.error(f"SIGNUP ERROR: {str(e)}")
            return render(request, "accounts/register.html", {
                'error': str(e),
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
            })
    
    return render(request, "accounts/register.html")

def login_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        logger.info(f"LOGIN DATA: email={email}")
        
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Create OTP and send to user's email, then store pending login in session
            otp, sent = create_and_send_otp(user)
            if not otp or not sent:
                logger.error(f"OTP send failed for {email}")
                return render(request, "accounts/login.html", {'error': 'Unable to send verification code. Try again later.', 'email': email})

            if settings.DEBUG and otp:
                request.session['debug_otp_code'] = otp.code

            request.session['pending_login_user_id'] = user.id
            request.session['pending_login_email'] = user.email
            request.session.modified = True
            return redirect('otp_verify')
        else:
            logger.error(f"LOGIN FAILED for {email}")
            return render(request, "accounts/login.html", {'error': 'Invalid email or password', 'email': email})
    
    return render(request, "accounts/login.html")

def logout_page(request):
    logout(request)
    return redirect('login_page')

def otp_verify(request):
    """Verify OTP for a pending login request."""
    pending_user_id = request.session.get('pending_login_user_id')
    email = request.session.get('pending_login_email')
    error = request.session.pop('otp_error', None)

    if not pending_user_id:
        return redirect('login_page')

    user = User.objects.filter(id=pending_user_id).first()
    if not user:
        request.session.pop('pending_login_user_id', None)
        request.session.pop('pending_login_email', None)
        return redirect('login_page')

    debug_otp_code = None
    if settings.DEBUG:
        debug_otp_code = request.session.pop('debug_otp_code', None)

    if request.method == 'POST':
        code = request.POST.get('otp', '').strip()
        ok, message = verify_otp(user, code)
        if ok:
            # Ensure user has a wallet
            from wallet.models import Wallet
            Wallet.objects.get_or_create(user=user)
            
            # Complete login
            login(request, user)
            request.session.pop('pending_login_user_id', None)
            request.session.pop('pending_login_email', None)
            return redirect('dashboard')
        else:
            request.session['otp_error'] = message
            return redirect('otp_verify')

    return render(request, "accounts/otp_verify.html", {'email': email, 'error': error, 'debug_otp_code': debug_otp_code})

def otp_resend(request):
    """Resend OTP for pending login."""
    pending_user_id = request.session.get('pending_login_user_id')
    if not pending_user_id:
        return redirect('login_page')

    user = User.objects.filter(id=pending_user_id).first()
    if not user:
        request.session.pop('pending_login_user_id', None)
        request.session.pop('pending_login_email', None)
        return redirect('login_page')

    otp, sent = create_and_send_otp(user)
    if settings.DEBUG and otp:
        request.session['debug_otp_code'] = otp.code
    if not otp or not sent:
        request.session['otp_error'] = 'Unable to resend code. Try again later.'
    return redirect('otp_verify')

def forgot_password_view(request):
    """Forgot password - send OTP to user's email so they can reset password without support."""
    account_email = ""
    notice = None

    if request.method == 'POST':
        account_email = request.POST.get('email', '').strip()
        user = User.objects.filter(email__iexact=account_email).first()
        if user:
            otp, sent = create_and_send_otp(user)
            if sent:
                # Store pending reset email in session and redirect to reset page
                request.session['pending_reset_email'] = user.email
                if settings.DEBUG and settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
                    request.session['reset_message'] = (
                        'A verification code was generated. In local development, check the server '
                        'terminal/console because email delivery is not configured.'
                    )
                else:
                    request.session['reset_message'] = 'A verification code was sent if the account exists.'
                return redirect('reset_password')
            else:
                notice = 'Failed to send verification code. Try again later. Check the server logs for details.'
        else:
            # Do not reveal whether the account exists
            request.session['pending_reset_email'] = account_email
            request.session['reset_message'] = 'If an account exists we sent a verification code.'
            return redirect('reset_password')

    return render(request, "accounts/forgot_password.html", {'account_email': account_email, 'notice': notice})

def reset_password_view(request):
    """Handle reset-password page using OTP verification and new password setting."""
    pending_email = request.session.get('pending_reset_email')
    message = request.session.pop('reset_message', None)
    error = None

    if request.method == 'POST':
        otp_code = request.POST.get('otp', '').strip()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not pending_email:
            error = 'Session expired. Please request a new code.'
            return render(request, "accounts/reset_password.html", {'email': pending_email or '', 'error': error})

        if password != confirm_password:
            error = 'Passwords do not match.'
            return render(request, "accounts/reset_password.html", {'email': pending_email, 'error': error})

        user = User.objects.filter(email__iexact=pending_email).first()
        if not user:
            error = 'Invalid account.'
            return render(request, "accounts/reset_password.html", {'email': pending_email, 'error': error})

        ok, msg = verify_otp(user, otp_code)
        if not ok:
            error = msg
            return render(request, "accounts/reset_password.html", {'email': pending_email, 'error': error})

        # Set new password
        user.set_password(password)
        user.save(update_fields=['password'])

        # Clear pending reset session
        request.session.pop('pending_reset_email', None)
        return render(request, "accounts/reset_password.html", {'success': True, 'message': 'Your password has been reset successfully.', 'email': user.email})

    return render(request, "accounts/reset_password.html", {'email': pending_email or '', 'message': message})


def reset_password_resend_view(request):
    """Resend reset OTP to the pending reset email (if present)."""
    pending_email = request.session.get('pending_reset_email')
    if not pending_email:
        return redirect('forgot_password')

    user = User.objects.filter(email__iexact=pending_email).first()
    if user:
        otp, sent = create_and_send_otp(user)
        if sent:
            if settings.DEBUG and settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
                request.session['reset_message'] = (
                    'A new verification code was generated. In local development, check the server '
                    'terminal/console because email delivery is not configured.'
                )
            else:
                request.session['reset_message'] = 'A new verification code has been sent.'
        else:
            request.session['reset_message'] = 'Unable to send code. Try again later.'
    else:
        # Non-existent account — still show generic message
        request.session['reset_message'] = 'If an account exists we have sent a verification code.'

    return redirect('reset_password')
