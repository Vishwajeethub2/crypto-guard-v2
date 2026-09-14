from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginResponse(BaseModel):
    message: str
    access_token: str
    token_type: str
    user_id: int
    email: str
    full_name: str | None = None