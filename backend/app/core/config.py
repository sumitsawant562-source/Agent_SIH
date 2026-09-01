import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Agentic AI Personalized Travel Intelligence Platform"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"

    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # Gemini AI Configuration (Backend Only - NEVER expose to frontend)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # OpenWeatherMap Configuration (Backend Only - NEVER expose to frontend)
    OPENWEATHER_API_KEY: str = ""
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    OPENWEATHER_GEO_URL: str = "http://api.openweathermap.org/geo/1.0"

    # Routing Configuration (Backend Only - NEVER expose to frontend)
    OPENROUTESERVICE_API_KEY: str = ""
    OPENROUTESERVICE_BASE_URL: str = "https://api.openrouteservice.org/v2"
    OSRM_BASE_URL: str = "https://router.project-osrm.org"

    # CORS Configuration
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:3002,http://127.0.0.1:3002"

    @property
    def cors_origins(self) -> List[str]:
        default_dev_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "http://localhost:3002",
            "http://127.0.0.1:3002",
        ]
        if not self.ALLOWED_ORIGINS:
            return default_dev_origins
        configured = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
        # Merge configured origins with default development origins safely
        merged: List[str] = []
        for origin in configured + default_dev_origins:
            if origin != "*" and origin not in merged:
                merged.append(origin)
        return merged or default_dev_origins

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
