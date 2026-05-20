from django.db import transaction
from django.utils import timezone
from wallet.models import Wallet, Transaction


def credit_submission_reward(submission, reviewer=None):
    """
    Credit the user's wallet for an approved submission.
    Idempotent: checks for existing transaction with reference "task_submission:{id}".
    Returns: Transaction instance or None if already processed.
    """
    reference = f"task_submission:{submission.id}"

    # Idempotency: ensure we don't credit twice
    if Transaction.objects.filter(reference=reference, transaction_type=Transaction.TransactionType.TASK_REWARD).exists():
        return None

    with transaction.atomic():
        # ensure wallet exists
        wallet, _ = Wallet.objects.get_or_create(user=submission.user)
        amount = submission.task.reward_amount

        # add balance using wallet helper
        wallet.add_balance(amount=amount, transaction_type=Transaction.TransactionType.TASK_REWARD, reference=reference)

        # mark reviewed fields if not already
        submission.status = submission.Status.APPROVED
        submission.reviewed_at = timezone.now()
        if reviewer:
            submission.reviewed_by = reviewer
        submission.save(update_fields=['status', 'reviewed_at', 'reviewed_by'])

        # return the created transaction
        tx = Transaction.objects.filter(reference=reference).first()
        return tx
