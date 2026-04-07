from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 60
    REFRESH_TOKEN_SECRET: str = ""
    REFRESH_TOKEN_MAX_PER_USER: int = 5

    UPLOAD_DIR: str = "static/uploads"
    UPLOAD_MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_TEMP_MAX_PER_USER: int = 20
    UPLOAD_TEMP_EXPIRE_HOURS: int = 24
    UPLOAD_MAX_IMAGES_PER_POST: int = 10
    UPLOAD_BASE_URL: str = "http://localhost:8000/static/uploads"

    model_config = {"env_file": ".env"}


settings = Settings()
