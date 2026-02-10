from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # API Keys
    GOOGLE_API_KEY: str = "your_google_api_key_here"
    
    # Database
    DATABASE_URL: str = "sqlite:///./plant_pot.db"
    
    # Storage
    STORAGE_PATH: str = "./audio_artifacts"
    
    # Hardware/Audio Configuration
    AUDIO_SAMPLE_RATE: int = 48000 # use 16000 which is optimized for ESP32 I2S
    AUDIO_CHANNELS: int = 1          # Mono
    AUDIO_BIT_DEPTH: int = 16       # 16-bit PCM
    WAKE_WORD: str = "hey plant"
    
    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

@lru_cache
def get_settings():
    return Settings()
