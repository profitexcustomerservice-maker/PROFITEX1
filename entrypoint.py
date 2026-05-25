#!/usr/bin/env python
"""
Render entrypoint script for Nova Profit
- Handles migrations gracefully
- Starts the Daphne ASGI server
"""

import os
import sys
import subprocess
import traceback

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "novaprofit.settings")

print("=" * 60)
print("Nova Profit Startup")
print("=" * 60)

# Check environment variables
print("\nChecking environment...")
db_url = os.environ.get("DATABASE_URL", "")
if db_url:
    masked = db_url.split("@")[0] + "@..." if "@" in db_url else "***"
    print(f"✓ DATABASE_URL found: {masked}")
else:
    print("⚠ DATABASE_URL not set (will use default SQLite)")

secret_key = os.environ.get("DJANGO_SECRET_KEY", "")
if secret_key:
    print(f"✓ DJANGO_SECRET_KEY found: {secret_key[:10]}...")
else:
    print("⚠ WARNING: DJANGO_SECRET_KEY not set!")

# Attempt Django setup
print("\nInitializing Django...")
try:
    import django
    django.setup()
    print("✓ Django initialized successfully")
except Exception as e:
    print(f"⚠ Django initialization warning: {e}")
    traceback.print_exc()

# Attempt migrations (fail gracefully)
print("\nAttempting to run migrations...")
try:
    from django.core.management import call_command
    call_command("migrate", verbosity=2, interactive=False)
    print("✓ Migrations completed successfully")
except SystemExit:
    # Django management commands exit, catch and continue
    print("✓ Migrations completed")
except Exception as e:
    error_msg = str(e)
    print(f"⚠ Migration warning: {error_msg}")
    print("  (App will continue without migrations - you can run them manually later)")
    traceback.print_exc()

# Attempt static files collection
print("\nCollecting static files...")
try:
    from django.core.management import call_command
    call_command("collectstatic", verbosity=0, interactive=False)
    print("✓ Static files collected successfully")
except SystemExit:
    print("✓ Static files handled")
except Exception as e:
    error_msg = str(e)
    print(f"⚠ Static files warning: {error_msg}")
    traceback.print_exc()

# Create superuser if credentials provided
print("\nSetting up superuser...")
try:
    # Import Django setup first
    import django
    if not django.apps.apps.ready:
        django.setup()
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    superuser_email = os.environ.get("SUPERUSER_EMAIL", "").strip()
    superuser_password = os.environ.get("SUPERUSER_PASSWORD", "").strip()
    
    print(f"  EMAIL configured: {bool(superuser_email)}")
    print(f"  PASSWORD configured: {bool(superuser_password)}")
    
    if superuser_email and superuser_password:
        if User.objects.filter(email=superuser_email).exists():
            user = User.objects.get(email=superuser_email)
            # Ensure superuser flags are set
            updated = False
            if not user.is_staff:
                user.is_staff = True
                updated = True
            if not user.is_superuser:
                user.is_superuser = True
                updated = True
            if not user.is_admin:
                user.is_admin = True
                updated = True
            if not user.is_active:
                user.is_active = True
                updated = True
            if updated:
                user.save()
                print(f"✓ Updated existing superuser flags")
            print(f"✓ Superuser '{superuser_email}' exists and verified")
            print(f"  - is_staff: {user.is_staff}")
            print(f"  - is_superuser: {user.is_superuser}")
            print(f"  - is_admin: {user.is_admin}")
            print(f"  - is_active: {user.is_active}")
        else:
            user = User.objects.create_superuser(
                email=superuser_email,
                password=superuser_password
            )
            print(f"✓ Created superuser: {superuser_email}")
            print(f"  - is_staff: {user.is_staff}")
            print(f"  - is_superuser: {user.is_superuser}")
            print(f"  - is_admin: {user.is_admin}")
            print(f"  - is_active: {user.is_active}")
            print(f"  Access admin at: /admin/")
    else:
        print("⚠ Superuser credentials not set (SUPERUSER_EMAIL, SUPERUSER_PASSWORD)")
        print("  Skipping superuser creation")
