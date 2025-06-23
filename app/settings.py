from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  camera_device_id: int = 0
  camera_width: int = 1280
  camera_height: int = 720
  camera_fps: int = 10  
  
  # Authentication settings
  streaming_token_secret: str = "your-streaming-secret-key-change-in-production"
  
  model_config = SettingsConfigDict(
    env_file=".env", 
    env_file_empty=True,
    extra="ignore"
  )

settings = Settings()