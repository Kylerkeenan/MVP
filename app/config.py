from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    db_backend: str = 'sqlite'
    sqlite_path: str = './data/nba_mvp.db'

    postgres_host: str = 'localhost'
    postgres_port: int = 5432
    postgres_db: str = 'nba'
    postgres_user: str = 'nba'
    postgres_password: str = 'nba'

    api_throttle_seconds: float = 0.7
    cache_dir: str = './data/cache'

    def database_url(self) -> str:
        if self.db_backend.lower() == 'postgres':
            return (
                f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return f"sqlite:///{self.sqlite_path}"

    def ensure_dirs(self) -> None:
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        if self.db_backend.lower() == 'sqlite':
            Path(self.sqlite_path).parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
