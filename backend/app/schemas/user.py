from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):

    email: EmailStr

    password: str = Field(min_length=8, max_length=128)

    full_name: str | None = None


class UserLogin(BaseModel):

    email: EmailStr

    password: str


class VerifyEmailRequest(BaseModel):

    email: EmailStr

    code: str = Field(pattern=r"^\d{6}$")


class ResendVerificationRequest(BaseModel):

    email: EmailStr