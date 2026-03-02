from __future__ import annotations

from typing import ClassVar

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    BOT_TOKEN: str
    ADMIN_ID: int = 0

    POSTGRES_DB: str = 'expense_tracker'
    POSTGRES_USER: str = 'expense_user'
    POSTGRES_PASSWORD: str = 'expense_password'
    POSTGRES_HOST: str = 'db'
    POSTGRES_PORT: int = 5432

    DATABASE_URL: str = ''
    TIMEZONE: str = 'Asia/Tashkent'

    BACKUP_DIR: str = 'backups'

    # Backup schedule env orqali boshqarilmaydi: har kuni 02:00, UTC+5.
    AUTO_BACKUP_ENABLED: ClassVar[bool] = True
    AUTO_BACKUP_SCHEDULE: ClassVar[str] = 'daily'
    AUTO_BACKUP_HOUR: ClassVar[int] = 2
    AUTO_BACKUP_MINUTE: ClassVar[int] = 0
    AUTO_BACKUP_UTC_OFFSET_HOURS: ClassVar[int] = 5

    AUTO_BACKUP_RETENTION_COUNT: ClassVar[int] = 5
    AUTO_BACKUP_PREFIX: ClassVar[str] = 'auto_expense_'
    MANUAL_BACKUP_PREFIX: ClassVar[str] = 'manual_expense_'
    PRE_RESTORE_BACKUP_PREFIX: ClassVar[str] = 'pre_restore_expense_'
    BACKUP_LOCK_TIMEOUT_SECONDS: ClassVar[int] = 600

    @model_validator(mode='after')
    def _build_database_url(self) -> 'Settings':
        if self.DATABASE_URL:
            return self

        self.DATABASE_URL = (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
        return self


config = Settings() # pyright: ignore[reportCallIssue]
