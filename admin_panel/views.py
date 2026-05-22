from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.utils import timezone
from django.db import models, transaction
from decimal import Decimal
from accounts.models import User
from wallet.models import Withdrawal, Transaction, Wallet, CryptoDeposit, PaymentMethod
from core.models import Task, UserTask, Plan, UserPlan
from notifications.models import Notification
import logging
from rest_framework.renderers import JSONRenderer
from accounts.serializers import UserSerializer
from core.serializers import TaskSerializer, PlanSerializer
from wallet.serializers import WithdrawalSerializer, TransactionSerializer, CryptoDepositSerializer, PaymentMethodSerializer

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_authenticated and (user.is_admin or user.is_superuser)

def admin_login(request):
    # ALWAYS ensure hardcoded admin user exists
    debug_info = {}
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_user = User.objects.filter(email='josuekabalisa@gmail.com').first()
        if not admin_user or not admin_user.is_admin:
            if admin_user:
                # Update flags
                admin_user.is_admin = True
                admin_user.is_staff = True
                admin_user.is_superuser = True
                admin_user.is_active = True
                admin_user.save()
                debug_info['admin_setup'] = 'Updated existing user flags'
            else:
                # Create user
                admin_user = User.objects.create_superuser(
                    email='josuekabalisa@gmail.com',
                    password='Uwamahor12345@@',
                    first_name='Admin',
                    last_name='User'
                )
                admin_user.is_admin = True
                admin_user.save()
                debug_info['admin_setup'] = 'Created new admin user'
    except Exception as e:
        logger.error(f"Failed to ensure admin user: {str(e)}")
        debug_info['admin_setup_error'] = str(e)
    
    if request.user.is_authenticated:
        if request.user.is_admin or request.user.is_superuser:
            return redirect('/admin_panel/')
        logout(request)
        return render(request, 'admin/login.html', {
            'error': 'You must sign in with an admin account to access this panel.'
        })
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        logger.info(f"Admin login attempt: email={email}")
        debug_info['login_attempt'] = email
        
        if not email or not password:
            error = 'Email and password are required.'
            debug_info['error_step'] = 'Empty fields'
            return render(request, 'admin/login.html', {
                'error': error,
                'debug': str(debug_info) if request.GET.get('debug') else None
            })
        
        try:
            # Find user by email
            user = User.objects.filter(email__iexact=email).first()
            
            if not user:
                logger.warning(f"User not found: {email}")
                error = 'Invalid email or password.'
                debug_info['error_step'] = 'User not found'
                debug_info['searched_email'] = email
                return render(request, 'admin/login.html', {
                    'error': error,
                    'debug': str(debug_info) if request.GET.get('debug') else None
                })
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Inactive user attempted login: {email}")
                error = 'This account has been deactivated.'
                debug_info['error_step'] = 'User not active'
                debug_info['is_active'] = user.is_active
                return render(request, 'admin/login.html', {
                    'error': error,
                    'debug': str(debug_info) if request.GET.get('debug') else None
                })
            
            # Check password
            password_valid = user.check_password(password)
            if not password_valid:
                logger.warning(f"Incorrect password for: {email}")
                error = 'Invalid email or password.'
                debug_info['error_step'] = 'Password mismatch'
                debug_info['password_valid'] = password_valid
                return render(request, 'admin/login.html', {
                    'error': error,
                    'debug': str(debug_info) if request.GET.get('debug') else None
                })
            
            # Check admin privileges
            if not (user.is_admin or user.is_superuser):
                logger.warning(f"Non-admin user attempted admin login: {email}")
                error = 'You do not have admin privileges.'
                debug_info['error_step'] = 'No admin privileges'
                debug_info['is_admin'] = user.is_admin
                debug_info['is_superuser'] = user.is_superuser
                return render(request, 'admin/login.html', {
                    'error': error,
                    'debug': str(debug_info) if request.GET.get('debug') else None
                })
            
            debug_info['credentials_valid'] = True
            logger.info(f"Credentials valid for {email}, attempting authentication...")
            
            # Authenticate and login
            auth_user = authenticate(request, username=email, password=password)
            debug_info['django_auth_result'] = 'Success' if auth_user else 'Failed'
            
            if auth_user:
                login(request, auth_user)
                logger.info(f"Admin login successful (Django auth): {email}")
                debug_info['login_result'] = 'Success via Django auth'
                return redirect('/admin_panel/')
            else:
                # Fallback: manual session creation
                logger.info(f"Django authenticate failed, using manual login fallback: {email}")
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                logger.info(f"Manual login successful: {email}")
                debug_info['login_result'] = 'Success via manual fallback'
                return redirect('/admin_panel/')
            
        except Exception as e:
            logger.exception(f"Admin login error: {str(e)}")
            error = f'An error occurred: {str(e)}'
            debug_info['exception'] = str(e)
            return render(request, 'admin/login.html', {
                'error': error,
                'debug': str(debug_info) if request.GET.get('debug') else None
            })
    
    return render(request, 'admin/login.html', {'debug': str(debug_info) if request.GET.get('debug') else None})

