#!/usr/bin/env python
"""
Email delivery test script.

Run this script to confirm whether OTP emails will be printed locally or sent
to a real inbox.
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "novaprofit.settings")
django.setup()

from django.conf import settings
from django.core.mail import send_mail


def is_real_delivery_configured():
    return settings.EMAIL_BACKEND != "django.core.mail.backends.console.EmailBackend"


def print_configuration():
    print("\n" + "=" * 60)
    print("EMAIL DELIVERY TEST")
    print("=" * 60 + "\n")
    print("CURRENT EMAIL CONFIGURATION:")
    print(f"  Debug: {settings.DEBUG}")
    print(f"  Email Backend: {settings.EMAIL_BACKEND}")
    print(f"  Email Host: {settings.EMAIL_HOST}")
    print(f"  Email Port: {settings.EMAIL_PORT}")
    print(f"  Email Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"  Email Host User: {settings.EMAIL_HOST_USER}")
    print(f"  Email Password Set: {bool(settings.EMAIL_HOST_PASSWORD)}")
    print(f"  Default From Email: {settings.DEFAULT_FROM_EMAIL}")
    print()


def print_next_steps():
    print("REAL EMAIL DELIVERY IS NOT CONFIGURED YET.")
    print()
    print("To deliver OTP emails to a real inbox, add one of these to .env:")
    print("  Gmail SMTP:")
    print("    EMAIL_HOST=smtp.gmail.com")
    print("    EMAIL_PORT=587")
    print("    EMAIL_HOST_USER=your_email@gmail.com")
    print("    EMAIL_HOST_PASSWORD=your_gmail_app_password")
    print("    DEFAULT_FROM_EMAIL=your_email@gmail.com")
    print()
    print("  SendGrid:")
    print("    SENDGRID_API_KEY=your_real_sendgrid_api_key")
    print("    SENDGRID_FROM_EMAIL=noreply@yourdomain.com")
    print()
    print("Until then, OTP emails will be printed in the Django runserver terminal.")


def send_test_email():
    test_email = input(
        "Enter email address to send test to (or press Enter to use DEFAULT_FROM_EMAIL): "
    ).strip()
    if not test_email:
        test_email = settings.DEFAULT_FROM_EMAIL

    print(f"\nAttempting to send test email to: {test_email}")
    print("-" * 60)

    result = send_mail(
        "NovaProfit Email Test",
        (
            "This is a test email from NovaProfit.\n\n"
            "If you received this, email sending is working correctly."
        ),
        settings.DEFAULT_FROM_EMAIL,
        [test_email],
        fail_silently=False,
    )

    print(f"\nSUCCESS: Test email sent successfully to {test_email}")
    print(f"Return value: {result}")
    if is_real_delivery_configured():
        print("Check the recipient inbox and spam folder.")
    else:
        print("Because console backend is active, the email content was printed here.")


def main():
    print_configuration()

    if not is_real_delivery_configured():
        print_next_steps()
        return

    try:
        send_test_email()
    except Exception as exc:
        print("\nERROR: Failed to send email")
        print(f"Error Type: {type(exc).__name__}")
        print(f"Error Message: {exc}")
        print()
        print("Common fixes:")
        print("  1. Gmail: use an App Password, not your normal password")
        print("  2. SendGrid: verify the sender email/domain")
        print("  3. Double-check the key/password in .env")
        print("  4. Check whether your firewall blocks SMTP traffic")


if __name__ == "__main__":
    main()
