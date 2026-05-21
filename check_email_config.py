#!/usr/bin/env python
"""
Check if email configuration is loaded correctly in Django
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novaprofit.settings')
django.setup()

from django.conf import settings

print("\n" + "="*60)
print("EMAIL CONFIGURATION CHECK")
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
    print("\nTo fix this, ensure the .env file has:")
    print("  EMAIL_HOST_USER=your_email@gmail.com")
    print("  EMAIL_HOST_PASSWORD=your_app_password")
else:
    print("✅ Email credentials appear to be configured")
    print("\nNote: If you recently updated .env, you may need to restart the Django server")
