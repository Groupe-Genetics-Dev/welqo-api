from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import  urlparse


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env",  extra="allow")
    
    postgres_url: str 
    access_token_expire_minutes: int = 30
    secret_key: str
    algorithm: str = "HS256"

    @property
    def postgres_username(self) -> str:
        parsed = urlparse(self.postgres_url)
        return parsed.username or ""
    
    @property
    def postgres_password(self) -> str:
        parsed = urlparse(self.postgres_url)
        return parsed.password or ""
    
    @property
    def postgres_host(self) -> str:
        parsed = urlparse(self.postgres_url)
        return parsed.hostname or ""
    
    @property
    def postgres_port(self) -> int:
        parsed = urlparse(self.postgres_url)
        return parsed.port or 5432
    
    @property
    def postgres_database(self) -> str:
        parsed = urlparse(self.postgres_url)
        path = parsed.path
        if path.startswith('/'):
            path = path[1:]
        return path
    
    
    @property
    def postgres_database_url(self) -> str:
        return self.postgres_url
    


def get_settings() -> Settings:
    return Settings()

settings = get_settings()

