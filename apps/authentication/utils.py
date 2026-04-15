from django.core import signing
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.core.signing import TimestampSigner
from urllib.parse import quote


def send_activation_email(user):      # Generate a signed token with user PK and email the activation link
    signer=TimestampSigner(salt='activation') #create token (value&timestamp)
    
    token = quote(signer.sign(str(user.pk)), safe='')

    activation_url = f"{settings.FRONTEND_URL}/activate/{token}"

    subject = 'Activate Your Crowdfund Account'
    message = (
        f"Hi {user.first_name},\n\n"
        f"Thanks for registering! Please click the link below to activate your account:\n\n"
        f"{activation_url}\n\n"
        f"This link will expire in 24 hours.\n\n"
        f"If you did not register for this account, you can safely ignore this email."
    )

    send_mail( #connect to smtp in .env
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    user.last_activation_sent = timezone.now()      # save when the activation email was sent for cooldown logic
    user.save(update_fields=['last_activation_sent'])



# 1. Receive user object
#         ↓
# 2. signing.dumps(user.pk) → creates cryptographically signed token
#         ↓
# 3. Build activation URL with FRONTEND_URL + token
#         ↓
# 4. Create email subject and message body
#         ↓
# 5. send_mail() → sends email via Mailtrap (sandbox) or real SMTP (production)
#         ↓
# 6. Update user.last_activation_sent timestamp
#         ↓
# 7. Save only that field to database


# 1:1wD4jp:XKn0yqgvM9TThATEAXHxYdzJDl7-yHhPIrg41HFoEk8
# │   │   └─────────────────────────────────────────────┘
# │   │                Signature (cryptographic proof)
# │   └─────────── Timestamp (encoded)
# └─────────────── User ID (1)
