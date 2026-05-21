from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import OTP
from accounts.models import User


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

    def test_login_requires_otp_before_access(self):
        user = User.objects.create_user(email='login@example.com', password='Secret1234')

        response = self.client.post(
            reverse('login_page'),
            {'email': user.email, 'password': 'Secret1234'},
        )

        self.assertRedirects(response, reverse('otp_verify'))
        self.assertEqual(OTP.objects.count(), 1)
        self.assertIsNone(self.client.session.get('_auth_user_id'))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_otp_is_sent_to_user_email(self):
        user = User.objects.create_user(email='alice@example.com', password='Secret1234')

        response = self.client.post(
            reverse('login_page'),
            {'email': user.email, 'password': 'Secret1234'},
        )

        self.assertRedirects(response, reverse('otp_verify'))
        self.assertEqual(OTP.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [user.email])
