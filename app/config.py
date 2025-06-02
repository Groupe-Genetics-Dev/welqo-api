from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    postgres_username: str
    postgres_password: str
    postgres_host: str
    postgres_port: int = 5432
    postgres_database: str

    secret_key: str
    algorithm: str = "HS256"

    @property
    def postgres_database_url(self) -> str:
        url = URL.create(
            drivername="postgresql+psycopg2",
            username=self.postgres_username,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_database
        )
        return url.render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

