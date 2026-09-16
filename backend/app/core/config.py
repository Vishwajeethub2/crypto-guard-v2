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


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()