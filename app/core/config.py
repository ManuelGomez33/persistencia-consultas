from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongo_uri: str
    mongo_database: str
    mongo_collection: str
    redis_url: str
    redis_ttl_seconds: int
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
