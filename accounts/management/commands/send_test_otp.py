from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from accounts.otp_utils import create_and_send_otp

User = get_user_model()


class Command(BaseCommand):
    help = (
        'Send a test OTP email to an existing user or send a raw email test to any address. '
        'Use this to verify the email backend and OTP delivery path.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            nargs='?', 
            help='Email address to send the OTP or raw test message to.',
        )
        parser.add_argument(
            '--raw',
            action='store_true',
            help='Send a raw test email without creating an OTP record.',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        raw = options.get('raw')

        self.stdout.write('EMAIL BACKEND: %s' % settings.EMAIL_BACKEND)
        self.stdout.write('EMAIL HOST: %s' % getattr(settings, 'EMAIL_HOST', ''))
        self.stdout.write('EMAIL PORT: %s' % getattr(settings, 'EMAIL_PORT', ''))
        self.stdout.write('EMAIL HOST USER: %s' % getattr(settings, 'EMAIL_HOST_USER', ''))
        self.stdout.write('DEFAULT FROM EMAIL: %s' % settings.DEFAULT_FROM_EMAIL)

        if not email:
            self.stderr.write(self.style.ERROR('Please provide an email address.'))
            self.stderr.write('Usage: python manage.py send_test_otp user@example.com')
            self.stderr.write('Or: python manage.py send_test_otp user@example.com --raw')
            return 1

        if raw:
            subject = 'Test Email Delivery'
            message = (
                'This is a raw delivery test from the Django OTP email backend. '
                'If you receive this message, the configured email backend is working.'
            )
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
                self.stdout.write(self.style.SUCCESS('Raw test email sent successfully to %s' % email))
                return 0
            except Exception as exc:
                self.stderr.write(self.style.ERROR('Raw email send failed: %s' % exc))
                return 1

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            self.stderr.write(self.style.ERROR(
                'No user found with email %s. Use --raw to test the backend for an arbitrary address.' % email
            ))
            return 1

        self.stdout.write('Found user %s. Creating OTP and sending email...' % user.email)
        otp, sent = create_and_send_otp(user)
        if sent:
            self.stdout.write(self.style.SUCCESS('OTP email sent successfully.'))
            self.stdout.write('The OTP was generated and emailed to %s.' % user.email)
            return 0
        self.stderr.write(self.style.ERROR('Failed to send OTP email. Check the console for detailed error output.'))
        return 1
