from functools import lru_cache
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DSP_", extra="ignore")
    app_name: str = "Data Science Path"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://dsp:dsp@localhost:5432/dsp"
    secret_key: str = Field(default="change-me-in-production", min_length=16)
    access_token_minutes: int = 60 * 24 * 7
    frontend_url: str = "http://localhost:3000"
    secure_cookies: bool = False

    @model_validator(mode="after")
    def production_safety(self):
        if self.environment == "production":
            if self.secret_key == "change-me-in-production" or not self.secure_cookies:
                raise ValueError("Production requires a unique DSP_SECRET_KEY and DSP_SECURE_COOKIES=true")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
