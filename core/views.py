from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import connections, transaction, IntegrityError
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from rest_framework import mixins, permissions, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.db.models import Sum
from decimal import Decimal
from .models import Plan, Task, UserPlan, UserTask, SystemSettings
from .serializers import PlanSerializer, TaskSerializer, UserPlanSerializer, UserTaskSerializer
from wallet.models import CryptoDeposit, Transaction as WalletTransaction, Wallet
from notifications.models import Notification
import logging

logger = logging.getLogger(__name__)


def user_can_do_tasks(user):
    if not user or not user.is_authenticated:
        return False

    # Admins and superusers can still manage tasks
    if getattr(user, 'is_admin', False) or getattr(user, 'is_superuser', False):
        return True

    minimum_deposit = Decimal('60.00')

    approved_crypto_total = CryptoDeposit.objects.filter(
        user=user,
        status=CryptoDeposit.Status.APPROVED
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    deposit_tx_total = WalletTransaction.objects.filter(
        user=user,
        transaction_type=WalletTransaction.TransactionType.DEPOSIT
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    has_joined_plan = UserPlan.objects.filter(user=user).exists()

    if has_joined_plan:
        return True

    return (approved_crypto_total + deposit_tx_total) > minimum_deposit

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.is_admin

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAdminOrReadOnly,)

    def get_queryset(self):
        qs = Task.objects.select_related().all().order_by("-created_at")
        if self.request.user.is_authenticated and self.request.user.is_admin:
            return qs
        # Show active tasks to all authenticated users
        # Non-invested users can see tasks but cannot perform them (checked in UserTaskViewSet)
        if self.request.user.is_authenticated:
            return qs.filter(active=True)
        return Task.objects.none()

class PlanViewSet(viewsets.ModelViewSet):
    serializer_class = PlanSerializer
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAdminOrReadOnly,)

    def get_queryset(self):
        qs = Plan.objects.all().order_by("-created_at")
        if not self.request.user.is_authenticated or not self.request.user.is_admin:
            return qs.filter(active=True)
        return qs
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to provide clearer errors and prevent deleting plans
        that have active user subscriptions.
        """
        try:
            instance = self.get_object()

            # Prevent deletion when there are existing subscriptions to avoid
            # accidental cascade deletes and unclear errors on the client.
            if hasattr(instance, 'subscriptions') and instance.subscriptions.exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot delete plan with active subscriptions. Remove subscriptions first.'
                }, status=400)

            self.perform_destroy(instance)
            return JsonResponse({'success': True, 'message': 'Plan deleted successfully.'})
        except Exception as e:
            logger.exception(f"Error deleting plan: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

class UserTaskViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = UserTaskSerializer
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return UserTask.objects.filter(user=self.request.user).select_related("task").order_by("-completed_at")

    def perform_create(self, serializer):
        if not user_can_do_tasks(self.request.user):
            raise PermissionDenied("Tasks are available only after you deposit more than $60 and join a plan.")

        task = serializer.validated_data["task"]
        duration_spent = serializer.validated_data.get("duration_spent", 0)

        if task.active is False:
            raise PermissionDenied("Task is not active")

        today = timezone.localdate()
        if UserTask.objects.filter(user=self.request.user, task=task, completed_date=today).exists():
            raise PermissionDenied("You can only complete this task once per day.")

        required_seconds = int(task.duration or 0) * 60
        if required_seconds > 0 and duration_spent < required_seconds:
            raise PermissionDenied(f"You must spend at least {required_seconds} seconds on this task before completing it.")

        with transaction.atomic():
            # Save user task completion
            user_task = serializer.save(user=self.request.user)
            
            # Add task reward to user wallet
            wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
            
            # Apply plan multiplier if user has an active plan
            reward_amount = task.reward
            try:
                active_user_plan = UserPlan.objects.filter(user=self.request.user).select_related('plan').first()
                if active_user_plan and active_user_plan.plan.reward_multiplier:
                    reward_amount = task.reward * active_user_plan.plan.reward_multiplier
            except Exception:
                pass

            wallet.add_balance(
                amount=reward_amount,
                transaction_type=WalletTransaction.TransactionType.TASK_REWARD,
                reference=f"task-{task.id}-{user_task.id}"
            )

            # Update user's last rewarded timestamp
            self.request.user.last_rewarded_at = timezone.now()
            self.request.user.save(update_fields=["last_rewarded_at"])
            
            # Create notification
            try:
                Notification.objects.create(
                    user=self.request.user,
                    title="Task completed",
                    message=f"You completed '{task.title}' and earned ${reward_amount:.2f}!",
                )
            except Exception as e:
                logger.warning(f"Notification error for task {task.id}: {e}")

class UserPlanViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = UserPlanSerializer
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return UserPlan.objects.filter(user=self.request.user).select_related("plan").order_by("-joined_at")

    def perform_create(self, serializer):
        plan = serializer.validated_data["plan"]
        if plan.active is False:
            raise PermissionDenied("Plan is not active")

        if UserPlan.objects.filter(user=self.request.user).exists():
            raise PermissionDenied("You have already joined a plan.")

        with transaction.atomic():
            wallet, _ = Wallet.objects.get_or_create(user=self.request.user)
            if wallet.balance < plan.amount:
                raise PermissionDenied("Insufficient balance to join plan")

            # Use safe subtract method first, then save the subscription.
            wallet.subtract_balance(
                amount=plan.amount,
                transaction_type=WalletTransaction.TransactionType.ADJUSTMENT,
                reference=f"plan-{plan.id}-reserve",
            )

            try:
                subscription = serializer.save(user=self.request.user)
            except IntegrityError:
                raise PermissionDenied("You have already joined a plan or this plan already exists for you.")

            # Update user plan level
            self.request.user.current_plan_level = plan.plan_level or 0
            self.request.user.save(update_fields=["current_plan_level"])

            try:
                Notification.objects.create(
                    user=self.request.user,
                    title="Plan joined",
                    message=f"You joined the '{plan.title}' plan and ${plan.amount} was deducted.",
                )
            except Exception as e:
                logger.warning(f"Notification error for plan {plan.id}: {e}")

@login_required
def tasks_page(request):
    return render(request, "tasks.html", {
        "task_access_allowed": user_can_do_tasks(request.user),
    })

@login_required
def plans_page(request):
    return render(request, "plans.html")

@cache_page(60 * 5)
def system_settings_api(request):
    """API endpoint to fetch system-wide settings"""
    try:
        from accounts.models import SocialLink
        settings = SystemSettings.get_settings()
        social_links = [
            {"name": link.name, "url": link.url, "icon": link.icon}
            for link in SocialLink.objects.filter(is_active=True).order_by('order', 'name')
        ]
        return JsonResponse({
            "success": True,
            "telegram_link": settings.telegram_link,
            "whatsapp_link": settings.whatsapp_link,
            "support_phone": settings.support_phone,
            "support_email": settings.support_email,
            "facebook_link": settings.facebook_link,
            "instagram_link": settings.instagram_link,
            "social_links": social_links,
            "announcement_banner": settings.announcement_banner,
            "updated_at": settings.updated_at.isoformat() if settings.updated_at else None
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def health_check(request):
    """Lightweight health endpoint for app monitoring."""
    status_code = 200
    response = {
        "status": "ok",
        "database": "ok",
        "cache": "ok",
    }

    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:
        response["database"] = "error"
        response["database_error"] = str(exc)
        status_code = 500

    try:
        cache.set("health_check_ping", "pong", timeout=5)
        if cache.get("health_check_ping") != "pong":
            raise RuntimeError("Cache ping returned unexpected value")
    except Exception as exc:
        response["cache"] = "error"
        response["cache_error"] = str(exc)
        status_code = 500

    return JsonResponse(response, status=status_code)
