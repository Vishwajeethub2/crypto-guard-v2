import smtplib
from email.message import EmailMessage

from fastapi import HTTPException

from app.core.config import settings


def send_verification_email(
    recipient_email: str,
    verification_code: str,
) -> None:
    """
    Send an email containing the user's verification code.

    SMTP configuration is loaded from the application settings.
    The verification code is never returned to the API response.
    """

    if not settings.smtp_host or not settings.smtp_from_email:
        raise HTTPException(
            status_code=503,
            detail="Email delivery is not configured on the server.",
        )

    message = EmailMessage()

    message["Subject"] = "Crypto Guard V2 - Email Verification"
    message["From"] = settings.smtp_from_email
    message["To"] = recipient_email

    message.set_content(
        f"""Hello,

Your Crypto Guard V2 email verification code is:

{verification_code}

This code will expire in {settings.email_verification_expire_minutes} minutes.

If you did not create a Crypto Guard V2 account, you can safely ignore this email.

Regards,
Crypto Guard V2
"""
    )

    try:
        if settings.smtp_use_tls:
            with smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            ) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()

                if settings.smtp_username and settings.smtp_password:
                    server.login(
                        settings.smtp_username,
                        settings.smtp_password,
                    )

                server.send_message(message)

        else:
            with smtplib.SMTP_SSL(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            ) as server:

                if settings.smtp_username and settings.smtp_password:
                    server.login(
                        settings.smtp_username,
                        settings.smtp_password,
                    )

                server.send_message(message)

    except (smtplib.SMTPException, OSError) as exc:
        print(
            f"SMTP ERROR: {type(exc).__name__}: {exc}"
        )
        raise HTTPException(
            status_code=503,
            detail="Unable to send verification email. Please try again.",
        )