from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str | None = None
    prod_database_url: str | None = None
    jwt_secret_key: str | None = None
    jwt_algorithm: str | None = "HS256"
    sender_email: str | None = None
    web_client_id: str | None = None
    spoonacular_api_key: str | None = None
    google_translation_credentials: str | None = None
    google_image_uploader_credentials: str | None = None
    gcs_bucket_name: str | None = None
    cors_origins: str | None = None
    task_secret_key: str | None = None
    brevo_api_key: str | None = None
    gcp_project_id: str | None = None
    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings():
    return Settings()
