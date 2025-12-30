from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AudioMixMentor"
    host: str = "0.0.0.0"
    port: int = 5005
    data_dir: str = "data"
    uploads_dir: str = "data/uploads"
    results_dir: str = "data/results"
    genre_profiles_path: str = "config/genre_profiles.json"
    demo_seed: int = 42
    max_upload_mb: int = 500

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
