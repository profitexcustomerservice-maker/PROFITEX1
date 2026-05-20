from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives


@shared_task(bind=True)
def send_otp_email_task(self, recipient_email, otp_code):
    """Send an OTP email asynchronously."""
    subject = "[Profitx] Your Verification Code"
    plain_message = (
        f"Your OTP code is: {otp_code}\n\n"
        "This code will expire in 5 minutes.\n\n"
        "If you did not request this code, please ignore this email."
    )
    html_message = f"""
    <p>Your OTP code is: <strong>{otp_code}</strong></p>
    <p>This code will expire in 5 minutes.</p>
    <p>If you did not request this code, please ignore this email.</p>
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [recipient_email]

    print(f"[Celery] Sending OTP email to {recipient_email}")
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=from_email,
        to=recipient_list,
        reply_to=[settings.EMAIL_HOST_USER],
        headers={'List-Unsubscribe': f'<mailto:{settings.EMAIL_HOST_USER}>'}
    )
    email.attach_alternative(html_message, "text/html")
    email.send(fail_silently=False)
    print(f"[Celery] OTP email queued/processed for {recipient_email}")
    return True
