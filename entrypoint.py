#!/usr/bin/env python
"""
Render entrypoint script for Nova Profit
- Handles migrations gracefully
- Starts the Daphne ASGI server
"""

import os
import sys
import subprocess
import time

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "novaprofit.settings")

print("=" * 60)
print("Nova Profit Startup")
print("=" * 60)

# Check environment variables
print("\nChecking environment...")
db_url = os.environ.get("DATABASE_URL", "")
if db_url:
    # Mask the password for security
    masked = db_url.split("@")[0] + "@..." if "@" in db_url else "***"
    print(f"✓ DATABASE_URL found: {masked}")
else:
    print("⚠ DATABASE_URL not set (will attempt to use default)")

secret_key = os.environ.get("DJANGO_SECRET_KEY", "")
if secret_key:
    print(f"✓ DJANGO_SECRET_KEY found: {secret_key[:10]}...")
else:
    print("⚠ WARNING: DJANGO_SECRET_KEY not set!")

# Attempt migrations (fail gracefully)
print("\nAttempting to run migrations...")
try:
    import django
    django.setup()
    from django.core.management import call_command
    call_command("migrate", verbosity=0, interactive=False)
    print("✓ Migrations completed successfully")
except Exception as e:
    error_msg = str(e)[:150]
    print(f"⚠ Migrations warning: {error_msg}")
    print("  (App will continue without migrations - you can run them manually later)")

# Attempt static files collection
print("\nCollecting static files...")
try:
    from django.core.management import call_command
    call_command("collectstatic", verbosity=0, interactive=False)
    print("✓ Static files collected successfully")
except Exception as e:
    error_msg = str(e)[:150]
    print(f"⚠ Static files warning: {error_msg}")
    print("  (Continuing without static files - WhiteNoise will handle this)")

# Start Daphne server
port = os.environ.get("PORT", "10000")
print(f"\n" + "=" * 60)
print(f"Starting Daphne ASGI server on 0.0.0.0:{port}")
print("=" * 60 + "\n")

# Use subprocess.run instead of execvp for better compatibility
try:
    import daphne.cli
    from daphne.cli import CommandLineInterface
    
    # Use daphne command via subprocess
    cmd = [
        sys.executable, "-m", "daphne",
        "-b", "0.0.0.0",
        "-p", port,
        "novaprofit.asgi:application"
    ]
    
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
    
except Exception as e:
    print(f"Error starting Daphne: {e}")
    print("\nTrying alternative startup method...")
    
    # Fallback: try direct command
    try:
        subprocess.run(
            ["daphne", "-b", "0.0.0.0", "-p", port, "novaprofit.asgi:application"],
            check=True
        )
    except Exception as e2:
        print(f"Failed to start server: {e2}")
        sys.exit(1)
