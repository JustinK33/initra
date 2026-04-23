import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    env: str = os.getenv("APP_ENV", "development")


settings = Settings()
