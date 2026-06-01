from django.utils import timezone
from django.shortcuts import render
from rest_framework import permissions, status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from .models import Transaction, Withdrawal, Wallet, PaymentMethod, CryptoDeposit
from .serializers import (
    TransactionSerializer, WithdrawalSerializer,
    PaymentMethodSerializer, CryptoDepositSerializer
)
from django.db import transaction as db_transaction
from notifications.models import Notification
import logging

logger = logging.getLogger(__name__)

# Business rule: Minimum withdrawal amount
MINIMUM_WITHDRAWAL_AMOUNT = 60.00


class IsAdminUserCustom(permissions.BasePermission):
    """Custom permission that checks the is_admin field on the User model."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)

def transactions_page(request):
    """Render the transactions page"""
    user = request.user
    if not user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('/login/')
    
    # Get user's wallet balance
    try:
        balance = user.wallet.balance
    except Wallet.DoesNotExist:
        balance = 0.00
    
    # Get user's transactions
    transactions = Transaction.objects.filter(user=user).select_related('wallet').order_by('-created_at')[:50]

    # Get pending withdrawals
    withdrawals = Withdrawal.objects.filter(user=user).order_by('-requested_at')
    
    context = {
        'balance': balance,
        'transactions': transactions,
        'withdrawals': withdrawals,
    }
    return render(request, 'transactions.html', context)

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_admin or obj.user == request.user

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        qs = Transaction.objects.select_related("wallet", "user").all()
        if self.request.user.is_admin:
            return qs
        return qs.filter(user=self.request.user)

class WithdrawalViewSet(viewsets.ModelViewSet):
    serializer_class = WithdrawalSerializer
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        qs = Withdrawal.objects.select_related("user").all()
        if self.request.user.is_admin:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Validate amount and balance before creating withdrawal
        amount = serializer.validated_data.get('amount')
        if amount <= 0:
            raise serializers.ValidationError({"amount": "Amount must be positive"})
        
        # Business rule: Minimum withdrawal validation
        if amount < MINIMUM_WITHDRAWAL_AMOUNT:
            raise serializers.ValidationError({
                "amount": "Minimum withdrawal amount is $60"
            })
        
        # Check if user has sufficient balance
        try:
            wallet = self.request.user.wallet
            if wallet.balance < amount:
                raise serializers.ValidationError({"amount": "Insufficient balance."})
        except Wallet.DoesNotExist:
            raise serializers.ValidationError({"amount": "No wallet found"})
        
        # Reserve funds immediately by creating the withdrawal and deducting the amount
        with db_transaction.atomic():
            withdrawal = serializer.save(
                user=self.request.user,
                status=Withdrawal.Status.PENDING,
                reference=f"WDL-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            )
            wallet.subtract_balance(
                amount=amount,
                transaction_type=Transaction.TransactionType.WITHDRAWAL,
                reference=withdrawal.reference
            )
        
        # Send notification (with error handling)
        try:
            Notification.objects.create(
                user=self.request.user,
                title="Withdrawal request submitted",
                message=f"Your withdrawal request of ${amount} has been submitted and is pending approval.",
            )
        except Exception as e:
            # Log error but don't fail the withdrawal creation
            pass

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUserCustom])
    def approve(self, request, pk=None):
        withdrawal = self.get_object()
        if withdrawal.status != Withdrawal.Status.PENDING:
            return Response({"detail": "Transaction already processed."}, status=status.HTTP_400_BAD_REQUEST)
        
        with db_transaction.atomic():
            wallet = withdrawal.user.wallet
            withdrawal.status = Withdrawal.Status.APPROVED
            withdrawal.processed_at = timezone.now()
            withdrawal.save(update_fields=["status", "processed_at"])
            
            # No additional deduction needed if funds were reserved during request creation.
            # For legacy withdrawals without an earlier reserved transaction, deduct now.
            existing_tx = Transaction.objects.filter(
                wallet=wallet,
                reference=withdrawal.reference,
                transaction_type=Transaction.TransactionType.WITHDRAWAL,
            ).exists()
            if not existing_tx:
                if wallet.balance < withdrawal.amount:
                    return Response({"detail": "Insufficient funds."}, status=status.HTTP_400_BAD_REQUEST)
                wallet.subtract_balance(
                    amount=withdrawal.amount,
                    transaction_type=Transaction.TransactionType.WITHDRAWAL,
                    reference=withdrawal.reference
                )
            
            try:
                Notification.objects.create(
                    user=withdrawal.user,
                    title="Withdrawal approved",
                    message=f"Your withdrawal of ${withdrawal.amount} was approved. Your balance has been updated.",
                )
            except Exception as e:
                pass
        
        wallet.refresh_from_db()
        return Response({"status": "approved", "balance": str(wallet.balance)})

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUserCustom])
    def reject(self, request, pk=None):
        withdrawal = self.get_object()
        if withdrawal.status != Withdrawal.Status.PENDING:
            return Response({"detail": "Transaction already processed."}, status=status.HTTP_400_BAD_REQUEST)
        
        with db_transaction.atomic():
            withdrawal.status = Withdrawal.Status.REJECTED
            withdrawal.processed_at = timezone.now()
            withdrawal.save(update_fields=["status", "processed_at"])
            
            # Send notification (with error handling)
            try:
                Notification.objects.create(
                    user=withdrawal.user,
                    title="Withdrawal rejected",
                    message=f"Your withdrawal request of ${withdrawal.amount} was rejected. Please contact support for more information.",
                )
            except Exception as e:
                # Log error but don't fail the rejection
                pass
        
        return Response({"status": "rejected"})

class PaymentMethodViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentMethodSerializer
    authentication_classes = (SessionAuthentication,)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUserCustom()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_admin:
            return PaymentMethod.objects.all().order_by('-created_at')
        return PaymentMethod.objects.filter(is_active=True).order_by('name')

class CryptoDepositViewSet(viewsets.ModelViewSet):
    serializer_class = CryptoDepositSerializer
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if self.request.user.is_admin:
            return CryptoDeposit.objects.all().order_by('-created_at')
        return CryptoDeposit.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        # Validate hash uniqueness
        tx_hash = serializer.validated_data.get('transaction_hash')
        if CryptoDeposit.objects.filter(transaction_hash=tx_hash).exists():
            raise serializers.ValidationError({"transaction_hash": "This transaction hash has already been submitted."})
            
        serializer.save(user=self.request.user, status=CryptoDeposit.Status.PENDING)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUserCustom])
    def approve(self, request, pk=None):
        deposit = self.get_object()
        if deposit.status != CryptoDeposit.Status.PENDING:
            return Response({"detail": "Transaction already processed."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            wallet = deposit.approve()
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"status": "approved", "balance": str(wallet.balance)})

    def _activate_user_plan(self, user, deposit_amount):
        """Activate or update user plan based on deposit amount (Crypto Only Version)"""
        from core.models import Plan, UserPlan
        
        if deposit_amount >= 120: plan_level = 4
        elif deposit_amount >= 80: plan_level = 3
        elif deposit_amount >= 50: plan_level = 2
        elif deposit_amount >= 20: plan_level = 1
        else: return
        
        try:
            plan = Plan.objects.get(plan_level=plan_level, active=True)
            if not UserPlan.objects.filter(user=user, plan=plan).exists():
                UserPlan.objects.create(user=user, plan=plan)
            user.current_plan_level = plan_level
            user.save(update_fields=["current_plan_level"])
        except Plan.DoesNotExist: pass

    @action(detail=True, methods=["post"], permission_classes=[IsAdminUserCustom])
    def reject(self, request, pk=None):
        deposit = self.get_object()
        if deposit.status != CryptoDeposit.Status.PENDING:
            return Response({"detail": "Transaction already processed."}, status=status.HTTP_400_BAD_REQUEST)
            
        deposit.status = CryptoDeposit.Status.REJECTED
        deposit.processed_at = timezone.now()
        deposit.save(update_fields=["status", "processed_at"])
        
        # Notification
        try:
            Notification.objects.create(
                user=deposit.user,
                title="Crypto Deposit Rejected",
                message=f"Your crypto deposit of ${deposit.amount} was rejected.",
            )
        except: pass
            
        return Response({"status": "rejected"})
