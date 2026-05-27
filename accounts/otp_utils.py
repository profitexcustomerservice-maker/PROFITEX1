import random
import time

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives

from .models import OTP


def generate_otp():
    """Generate a 6-digit OTP code."""
    return str(random.randint(100000, 999999))


def send_otp_email(user, otp):
    """Send OTP email to user with enhanced debugging."""
    subject = "[Profitex] Your Verification Code"
    plain_message = (
        f"Your OTP code is: {otp}\n\n"
        "This code will expire in 5 minutes.\n\n"
        "If you did not request this code, please ignore this email."
    )
    html_message = f"""
    <p>Your OTP code is: <strong>{otp}</strong></p>
    <p>This code will expire in 5 minutes.</p>
    <p>If you did not request this code, please ignore this email.</p>
    """
    recipient_email = (user.email or "").strip().lower()
    if not recipient_email:
        print(f"ERROR: User has invalid or empty email. User ID: {user.id}")
        return False

    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [recipient_email]

    print("\n" + "="*60)
    print("EMAIL SENDING DEBUG")
    print("="*60)
    print(f"Recipient: {recipient_email}")
    print(f"From: {from_email}")
    print(f"Email Backend: {settings.EMAIL_BACKEND}")
    print(f"Email Host: {settings.EMAIL_HOST}")
    print(f"Email Port: {settings.EMAIL_PORT}")
    print(f"Email User: {settings.EMAIL_HOST_USER}")
    print(f"Email Password Set: {bool(settings.EMAIL_HOST_PASSWORD)}")
    print(f"TLS Enabled: {settings.EMAIL_USE_TLS}")
    print("="*60 + "\n")

    max_attempts = 3
    backoff_seconds = 1

    for attempt in range(1, max_attempts + 1):
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=from_email,
                to=recipient_list,
                reply_to=[settings.EMAIL_HOST_USER],
                headers={
                    'List-Unsubscribe': f'<mailto:{settings.EMAIL_HOST_USER}>'
                }
            )
            # attach HTML alternative
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            print(f"[OK] EMAIL SENT SUCCESSFULLY to {recipient_email} (attempt {attempt})")
            return True
        except Exception as exc:
            error_type = type(exc).__name__
            error_msg = str(exc)
            print(f"[ERROR] EMAIL ERROR on attempt {attempt}/{max_attempts}")
            print(f"  Type: {error_type}")
            print(f"  Message: {error_msg}")
            print(f"  Recipient: {recipient_email}")
            
            import traceback
            print("  Traceback:")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    print(f"    {line}")
            
            if attempt == max_attempts:
                print(f"[ERROR] EMAIL FAILED after {max_attempts} attempts!")
                return False
            
            print(f"  Retrying in {backoff_seconds} seconds...")
            time.sleep(backoff_seconds)
            backoff_seconds *= 2
    
    return False


def queue_send_otp_email(user, otp):
    """Queue OTP email delivery via Celery when available, with fallback to sync send."""
    try:
        from .tasks import send_otp_email_task
        send_otp_email_task.delay(user.email, otp)
        print(f"Queued OTP email for {user.email}")
        return True
    except Exception as exc:
        print(f"Failed to queue OTP email, sending synchronously: {exc}")
    # Always try direct send as final fallback (works with console backend)
    return send_otp_email(user, otp)


def create_and_send_otp(user):
    """Create an OTP record and send it to the user's email."""
    if not user.email:
        print(f"ERROR: User has no email address. User ID: {user.id}")
        return None, False

    print(f"Creating OTP for user: {user.email}")

    OTP.objects.filter(user=user, is_verified=False).delete()

    otp_code = generate_otp()
    print(f"Generated OTP: {otp_code}")

    otp = OTP.objects.create(user=user, code=otp_code)
    print(f"OTP record created with ID: {otp.id}")

    email_sent = queue_send_otp_email(user, otp_code)
    return otp, email_sent


def verify_otp(user, code):
    """Verify the latest unverified OTP code for a user."""
    otp = OTP.objects.filter(user=user, is_verified=False).order_by("-created_at").first()

    if not otp:
        return False, "No OTP found. Please request a new code."

    if otp.is_expired():
        return False, "OTP has expired. Please request a new code."

    if otp.attempts >= 3:
        return False, "Too many failed attempts. Please request a new code."

    if otp.code == code:
        otp.is_verified = True
        otp.save(update_fields=["is_verified"])
        return True, "OTP verified successfully"

    otp.attempts += 1
    otp.save(update_fields=["attempts"])
    remaining_attempts = 3 - otp.attempts
    return False, f"Invalid OTP. {remaining_attempts} attempts remaining."