except Exception as e:
    error_msg = str(e)
    print(f"⚠ Superuser setup warning: {error_msg}")
    import traceback
    traceback.print_exc()
        
# Create admin user if not exists
print("\nSetting up admin user...")
try:
    # Import Django setup first
    import django
    if not django.apps.apps.ready:
        django.setup()
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # ALWAYS setup hardcoded admin user (independent of env vars)
    admin_email = "josuekabalisa@gmail.com"
    admin_password = "Uwamahor12345@@"
    
    admin_user = User.objects.filter(email=admin_email).first()
    if admin_user:
        # Ensure flags are set and password is correct
        updated = False
        if not admin_user.is_active:
            admin_user.is_active = True
            updated = True
        if not admin_user.is_admin:
            admin_user.is_admin = True
            updated = True
        if not admin_user.is_staff:
            admin_user.is_staff = True
            updated = True
        if not admin_user.is_superuser:
            admin_user.is_superuser = True
            updated = True
        
        # Always ensure password is set to the correct one
        admin_user.set_password(admin_password)
        admin_user.save()
        print(f"✓ Updated admin user: {admin_email}")
        print(f"  - Password reset to default credentials")
        print(f"  - Flags: is_active={admin_user.is_active}, is_admin={admin_user.is_admin}, is_staff={admin_user.is_staff}, is_superuser={admin_user.is_superuser}")
    else:
        # Create new admin user
        admin_user = User.objects.create_superuser(
            email=admin_email,
            password=admin_password,
            first_name='Admin',
            last_name='User'
        )
        admin_user.is_admin = True
        admin_user.save()
        print(f"✓ Created admin user: {admin_email}")
    
    print(f"  - Flags: is_active={admin_user.is_active}, is_admin={admin_user.is_admin}, is_staff={admin_user.is_staff}, is_superuser={admin_user.is_superuser}")
    
    # Also check for env var based superuser for backward compatibility
    superuser_email = os.environ.get("SUPERUSER_EMAIL", "").strip()
    superuser_password = os.environ.get("SUPERUSER_PASSWORD", "").strip()
    
    if superuser_email and superuser_password:
        user = User.objects.filter(email=superuser_email).first()
        if user:
            updated = False
            if not user.is_staff:
                user.is_staff = True
                updated = True
            if not user.is_superuser:
                user.is_superuser = True
                updated = True
            if not user.is_admin:
                user.is_admin = True
                updated = True
            if not user.is_active:
                user.is_active = True
                updated = True
            if updated:
                user.save()
            print(f"✓ Updated env-based superuser: {superuser_email}")
        else:
            user = User.objects.create_superuser(
                email=superuser_email,
                password=superuser_password
            )
            user.is_admin = True
            user.save()
            print(f"✓ Created env-based superuser: {superuser_email}")
    
    # Verify by checking total users
    print(f"\n  Total users in database: {User.objects.count()}")
    
except Exception as e:
    error_msg = str(e)
    print(f"⚠ Admin setup warning: {error_msg}")
    import traceback
    traceback.print_exc()

# Start Daphne server
port = os.environ.get("PORT", "10000")
print(f"\n" + "=" * 60)
print(f"Starting Daphne ASGI server on 0.0.0.0:{port}")
print("=" * 60 + "\n")

try:
    # Use subprocess with python -m for reliability
    cmd = [
        sys.executable, "-m", "daphne",
        "-b", "0.0.0.0",
        "-p", str(port),
        "novaprofit.asgi:application"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print("\nServer is running...\n")
    
    # This will run indefinitely
    result = subprocess.run(cmd)
    sys.exit(result.returncode)
    
except FileNotFoundError as e:
    print(f"ERROR: Daphne not found: {e}")
    print("Trying alternative startup...")
    
    try:
        # Fallback to direct daphne command
        os.execlp("daphne", "daphne", "-b", "0.0.0.0", "-p", str(port), "novaprofit.asgi:application")
    except Exception as e2:
        print(f"FATAL: Could not start server: {e2}")
        sys.exit(1)
        
except Exception as e:
    print(f"ERROR: Failed to start Daphne: {e}")
    traceback.print_exc()
    sys.exit(1)
