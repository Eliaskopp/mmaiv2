from pathlib import Path

from pydantic_settings import BaseSettings

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "MMAi V2"
    debug: bool = False

    # Database
    database_url: str

    # Auth
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 10080  # 7 days

    # CORS
    allowed_origins: list[str] = ["http://localhost:5173"]

    # Email (Resend)
    resend_api_key: str = ""
    email_from: str = "MMAi Coach <noreply@mmai.coach>"
    app_url: str = "http://localhost:5173"

    # AI
    grok_api_key: str = ""
    grok_base_url: str = "https://api.x.ai/v1"

    model_config = {
        "env_file": str(BACKEND_DIR / ".env"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()
