from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .models import Task, UserTaskSubmission
from .serializers import TaskSerializer, UserTaskSubmissionSerializer
from django.shortcuts import get_object_or_404
from wallet.models import Wallet, Transaction, CryptoDeposit
from .services import credit_submission_reward
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from wallet.models import Transaction
from decimal import Decimal
from core.plan_utils import user_has_active_plan


def user_has_deposit(user):
    """Check if user has made at least one approved deposit"""
    return CryptoDeposit.objects.filter(
        user=user,
        status=CryptoDeposit.Status.APPROVED
    ).exists()


class PublicTaskViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Task.objects.filter(is_active=True)
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = UserTaskSubmission.objects.all()
    serializer_class = UserTaskSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # users see their submissions; admins see all
        user = self.request.user
        if user.is_staff or getattr(user, 'is_admin', False):
            return super().get_queryset()
        return super().get_queryset().filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        
        # Check if user has made a deposit first
        if not user_has_deposit(user):
            raise PermissionDenied(
                detail="Please make a deposit first to work on tasks."
            )
        
        # Check if user has an active plan
        if not user_has_active_plan(user):
            raise PermissionDenied(
                detail="You must purchase a plan to access tasks. Please buy a plan to continue working on tasks."
            )
        
        submission = serializer.save(user=user)
        # Optionally notify admins (simplified)
        # TODO: hook into notification system

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        submission = get_object_or_404(UserTaskSubmission, pk=pk)
        if submission.status == submission.Status.APPROVED:
            return Response({'detail': 'Already approved.'}, status=status.HTTP_200_OK)

        tx = credit_submission_reward(submission, reviewer=request.user)
        # send email
        if tx and settings.EMAIL_HOST:
            try:
                send_mail(
                    subject='Submission approved',
                    message=f'Your submission for {submission.task.title} was approved and ${submission.task.reward_amount} credited.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[submission.user.email],
                )
            except Exception:
                pass

        return Response({'detail': 'Approved and credited' if tx else 'Already credited'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        submission = get_object_or_404(UserTaskSubmission, pk=pk)
        if submission.status == submission.Status.REJECTED:
            return Response({'detail': 'Already rejected.'}, status=status.HTTP_200_OK)
        submission.status = submission.Status.REJECTED
        submission.reviewed_at = timezone.now()
        submission.reviewed_by = request.user
        submission.save(update_fields=['status', 'reviewed_at', 'reviewed_by'])

        # notify user
        if settings.EMAIL_HOST:
            try:
                send_mail(
                    subject='Submission rejected',
                    message=f'Your submission for {submission.task.title} was rejected. Comment: {submission.admin_comment}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[submission.user.email],
                )
            except Exception:
                pass

        return Response({'detail': 'Rejected'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def check_eligibility(self, request):
        """Check if user is eligible to submit tasks"""
        from core.plan_utils import get_plan_info
        
        user = request.user
        has_deposit = user_has_deposit(user)
        has_plan = user_has_active_plan(user)
        plan_info = get_plan_info(user)
        
        return Response({
            'eligible': has_deposit and has_plan,
            'has_deposit': has_deposit,
            'has_plan': has_plan,
            'plan_info': plan_info,
            'messages': {
                'deposit': 'Approved' if has_deposit else 'No approved deposit found. Please make a deposit to access tasks.',
                'plan': 'Active' if has_plan else 'No active plan. Please purchase a plan to access tasks.',
            }
        })
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def track_link_open(self, request, pk=None):
        """Track when a user opens an external link for a task"""
        submission = self.get_object()
        
        # Verify user owns this submission
        if submission.user != request.user:
            return Response(
                {'detail': 'You cannot track links for submissions you do not own.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Record link open time
        submission.link_opened_at = timezone.now()
        submission.save(update_fields=['link_opened_at'])
        
        return Response({
            'success': True,
            'message': 'Link opening tracked',
            'link_opened_at': submission.link_opened_at.isoformat(),
            'required_duration': submission.task.required_duration,
        })
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def track_timer(self, request, pk=None):
        """Track timer data when user completes a task"""
        submission = self.get_object()
        
        # Verify user owns this submission
        if submission.user != request.user:
            return Response(
                {'detail': 'You cannot update submissions you do not own.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get time spent from request
        time_spent = request.data.get('time_spent', 0)
        
        try:
            time_spent = int(time_spent)
        except (ValueError, TypeError):
            return Response(
                {'detail': 'time_spent must be an integer (seconds)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate minimum duration
        if submission.task.required_duration and time_spent < submission.task.required_duration:
            return Response({
                'success': False,
                'detail': f'Minimum {submission.task.required_duration}s required. You spent {time_spent}s.',
                'required_duration': submission.task.required_duration,
                'time_spent': time_spent,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update submission with timer data
        submission.time_spent = time_spent
        submission.timer_completed_at = timezone.now()
        
        # Set timer started if not already set
        if not submission.timer_started_at:
            submission.timer_started_at = submission.timer_completed_at
        
        submission.save(update_fields=['time_spent', 'timer_completed_at', 'timer_started_at'])
        
        return Response({
            'success': True,
            'message': 'Timer recorded successfully',
            'time_spent': submission.time_spent,
            'timer_completed_at': submission.timer_completed_at.isoformat(),
            'minimum_duration_met': submission.is_minimum_duration_met(),
        })


class WalletView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        txs = Transaction.objects.filter(user=request.user).order_by('-created_at')[:10]
        return Response({
            'balance': str(wallet.balance),
            'recent_transactions': [
                {
                    'id': t.id,
                    'amount': str(t.amount),
                    'type': t.transaction_type,
                    'reference': t.reference,
                    'created_at': t.created_at,
                }
                for t in txs
            ]
        })
