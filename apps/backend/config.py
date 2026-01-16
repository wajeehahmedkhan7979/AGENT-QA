from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    database_url: str = Field(
        default="sqlite:///./qa_demo.db",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    storage_backend: str = Field(default="localfs", alias="STORAGE_BACKEND")
    storage_root: str = Field(default="./artifacts", alias="STORAGE_ROOT")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

