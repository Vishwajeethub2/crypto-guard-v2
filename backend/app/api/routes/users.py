import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import User
from app.db.session import get_db
from app.schemas.auth import LoginResponse
from app.schemas.user import (
    ResendVerificationRequest,
    UserCreate,
    UserLogin,
    VerifyEmailRequest,
)
from app.services.auth import get_current_user
from app.services.email import send_verification_email
from app.services.jwt import create_access_token
from app.services.password import hash_password, verify_password


router = APIRouter(prefix="/users", tags=["Users"])


def generate_verification_code() -> str:
    """Generate a secure 6-digit email verification code."""
    return f"{secrets.randbelow(1_000_000):06d}"


def prepare_verification_code(user: User) -> str:
    """
    Generate and store a hashed verification code for a user.
    Returns the plain code so it can be sent by email.
    """
    code = generate_verification_code()

    user.verification_code_hash = hash_password(code)
    user.verification_code_expires_at = datetime.utcnow() + timedelta(
        minutes=settings.email_verification_expire_minutes
    )
    user.verification_attempts = 0

    return code


@router.post("/")
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    verification_code = generate_verification_code()

    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        is_email_verified=False,
        verification_code_hash=hash_password(verification_code),
        verification_code_expires_at=datetime.utcnow()
        + timedelta(
            minutes=settings.email_verification_expire_minutes
        ),
        verification_attempts=0,
    )

    db.add(user)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    db.refresh(user)

    try:
        send_verification_email(
            recipient_email=user.email,
            verification_code=verification_code,
        )
    except HTTPException:
        # The account has already been created.
        # The user can request another verification code later.
        raise

    return {
        "message": "Account created. Please verify your email before signing in.",
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "email_verified": user.is_email_verified,
    }


@router.post("/verify-email")
def verify_email(
    verification_data: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == verification_data.email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification code",
        )

    if user.is_email_verified:
        return {
            "message": "Email is already verified.",
            "email_verified": True,
        }

    if (
        user.verification_code_hash is None
        or user.verification_code_expires_at is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification code",
        )

    if user.verification_attempts >= 5:
        raise HTTPException(
            status_code=429,
            detail="Too many invalid verification attempts. Request a new code.",
        )

    if datetime.utcnow() > user.verification_code_expires_at:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification code",
        )

    if not verify_password(
        verification_data.code,
        user.verification_code_hash,
    ):
        user.verification_attempts += 1
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification code",
        )

    user.is_email_verified = True
    user.verification_code_hash = None
    user.verification_code_expires_at = None
    user.verification_attempts = 0

    db.commit()

    return {
        "message": "Email verified successfully. You can now sign in.",
        "email_verified": True,
    }


@router.post("/resend-verification")
def resend_verification(
    verification_data: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == verification_data.email)
        .first()
    )

    # Use the same response for unknown/already verified accounts
    # so this endpoint does not reveal account state.
    if user is None or user.is_email_verified:
        return {
            "message": "If the account requires verification, a new code has been sent."
        }

    verification_code = prepare_verification_code(user)

    db.commit()
    db.refresh(user)

    try:
        send_verification_email(
            recipient_email=user.email,
            verification_code=verification_code,
        )
    except HTTPException:
        raise

    return {
        "message": "If the account requires verification, a new code has been sent."
    }


@router.post("/login", response_model=LoginResponse)
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not verify_password(
        user_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not user.is_email_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before signing in.",
        )

    access_token = create_access_token(user.id)

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
    }


@router.get("/")
def get_users(
    db: Session = Depends(get_db),
):
    users = db.query(User).all()

    return [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "email_verified": user.is_email_verified,
            "created_at": user.created_at,
        }
        for user in users
    ]


@router.get("/me")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "email_verified": current_user.is_email_verified,
        "created_at": current_user.created_at,
    }


@router.get("/{user_id}")
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    user = current_user

    if user.id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only access your own profile",
        )

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "email_verified": user.is_email_verified,
        "created_at": user.created_at,
    }