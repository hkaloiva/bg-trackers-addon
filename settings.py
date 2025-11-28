from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    addon_name: str = "BG Trackers Unified Search"
    addon_version: str = "0.1.0"
    port: int = 8080
    
    # Jackett/Prowlarr
    jackett_url: Optional[str] = None
    jackett_api_key: Optional[str] = None
    
    # Debrid Services
    realdebrid_api_key: Optional[str] = None
    alldebrid_api_key: Optional[str] = None
    torbox_api_key: Optional[str] = None
    
    # Redis
    redis_url: Optional[str] = None
    
    # Security
    secret_key: str = "change_this_to_a_random_secret_key"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
