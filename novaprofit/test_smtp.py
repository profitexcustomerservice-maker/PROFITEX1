#!/usr/bin/env python
"""
Direct SMTP Test - Test email sending with actual error output
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novaprofit.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("\n" + "="*60)
print("SMTP EMAIL TEST")
print("="*60 + "\n")

print("Current Email Configuration:")
print(f"  Email Backend: {settings.EMAIL_BACKEND}")
print(f"  Email Host: {settings.EMAIL_HOST}")
print(f"  Email Port: {settings.EMAIL_PORT}")
print(f"  Email Use TLS: {settings.EMAIL_USE_TLS}")
print(f"  Email Host User: {settings.EMAIL_HOST_USER}")
print(f"  Email Password Set: {bool(settings.EMAIL_HOST_PASSWORD)}")
print(f"  Default From Email: {settings.DEFAULT_FROM_EMAIL}")
print()

if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
    print("❌ ERROR: Email credentials are not configured!")
    exit(1)

print("Attempting to send test email...")
print("-" * 60)

try:
    result = send_mail(
        "NovaProfit SMTP Test",
        "This is a test email from NovaProfit.\n\nIf you received this, SMTP is working correctly!",
        settings.DEFAULT_FROM_EMAIL,
        [settings.EMAIL_HOST_USER],  # Send to self
        fail_silently=False,
    )

    print(f"\n✅ SUCCESS: Test email sent successfully")
    print(f"   Return value: {result}")
    print("✅ Please check your inbox (and spam folder) for the test email.")

except Exception as e:
    print(f"\n❌ ERROR: Failed to send email")
    print(f"   Error Type: {type(e).__name__}")
    print(f"   Error Message: {str(e)}")
    print("\nCommon fixes:")
    print("  1. For Gmail: Use an App Password (not your regular password)")
    print("     Generate at: https://myaccount.google.com/apppasswords")
    print("  2. Enable 2FA on your Google Account (required for App Passwords)")
    print("  3. Check that EMAIL_HOST and EMAIL_PORT are correct")
    print("  4. Ensure your firewall is not blocking SMTP port 587")
    print("  5. For production, use a dedicated email service (SendGrid, Mailgun)")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
