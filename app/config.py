from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Vehicle Tracking Platform"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./vehicle_tracking.db"
    POSTGRES_URL: Optional[str] = None
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Mapbox
    MAPBOX_ACCESS_TOKEN: str = "your_mapbox_token_here"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"


settings = Settings()