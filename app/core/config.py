from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    smtp_server: str
    smtp_port: int
    sender_email: str
    sender_password: str
    web_client_id: str
    spoonacular_api_key: str
    google_translation_credentials: str
    google_image_uploader_credentials: str
    gcs_bucket_name: str
    cors_origins: str
    task_secret_key: str
    brevo_api_key: str
    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings():
    return Settings()