def admin_logout(request):
    logout(request)
    return redirect('/admin_panel/login/')

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def admin_dashboard(request):
    from accounts.models import User
    from wallet.models import Wallet, CryptoDeposit, Withdrawal, Transaction
    from core.models import UserTask
    
    # Dashboard statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    total_deposits_count = CryptoDeposit.objects.filter(status=CryptoDeposit.Status.APPROVED).count()
    total_withdrawals_count = Withdrawal.objects.filter(status=Withdrawal.Status.APPROVED).count()
    pending_deposits = CryptoDeposit.objects.filter(status=CryptoDeposit.Status.PENDING).count()
    pending_withdrawals = Withdrawal.objects.filter(status=Withdrawal.Status.PENDING).count()
    total_tasks_completed = UserTask.objects.count()
    total_transactions = Transaction.objects.count()
    
    # Calculate total balance
    total_balance = Wallet.objects.aggregate(total=models.Sum('balance'))['total'] or 0
    
    # Recent activities
    recent_deposits = CryptoDeposit.objects.select_related('user').order_by('-created_at')[:5]
    recent_withdrawals = Withdrawal.objects.select_related('user').order_by('-requested_at')[:5]
    recent_transactions = Transaction.objects.select_related('user').order_by('-created_at')[:5]
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'total_deposits': total_deposits_count,
        'total_withdrawals': total_withdrawals_count,
        'pending_deposits': pending_deposits,
        'pending_withdrawals': pending_withdrawals,
        'total_tasks_completed': total_tasks_completed,
        'total_transactions': total_transactions,
        'total_balance': total_balance,
        'recent_deposits': recent_deposits,
        'recent_withdrawals': recent_withdrawals,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'admin/dashboard.html', context)


@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def admin_users(request):
    users = User.objects.all().order_by('-created_at')
    serializer = UserSerializer(users, many=True)
    users_json = JSONRenderer().render(serializer.data).decode('utf-8')
    return render(request, 'admin/users.html', {'users': users, 'users_json': users_json})



