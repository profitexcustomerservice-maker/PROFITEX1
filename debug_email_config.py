#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novaprofit.settings')
django.setup()

from django.conf import settings

print("="*70)
print("EMAIL CONFIGURATION DEBUG")
print("="*70)
print(f"DEBUG mode: {settings.DEBUG}")
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"EMAIL_HOST_PASSWORD set: {bool(settings.EMAIL_HOST_PASSWORD)}")
print(f"EMAIL_HOST_PASSWORD value: {repr(settings.EMAIL_HOST_PASSWORD)}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print()
print("Environment variables:")
print(f"  EMAIL_HOST_PASSWORD env: {os.getenv('EMAIL_HOST_PASSWORD', 'NOT_SET')}")
print(f"  EMAIL_FORCE_CONSOLE env: {os.getenv('EMAIL_FORCE_CONSOLE', 'NOT_SET')}")
print()

# Check if console backend
if 'console' in settings.EMAIL_BACKEND:
    print("✓ USING CONSOLE EMAIL BACKEND - OTP will be printed to logs")
else:
    print("✗ USING SMTP EMAIL BACKEND - Will attempt to send via SMTP")
    print("  WARNING: This will timeout on Render due to network isolation")
