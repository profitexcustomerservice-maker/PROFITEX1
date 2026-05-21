from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Plan, UserPlan
from wallet.models import CryptoDeposit, PaymentMethod, Wallet


class CryptoDepositApprovalTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email="user@example.com", password="password123")
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="adminpassword",
            is_admin=True,
            is_staff=True,
            is_superuser=False,
        )
        self.payment_method = PaymentMethod.objects.create(
            name="BTC",
            network="TRC20",
            wallet_address="fake-wallet-address",
        )
        self.plan4 = Plan.objects.create(plan_level=4, title="Plan 4", active=True)

    def test_crypto_deposit_approve_credits_wallet_and_activates_plan(self):
        deposit = CryptoDeposit.objects.create(
            user=self.user,
            payment_method=self.payment_method,
            amount=150,
            transaction_hash="TESTHASH1234567890",
            status=CryptoDeposit.Status.PENDING,
        )

        wallet = deposit.approve()
        self.user.refresh_from_db()
        wallet.refresh_from_db()

        self.assertEqual(wallet.balance, 150)
        self.assertEqual(self.user.current_plan_level, 4)
        self.assertTrue(UserPlan.objects.filter(user=self.user, plan=self.plan4).exists())
        self.assertEqual(deposit.status, CryptoDeposit.Status.APPROVED)

    def test_admin_api_can_approve_crypto_deposit(self):
        deposit = CryptoDeposit.objects.create(
            user=self.user,
            payment_method=self.payment_method,
            amount=120,
            transaction_hash="APIHASH1234567890",
            status=CryptoDeposit.Status.PENDING,
        )

        self.client.login(email="admin@example.com", password="adminpassword")
        url = reverse("api_crypto_deposit_approve", args=[deposit.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("status"), "approved")
        self.assertEqual(data.get("balance"), "120.00")

        deposit.refresh_from_db()
        self.assertEqual(deposit.status, CryptoDeposit.Status.APPROVED)
        self.assertEqual(Wallet.objects.get(user=self.user).balance, 120)

    def test_approval_returns_error_for_processed_deposit(self):
        deposit = CryptoDeposit.objects.create(
            user=self.user,
            payment_method=self.payment_method,
            amount=100,
            transaction_hash="ALREADY1234567890",
            status=CryptoDeposit.Status.APPROVED,
        )

        self.client.login(email="admin@example.com", password="adminpassword")
        url = reverse("api_crypto_deposit_approve", args=[deposit.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get("error"), "Deposit already processed")
