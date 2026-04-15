from django.core import signing
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

def send_activation_email(user):      # Generate a signed token with user PK and email the activation link
    token = signing.dumps(user.pk)

    activation_url = f"{settings.FRONTEND_URL}/activate/{token}"

    subject = 'Activate Your Crowdfund Account'
    message = (
        f"Hi {user.first_name},\n\n"
        f"Thanks for registering! Please click the link below to activate your account:\n\n"
        f"{activation_url}\n\n"
        f"This link will expire in 24 hours.\n\n"
        f"If you did not register for this account, you can safely ignore this email."
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    user.last_activation_sent = timezone.now()      # save when the activation email was sent for cooldown logic
    user.save(update_fields=['last_activation_sent'])
