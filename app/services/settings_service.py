from sqlalchemy.orm import Session

from config import config
from models import UserSettings


class SettingsService:
    @staticmethod
    def get_or_create(db: Session, user_id: int) -> UserSettings:
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if settings:
            return settings

        settings = UserSettings(
            user_id=user_id,
            timezone=config.TIMEZONE,
            report_format="xlsx",
            daily_reminder_enabled=True,
            overdue_reminder_enabled=True,
            daily_summary_enabled=True,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings

    @staticmethod
    def set_timezone(db: Session, user_id: int, timezone_name: str) -> UserSettings:
        settings = SettingsService.get_or_create(db, user_id)
        settings.timezone = timezone_name
        db.commit()
        db.refresh(settings)
        return settings

    @staticmethod
    def set_report_format(db: Session, user_id: int, report_format: str) -> UserSettings:
        settings = SettingsService.get_or_create(db, user_id)
        normalized = (report_format or "").strip().lower()
        settings.report_format = "pdf" if normalized == "pdf" else "xlsx"
        db.commit()
        db.refresh(settings)
        return settings

    @staticmethod
    def toggle_daily_reminder(db: Session, user_id: int) -> UserSettings:
        settings = SettingsService.get_or_create(db, user_id)
        settings.daily_reminder_enabled = not bool(settings.daily_reminder_enabled)
        db.commit()
        db.refresh(settings)
        return settings

    @staticmethod
    def toggle_overdue_reminder(db: Session, user_id: int) -> UserSettings:
        settings = SettingsService.get_or_create(db, user_id)
        settings.overdue_reminder_enabled = not bool(settings.overdue_reminder_enabled)
        db.commit()
        db.refresh(settings)
        return settings

    @staticmethod
    def toggle_daily_summary(db: Session, user_id: int) -> UserSettings:
        settings = SettingsService.get_or_create(db, user_id)
        settings.daily_summary_enabled = not bool(settings.daily_summary_enabled)
        db.commit()
        db.refresh(settings)
        return settings
