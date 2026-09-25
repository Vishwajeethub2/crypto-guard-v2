from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Crypto Guard V2"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://localhost:5432/crypto_guard"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    alchemy_api_key: str

    neo4j_uri: str
    neo4j_username: str
    neo4j_password: str

    # Email / SMTP settings
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True
    smtp_timeout_seconds: int = 15

    # Email verification settings
    email_verification_expire_minutes: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()