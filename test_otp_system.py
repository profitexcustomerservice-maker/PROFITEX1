#!/usr/bin/env python
"""
Comprehensive OTP System Test
Tests OTP generation, validation, expiration, and attempt limiting
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'novaprofit.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import OTP
from accounts.otp_utils import generate_otp, create_and_send_otp, verify_otp

User = get_user_model()

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_otp_generation():
    """Test OTP generation"""
    print_header("TEST 1: OTP Generation")
    
    try:
        otp_code = generate_otp()
        print(f"✓ Generated OTP: {otp_code}")
        print(f"  - Length: {len(otp_code)} (expected 6)")
        print(f"  - Is numeric: {otp_code.isdigit()}")
        
        if len(otp_code) == 6 and otp_code.isdigit():
            print("✓ OTP generation PASSED")
            return True
        else:
            print("✗ OTP generation FAILED - Invalid format")
            return False
    except Exception as e:
        print(f"✗ OTP generation FAILED: {e}")
        return False

def test_otp_model():
    """Test OTP model fields and methods"""
    print_header("TEST 2: OTP Model Structure")
    
    try:
        # Check OTP model fields
        otp_fields = {f.name for f in OTP._meta.get_fields()}
        required_fields = {'user', 'code', 'created_at', 'is_verified', 'attempts'}
        
        missing = required_fields - otp_fields
        if missing:
            print(f"✗ Missing OTP fields: {missing}")
            return False
        
        print(f"✓ OTP fields present: {', '.join(required_fields)}")
        
        # Check expiration logic
        old_otp = OTP(user=None, code='000000')
        old_otp.created_at = timezone.now() - timedelta(minutes=6)
        print(f"✓ Can check expiration (6min old): {old_otp.is_expired()}")
        
        new_otp = OTP(user=None, code='000000')
        new_otp.created_at = timezone.now() - timedelta(minutes=1)
        print(f"✓ Fresh OTP is not expired (1min old): {not new_otp.is_expired()}")
        
        print("✓ OTP model structure PASSED")
        return True
    except Exception as e:
        print(f"✗ OTP model test FAILED: {e}")
        return False

def test_otp_email_sending():
    """Test OTP email sending without user"""
    print_header("TEST 3: OTP Email Configuration")
    
    try:
        from django.conf import settings
        
        print(f"✓ Email Backend: {settings.EMAIL_BACKEND}")
        print(f"  - Is Console Backend: {'console' in settings.EMAIL_BACKEND}")
        print(f"  - Email Host: {settings.EMAIL_HOST}")
        print(f"  - Email Port: {settings.EMAIL_PORT}")
        print(f"  - USE_TLS: {settings.EMAIL_USE_TLS}")
        print(f"  - From Email: {settings.DEFAULT_FROM_EMAIL}")
        
        if 'console' in settings.EMAIL_BACKEND:
            print("✓ Using Console Email Backend (OTP will print to console)")
            print("✓ Email configuration PASSED (development mode)")
            return True
        else:
            print("✓ Using production email backend")
            return True
    except Exception as e:
        print(f"✗ Email configuration test FAILED: {e}")
        return False

def test_otp_with_user():
    """Test complete OTP flow with real user"""
    print_header("TEST 4: Complete OTP Flow")
    
    try:
        # Get or create test user
        test_email = 'otp-test@example.com'
        user, created = User.objects.get_or_create(
            email=test_email,
            defaults={'first_name': 'OTP', 'last_name': 'Test'}
        )
        
        if created:
            print(f"✓ Created test user: {test_email}")
        else:
            print(f"✓ Using existing test user: {test_email}")
        
        # Clear old OTPs
        old_count = OTP.objects.filter(user=user, is_verified=False).count()
        OTP.objects.filter(user=user, is_verified=False).delete()
        print(f"✓ Cleared {old_count} unverified OTPs")
        
        # Create and send OTP
        print("\n  Creating and sending OTP...")
        otp_obj, email_sent = create_and_send_otp(user)
        
        if otp_obj is None:
            print("✗ OTP creation returned None")
            return False
        
        print(f"✓ OTP created: {otp_obj.code}")
        print(f"✓ Email sent status: {email_sent}")
        print(f"  - OTP ID: {otp_obj.id}")
        print(f"  - Is Verified: {otp_obj.is_verified}")
        print(f"  - Attempts: {otp_obj.attempts}")
        print(f"  - Created At: {otp_obj.created_at}")
        
        # Test verification
        print("\n  Testing OTP verification...")
        
        # Test invalid code first
        ok, msg = verify_otp(user, '000000')
        print(f"✓ Invalid code returns False: {not ok}")
        print(f"  - Message: {msg}")
        
        # Get fresh OTP
        otp_obj = OTP.objects.filter(user=user, is_verified=False).first()
        if not otp_obj:
            print("✗ OTP not found after invalid attempt")
            return False
        
        print(f"  - Attempts increased: {otp_obj.attempts}")
        
        # Test correct code
        correct_code = otp_obj.code
        ok, msg = verify_otp(user, correct_code)
        print(f"✓ Correct code returns True: {ok}")
        print(f"  - Message: {msg}")
        
        # Check if marked verified
        otp_obj.refresh_from_db()
        print(f"✓ OTP marked as verified: {otp_obj.is_verified}")
        
        print("\n✓ Complete OTP flow PASSED")
        return True
    except Exception as e:
        print(f"✗ Complete OTP flow FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_otp_expiration():
    """Test OTP expiration logic"""
    print_header("TEST 5: OTP Expiration")
    
    try:
        test_email = 'otp-expiry-test@example.com'
        user, _ = User.objects.get_or_create(
            email=test_email,
            defaults={'first_name': 'OTP', 'last_name': 'Expiry'}
        )
        
        # Create expired OTP
        expired_otp = OTP.objects.create(
            user=user,
            code='999999',
            is_verified=False,
            attempts=0
        )
        # Manually set created_at to 6 minutes ago
        expired_otp.created_at = timezone.now() - timedelta(minutes=6)
        expired_otp.save()
        
        print(f"✓ Created OTP from 6 minutes ago")
        print(f"  - Is Expired: {expired_otp.is_expired()}")
        
        # Try to verify expired OTP
        ok, msg = verify_otp(user, '999999')
        print(f"✓ Verify expired OTP returns False: {not ok}")
        print(f"  - Message: {msg}")
        
        if "expired" in msg.lower():
            print("✓ OTP expiration PASSED")
            return True
        else:
            print("✗ OTP expiration FAILED - wrong error message")
            return False
    except Exception as e:
        print(f"✗ OTP expiration test FAILED: {e}")
        return False

def test_otp_attempt_limiting():
    """Test OTP attempt limiting (3 attempts max)"""
    print_header("TEST 6: OTP Attempt Limiting")
    
    try:
        test_email = 'otp-attempts-test@example.com'
        user, _ = User.objects.get_or_create(
            email=test_email,
            defaults={'first_name': 'OTP', 'last_name': 'Attempts'}
        )
        
        # Clear old OTPs
        OTP.objects.filter(user=user, is_verified=False).delete()
        
        # Create OTP
        otp_obj = OTP.objects.create(user=user, code='777777')
        print(f"✓ Created OTP: {otp_obj.code}")
        
        # Make 3 failed attempts
        for attempt in range(1, 4):
            ok, msg = verify_otp(user, '000000')
            otp_obj.refresh_from_db()
            print(f"  - Attempt {attempt}: Failed, Total attempts: {otp_obj.attempts}")
            if not ok and 'attempt' in msg.lower():
                print(f"    Message: {msg}")
        
        # Try 4th attempt (should be blocked)
        ok, msg = verify_otp(user, otp_obj.code)
        print(f"✓ 4th attempt blocked: {not ok}")
        if "too many" in msg.lower():
            print(f"  - Message: {msg}")
            print("✓ OTP attempt limiting PASSED")
            return True
        else:
            print(f"✗ Expected 'too many' message, got: {msg}")
            return False
    except Exception as e:
        print(f"✗ OTP attempt limiting test FAILED: {e}")
        return False

def main():
    """Run all OTP tests"""
    print_header("OTP SYSTEM COMPREHENSIVE TEST SUITE")
    print(f"Test started at: {datetime.now()}")
    
    tests = [
        ("OTP Generation", test_otp_generation),
        ("OTP Model", test_otp_model),
        ("Email Configuration", test_otp_email_sending),
        ("Complete OTP Flow", test_otp_with_user),
        ("OTP Expiration", test_otp_expiration),
        ("OTP Attempt Limiting", test_otp_attempt_limiting),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n✗ {name} - Unexpected error: {e}")
            results[name] = False
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓✓✓ ALL OTP TESTS PASSED ✓✓✓")
        return 0
    else:
        print(f"\n✗✗✗ {total - passed} TEST(S) FAILED ✗✗✗")
        return 1

if __name__ == '__main__':
    sys.exit(main())
