from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Task, UserTaskSubmission
from .serializers import TaskSerializer, UserTaskSubmissionSerializer
from django.shortcuts import get_object_or_404
from wallet.models import Wallet, Transaction
from .services import credit_submission_reward
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from wallet.models import Transaction
from decimal import Decimal


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
        submission = serializer.save(user=self.request.user)
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
