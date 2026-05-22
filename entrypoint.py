#!/usr/bin/env python
"""
Render entrypoint script for Nova Profit
- Handles migrations gracefully
- Starts the Daphne ASGI server
"""

import os
import sys
import subprocess

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "novaprofit.settings")

# Attempt migrations (fail gracefully)
print("Attempting to run migrations...")
try:
    import django
    django.setup()
    from django.core.management import call_command
    call_command("migrate", verbosity=0, interactive=False)
    print("✓ Migrations completed")
except Exception as e:
    print(f"⚠ Migrations skipped: {str(e)[:100]}")

# Attempt static files collection
print("Collecting static files...")
try:
    from django.core.management import call_command
    call_command("collectstatic", verbosity=0, interactive=False)
    print("✓ Static files collected")
except Exception as e:
    print(f"⚠ Static files skipped: {str(e)[:100]}")

# Start Daphne server
port = os.environ.get("PORT", "8000")
print(f"Starting Daphne server on port {port}...")

cmd = [
    "daphne",
    "-b", "0.0.0.0",
    "-p", port,
    "novaprofit.asgi:application"
]

os.execvp("daphne", cmd)
