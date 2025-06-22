from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  camera_device_id: int = 0
  camera_width: int = 1280
  camera_height: int = 720
  camera_fps: int = 10

  # Authentication settings
  clerk_publishable_key: str = ""
  clerk_secret_key: str = ""
  clerk_jwt_verification: bool = True

  # Admin credentials for backend login
  admin_username: str = "admin"
  admin_email: str = "admin@ptt-home.local"
  admin_password: str = "123"

  # Development settings
  development_mode: bool = False

  model_config = SettingsConfigDict(
    env_file=".env", 
    env_file_empty=True,
    extra="ignore"
  )

settings = Settings()