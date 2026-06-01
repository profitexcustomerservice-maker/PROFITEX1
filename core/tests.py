from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Plan, UserPlan
from core.views import user_can_do_tasks, user_has_deposited
from wallet.models import Wallet, Transaction

User = get_user_model()


class PlanAndTaskAccessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@example.com', password='secret1234')
        self.plan = Plan.objects.create(plan_level=1, title='Plan 1', amount=100, active=True)
        self.wallet, _ = Wallet.objects.get_or_create(user=self.user, defaults={'balance': 100})
        if self.wallet.balance != 100:
            self.wallet.balance = 100
            self.wallet.save()

    def test_user_without_deposit_or_plan_cannot_do_tasks(self):
        self.assertFalse(user_can_do_tasks(self.user))

    def test_user_with_deposit_can_do_tasks(self):
        Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            amount=100,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            reference='DEPOSIT-TASK-TEST'
        )
        self.assertTrue(user_has_deposited(self.user))
        self.assertTrue(user_can_do_tasks(self.user))

    def test_user_with_plan_can_do_tasks(self):
        UserPlan.objects.create(user=self.user, plan=self.plan)
        self.assertTrue(user_can_do_tasks(self.user))

    def test_user_without_deposit_cannot_buy_plan_even_with_balance(self):
        # Wallet balance may exist, but without a deposit record the user cannot join a plan.
        self.assertFalse(user_has_deposited(self.user))

        self.client.force_login(self.user)
        response = self.client.post('/api/user-plans/', {'plan_id': self.plan.id})
        self.assertEqual(response.status_code, 403)
        self.assertIn('You must deposit funds before buying a plan', response.content.decode())

    def test_user_with_deposit_can_buy_plan(self):
        Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            amount=100,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            reference='DEPOSIT-TEST'
        )
        self.assertTrue(user_has_deposited(self.user))

        self.client.force_login(self.user)
        response = self.client.post('/api/user-plans/', {'plan_id': self.plan.id})
        self.assertIn(response.status_code, (200, 201))
        self.assertTrue(UserPlan.objects.filter(user=self.user, plan=self.plan).exists())
