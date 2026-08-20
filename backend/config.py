from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    github_token: str = ""
    max_repositories: int = 500
    collection_interval: int = 5
    database_url: str = "sqlite:///./liverank.db"
    dashboard_refresh_interval: int = 30
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
