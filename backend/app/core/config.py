from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "DentoScan API"
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    app_version: str = "2.0.0"

    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "https://dento-scan.netlify.app",
            "https://dentoscan.netlify.app",
            "https://dento-scan.vercel.app",
            "https://dentoscan.vercel.app",
        ],
        validation_alias="CORS_ORIGINS",
    )

    roboflow_api_key: str | None = Field(default=None, validation_alias="ROBOFLOW_API_KEY")
    roboflow_model_id: str = Field(default="adr/6", validation_alias="ROBOFLOW_MODEL_ID")
    roboflow_confidence_threshold: float = Field(
        default=0.3,
        validation_alias="ROBOFLOW_CONFIDENCE_THRESHOLD",
    )
    roboflow_overlap_threshold: float = Field(
        default=0.5,
        validation_alias="ROBOFLOW_OVERLAP_THRESHOLD",
    )
    roboflow_base_url: str = Field(
        default="https://detect.roboflow.com",
        validation_alias="ROBOFLOW_BASE_URL",
    )

    groq_api_key: str | None = Field(default=None, validation_alias="GROQ_API_KEY")
    groq_model: str = Field(default="openai/gpt-oss-120b", validation_alias="GROQ_MODEL")
    groq_fallback_models: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "llama-3.3-70b-versatile",
            "openai/gpt-oss-20b",
        ],
        validation_alias="GROQ_FALLBACK_MODELS",
    )

    request_timeout_seconds: float = Field(default=20.0, validation_alias="REQUEST_TIMEOUT_SECONDS")
    roboflow_timeout_seconds: float | None = Field(
        default=None,
        validation_alias="ROBOFLOW_TIMEOUT_SECONDS",
    )
    groq_timeout_seconds: float = Field(default=12.0, validation_alias="GROQ_TIMEOUT_SECONDS")
    max_upload_size_mb: int = Field(default=50, validation_alias="MAX_UPLOAD_SIZE_MB")
    max_file_age_hours: int = Field(default=24, validation_alias="MAX_FILE_AGE_HOURS")
    cleanup_interval_seconds: int = Field(default=3600, validation_alias="CLEANUP_INTERVAL_SECONDS")

    upload_dir: Path = Field(default=BACKEND_ROOT / "uploads")
    static_dir: Path = Field(default=BACKEND_ROOT / "static")
    temp_dir: Path = Field(default=BACKEND_ROOT / "temp")

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("cors_origins", "groq_fallback_models", mode="before")
    @classmethod
    def _parse_list(cls, value: object) -> object:
        if value is None or isinstance(value, list):
            return value
        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []
            if raw_value.startswith("["):
                return json.loads(raw_value)
            return [item.strip() for item in raw_value.split(",") if item.strip()]
        return value

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def roboflow_request_timeout_seconds(self) -> float:
        return self.roboflow_timeout_seconds or self.request_timeout_seconds

    @property
    def report_models(self) -> list[str]:
        seen: set[str] = set()
        models: list[str] = []
        for model in [self.groq_model, *self.groq_fallback_models]:
            if model and model not in seen:
                seen.add(model)
                models.append(model)
        return models


@lru_cache
def get_settings() -> Settings:
    return Settings()
