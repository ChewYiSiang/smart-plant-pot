from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str = "your_openai_api_key_here"
    GOOGLE_API_KEY: str = "your_google_api_key_here"
    
    # Database
    DATABASE_URL: str = "sqlite:///./plant_pot.db"
    
    # Storage
    STORAGE_PATH: str = "./audio_artifacts"
    
    # Device Security
    DEVICE_API_KEY: str = "generate_a_secure_key_here"
    
    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings():
    return Settings()