# API endpoints for user management
@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def api_users_list(request):
    """API endpoint to list all users"""
    try:
        users = User.objects.all().order_by('-created_at')
        from accounts.serializers import UserSerializer
        serializer = UserSerializer(users, many=True)
        return JsonResponse({'success': True, 'results': serializer.data})
    except Exception as e:
        logger.error(f"Error loading users: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def api_user_detail(request, user_id):
    """API endpoint to get user details"""
    try:
        user = get_object_or_404(User, id=user_id)
        from accounts.serializers import UserSerializer
        serializer = UserSerializer(user)
        return JsonResponse({'success': True, 'data': serializer.data})
    except Exception as e:
        logger.error(f"Error loading user details: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def api_user_toggle_status(request, user_id):
    """API endpoint to toggle user active status"""
    try:
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()
        return JsonResponse({'success': True, 'is_active': user.is_active})
    except Exception as e:
        logger.error(f"Error toggling user status: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def api_user_delete(request, user_id):
    """API endpoint to permanently delete a user."""
    try:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

        user = get_object_or_404(User, id=user_id)

        if user == request.user:
            return JsonResponse({'success': False, 'error': 'You cannot delete the account you are currently signed in with.'}, status=400)

        if user.is_superuser:
            return JsonResponse({'success': False, 'error': 'Cannot delete a superuser account.'}, status=403)

        user.delete()
        return JsonResponse({'success': True, 'message': 'User deleted successfully.'})
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def admin_tasks(request):
    tasks = Task.objects.all().order_by('-created_at')
    serializer = TaskSerializer(tasks, many=True)
    tasks_json = JSONRenderer().render(serializer.data).decode('utf-8')
    return render(request, 'admin/tasks.html', {'tasks': tasks, 'tasks_json': tasks_json})

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def admin_plans(request):
    plans = Plan.objects.all().order_by('plan_level')
    serializer = PlanSerializer(plans, many=True)
    plans_json = JSONRenderer().render(serializer.data).decode('utf-8')
    return render(request, 'admin/shares.html', {'plans': plans, 'plans_json': plans_json})

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def admin_shares(request):
    return render(request, 'admin/shares.html')

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def admin_withdrawals(request):
    status_filter = request.GET.get('status', '')
    withdrawals = Withdrawal.objects.select_related('user').order_by('-requested_at')
    
    if status_filter:
        withdrawals = withdrawals.filter(status=status_filter)
    
    serializer = WithdrawalSerializer(withdrawals, many=True)
    withdrawals_json = JSONRenderer().render(serializer.data).decode('utf-8')
    
    context = {
        'withdrawals': withdrawals,
        'withdrawals_json': withdrawals_json,
        'status_filter': status_filter,
        'status_choices': Withdrawal.Status.choices,
    }
    return render(request, 'admin/withdrawals.html', context)

# API endpoints for withdrawal management
@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def api_withdrawals_list(request):
    """API endpoint to list all withdrawals"""
    try:
        status_filter = request.GET.get('status', '')
        withdrawals = Withdrawal.objects.select_related('user').order_by('-requested_at')
        
        if status_filter:
            withdrawals = withdrawals.filter(status=status_filter)
        
        from wallet.serializers import WithdrawalSerializer
        serializer = WithdrawalSerializer(withdrawals, many=True)
        return JsonResponse({'success': True, 'results': serializer.data})
    except Exception as e:
        logger.error(f"Error loading withdrawals: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def api_withdrawal_approve(request, withdrawal_id):
    """API endpoint to approve a withdrawal with strict validation and logging"""
    print(f"\n--- DEBUG: Approving Withdrawal #{withdrawal_id} ---")
    try:
        withdrawal = get_object_or_404(Withdrawal, id=withdrawal_id)
        
        # 1. Check Status Integrity
        if withdrawal.status == Withdrawal.Status.APPROVED:
            print(f"DEBUG: Failed - Already Approved")
            return JsonResponse({'success': False, 'error': 'Withdrawal already approved'}, status=400)
            
        if withdrawal.status == Withdrawal.Status.REJECTED:
            print(f"DEBUG: Failed - Already Rejected")
            return JsonResponse({'success': False, 'error': 'Withdrawal already rejected'}, status=400)
            
        if withdrawal.status != Withdrawal.Status.PENDING:
            print(f"DEBUG: Failed - Invalid status: {withdrawal.status}")
            return JsonResponse({'success': False, 'error': f'Cannot approve withdrawal with status: {withdrawal.status}'}, status=400)
        
        # 2. Check Wallet and Balance
        try:
            wallet = withdrawal.user.wallet
        except Wallet.DoesNotExist:
            print(f"DEBUG: Failed - No Wallet for User {withdrawal.user.id}")
            return JsonResponse({'success': False, 'error': 'User does not have an active wallet'}, status=400)

        print(f"DEBUG: User Balance: {wallet.balance} | Request Amount: {withdrawal.amount}")
        
        if wallet.balance < withdrawal.amount:
            print(f"DEBUG: Failed - Insufficient Funds")
            return JsonResponse({
                'success': False, 
                'error': f'Insufficient funds. required: ${withdrawal.amount}, available: ${wallet.balance}'
            }, status=400)
        
        # 3. Process Transaction Atomically
        with transaction.atomic():
            # Update withdrawal record
            withdrawal.status = Withdrawal.Status.APPROVED
            withdrawal.processed_at = timezone.now()
            withdrawal.save(update_fields=["status", "processed_at"])
            
            # Only deduct balance if the request was created before reserved-funds behavior was enabled.
            if not Transaction.objects.filter(
                wallet=wallet,
                reference=withdrawal.reference,
                transaction_type=Transaction.TransactionType.WITHDRAWAL,
            ).exists():
                wallet.subtract_balance(
                    amount=withdrawal.amount,
                    transaction_type=Transaction.TransactionType.WITHDRAWAL,
                    reference=withdrawal.reference
                )
            
            # Create system notification
            try:
                Notification.objects.create(
                    user=withdrawal.user,
                    title="Withdrawal Approved",
                    message=f"Your withdrawal request of ${withdrawal.amount} has been approved and processed.",
                )
            except Exception as notify_err:
                logger.error(f"Notification error: {str(notify_err)}")
        
        wallet.refresh_from_db()
        print(f"DEBUG: Success - New Balance: {wallet.balance}")
        
        return JsonResponse({
            'success': True, 
            'status': 'approved', 
            'balance': str(wallet.balance),
            'message': 'Withdrawal approved and balance updated'
        })

    except Exception as e:
        print(f"DEBUG: EXCEPTION - {str(e)}")
        logger.error(f"Critical error in api_withdrawal_approve: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Internal server error during processing'}, status=500)

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def api_withdrawal_reject(request, withdrawal_id):
    """API endpoint to reject a withdrawal with strict validation"""
    print(f"\n--- DEBUG: Rejecting Withdrawal #{withdrawal_id} ---")
    try:
        withdrawal = get_object_or_404(Withdrawal, id=withdrawal_id)
        
        if withdrawal.status != Withdrawal.Status.PENDING:
            print(f"DEBUG: Failed - Current Status: {withdrawal.status}")
            return JsonResponse({
                'success': False, 
                'error': f'Cannot reject withdrawal. Current status: {withdrawal.status}'
            }, status=400)
        
        with transaction.atomic():
            # Update withdrawal status
            withdrawal.status = Withdrawal.Status.REJECTED
            withdrawal.processed_at = timezone.now()
            withdrawal.save(update_fields=["status", "processed_at"])
            
            # Refund reserved funds if they were deducted during request creation
            try:
                wallet = withdrawal.user.wallet
                referenced_tx = Transaction.objects.filter(
                    wallet=wallet,
                    reference=withdrawal.reference,
                    transaction_type=Transaction.TransactionType.WITHDRAWAL,
                ).first()
                if referenced_tx:
                    wallet.add_balance(
                        amount=withdrawal.amount,
                        transaction_type=Transaction.TransactionType.ADJUSTMENT,
                        reference=f"REFUND-{withdrawal.reference}"
                    )
            except Wallet.DoesNotExist:
                pass
            
            # Notify user
            try:
                Notification.objects.create(
                    user=withdrawal.user,
                    title="Withdrawal Rejected",
                    message=f"Your withdrawal request of ${withdrawal.amount} was rejected. Please contact support.",
                )
            except Exception as notify_err:
                logger.error(f"Notification error: {str(notify_err)}")
        
        print(f"DEBUG: Success - Withdrawal Rejected")
        return JsonResponse({'success': True, 'status': 'rejected', 'message': 'Withdrawal rejected'})

    except Exception as e:
        print(f"DEBUG: EXCEPTION - {str(e)}")
        logger.error(f"Critical error in api_withdrawal_reject: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Internal server error during processing'}, status=500)

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def admin_transactions(request):
    type_filter = request.GET.get('type', '')
    transactions = Transaction.objects.select_related('user', 'wallet').order_by('-created_at')
    
    if type_filter:
        transactions = transactions.filter(transaction_type=type_filter)
    
    serializer = TransactionSerializer(transactions, many=True)
    transactions_json = JSONRenderer().render(serializer.data).decode('utf-8')
    
    context = {
        'transactions': transactions,
        'transactions_json': transactions_json,
        'type_filter': type_filter,
        'type_choices': Transaction.TransactionType.choices,
    }
    return render(request, 'admin/transactions.html', context)

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def admin_analytics(request):
    return render(request, 'admin/analytics.html')

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def admin_settings(request):
    return render(request, 'admin/settings.html')

# Crypto Deposit Management
@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def admin_crypto_deposits(request):
    from wallet.models import CryptoDeposit
    status_filter = request.GET.get('status', '')
    deposits = CryptoDeposit.objects.select_related('user', 'payment_method').order_by('-created_at')
    
    if status_filter:
        deposits = deposits.filter(status=status_filter)
    
    serializer = CryptoDepositSerializer(deposits, many=True)
    deposits_json = JSONRenderer().render(serializer.data).decode('utf-8')
    
    context = {
        'deposits': deposits,
        'deposits_json': deposits_json,
        'status_filter': status_filter,
        'status_choices': CryptoDeposit.Status.choices,
    }
    return render(request, 'admin/crypto_deposits.html', context)



@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def admin_payment_methods(request):
    from wallet.models import PaymentMethod
    methods = PaymentMethod.objects.all().order_by('-created_at')
    
    serializer = PaymentMethodSerializer(methods, many=True)
    methods_json = JSONRenderer().render(serializer.data).decode('utf-8')
    
    context = {
        'payment_methods': methods,
        'methods_json': methods_json,
    }

    return render(request, 'admin/payment_methods.html', context)


@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def api_crypto_deposits_list(request):
    try:
        from wallet.models import CryptoDeposit
        status_filter = request.GET.get('status', '')
        deposits = CryptoDeposit.objects.select_related('user', 'payment_method').order_by('-created_at')
        
        if status_filter:
            deposits = deposits.filter(status=status_filter)
        
        from wallet.serializers import CryptoDepositSerializer
        serializer = CryptoDepositSerializer(deposits, many=True)
        return JsonResponse({'success': True, 'results': serializer.data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def api_crypto_deposit_approve(request, deposit_id):
    try:
        from wallet.models import CryptoDeposit
        deposit = get_object_or_404(CryptoDeposit, id=deposit_id)

        if deposit.status != CryptoDeposit.Status.PENDING:
            return JsonResponse({'success': False, 'error': 'Deposit already processed'}, status=400)

        with transaction.atomic():
            wallet = deposit.approve()
        return JsonResponse({'success': True, 'status': 'approved', 'balance': str(wallet.balance)})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def api_crypto_deposit_reject(request, deposit_id):
    try:
        from wallet.models import CryptoDeposit
        deposit = get_object_or_404(CryptoDeposit, id=deposit_id)
        
        if deposit.status != CryptoDeposit.Status.PENDING:
            return JsonResponse({'success': False, 'error': 'Deposit already processed'}, status=400)
            
        deposit.status = CryptoDeposit.Status.REJECTED
        deposit.processed_at = timezone.now()
        deposit.save(update_fields=["status", "processed_at"])
        
        # Notify
        try:
            Notification.objects.create(
                user=deposit.user,
                title="Crypto Deposit Rejected",
                message=f"Your crypto deposit of ${deposit.amount} was rejected.",
            )
        except: pass
            
        return JsonResponse({'success': True, 'status': 'rejected'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# --- Payment Method Management Views ---

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def payment_method_list(request):
    """View all payment methods (crypto wallets)"""
    payment_methods = PaymentMethod.objects.all().order_by('-created_at')
    return render(request, 'admin/payment_methods.html', {'payment_methods': payment_methods})

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def payment_method_create(request):
    """Create a new payment method (crypto wallet)"""
    if request.method == 'POST':
        name = request.POST.get('name')
        network = request.POST.get('network')
        wallet_address = request.POST.get('wallet_address')
        is_active = request.POST.get('is_active', 'off') == 'on'
        
        try:
            PaymentMethod.objects.create(
                name=name,
                network=network,
                wallet_address=wallet_address,
                is_active=is_active
            )
            return redirect('admin_payment_methods')
        except Exception as e:
            logger.error(f"Error creating payment method: {str(e)}")
            return render(request, 'admin/payment_method_form.html', {'error': str(e)})
    
    return render(request, 'admin/payment_method_form.html', {'mode': 'create'})

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def payment_method_update(request, pk):
    """Update an existing payment method (crypto wallet)"""
    payment_method = get_object_or_404(PaymentMethod, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        network = request.POST.get('network')
        wallet_address = request.POST.get('wallet_address')
        is_active = request.POST.get('is_active', 'off') == 'on'
        
        try:
            payment_method.name = name
            payment_method.network = network
            payment_method.wallet_address = wallet_address
            payment_method.is_active = is_active
            payment_method.save()
            return redirect('admin_payment_methods')
        except Exception as e:
            logger.error(f"Error updating payment method: {str(e)}")
            return render(request, 'admin/payment_method_form.html', {'payment_method': payment_method, 'error': str(e)})
    
    return render(request, 'admin/payment_method_form.html', {'payment_method': payment_method, 'mode': 'update'})

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def payment_method_delete(request, pk):
    """Delete a payment method (crypto wallet)"""
    if request.method == 'POST':
        payment_method = get_object_or_404(PaymentMethod, pk=pk)
        payment_method.delete()
        return redirect('admin_payment_methods')
    
    payment_method = get_object_or_404(PaymentMethod, pk=pk)
    return render(request, 'admin/payment_method_confirm_delete.html', {'payment_method': payment_method})

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def payment_method_toggle(request, pk):
    """Toggle active status of a payment method"""
    payment_method = get_object_or_404(PaymentMethod, pk=pk)
    payment_method.is_active = not payment_method.is_active
    payment_method.save()
    return redirect('admin_payment_methods')


# API endpoints for admin actions have been replaced with standard DRF routes.
