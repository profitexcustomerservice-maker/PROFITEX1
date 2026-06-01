from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from django.conf import settings

from accounts.models import OTP
from accounts.models import User
from accounts.models import Referral
from wallet.models import Wallet, Transaction, CryptoDeposit, PaymentMethod


@override_settings(
    ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1'],
    SECURE_SSL_REDIRECT=False,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class PasswordResetOtpFlowTests(TestCase):
    def test_forgot_password_page_shows_send_code_form(self):
        response = self.client.get(reverse('forgot_password'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reset your password with a verification code')
        self.assertContains(response, 'Send Code')

    def test_forgot_password_post_sends_code_and_redirects(self):
        user = User.objects.create_user(email='person@example.com', password='Secret1234')

        response = self.client.post(
            reverse('forgot_password'),
            {'email': user.email},
        )

        self.assertRedirects(response, reverse('reset_password'))
        self.assertEqual(OTP.objects.count(), 1)

    def test_reset_password_page_renders_otp_form(self):
        response = self.client.get(reverse('reset_password'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter Verification Code')
        self.assertContains(response, 'New Password')

    def test_reset_resend_route_redirects_to_forgot_password_when_no_session(self):
        response = self.client.get(reverse('reset_password_resend'))

        self.assertRedirects(response, reverse('forgot_password'))

    def test_legacy_otp_routes_redirect_to_login(self):
        verify_response = self.client.get(reverse('otp_verify'))
        resend_response = self.client.get(reverse('otp_resend'))

        self.assertRedirects(verify_response, reverse('login_page'))
        self.assertRedirects(resend_response, reverse('login_page'))

    def test_login_redirects_directly_to_dashboard(self):
        user = User.objects.create_user(email='login@example.com', password='Secret1234')

        response = self.client.post(
            reverse('login_page'),
            {'email': user.email, 'password': 'Secret1234'},
        )

        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(OTP.objects.count(), 0)
        self.assertEqual(self.client.session.get('_auth_user_id'), str(user.id))


class ReferralRewardTests(TestCase):
    def setUp(self):
        self.referrer = User.objects.create_user(email='referrer@example.com', password='Secret1234')
        self.referred = User.objects.create_user(email='referred@example.com', password='Secret1234')
        self.referred.referred_by = self.referrer
        self.referred.save(update_fields=['referred_by'])
        Referral.objects.create(referrer=self.referrer, referred_user=self.referred)

        self.payment_method = PaymentMethod.objects.create(
            name='USDT',
            network='TRC20',
            wallet_address='test-address',
            is_active=True,
        )

    def test_referrer_gets_reward_on_first_crypto_deposit_approval(self):
        deposit = CryptoDeposit.objects.create(
            user=self.referred,
            payment_method=self.payment_method,
            amount=10,
            transaction_hash='hash1',
            status=CryptoDeposit.Status.PENDING,
        )

        wallet = Wallet.objects.get(user=self.referrer)
        self.assertEqual(wallet.balance, 0)

        deposit.approve()

        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, settings.REFERRAL_REWARD_AMOUNT)

        transaction = Transaction.objects.filter(
            user=self.referrer,
            transaction_type=Transaction.TransactionType.REFERRAL_REWARD,
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(float(transaction.amount), settings.REFERRAL_REWARD_AMOUNT)

        referral = Referral.objects.get(referrer=self.referrer, referred_user=self.referred)
        self.assertEqual(float(referral.reward_amount), settings.REFERRAL_REWARD_AMOUNT)
        self.assertFalse(referral.is_active)
