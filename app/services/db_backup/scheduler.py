import logging
from datetime import timedelta, timezone

from config import config
from services.db_backup.engine import backup_engine


logger = logging.getLogger(__name__)


def setup_backup_scheduler(scheduler) -> None:
    if not config.AUTO_BACKUP_ENABLED:
        logger.info("Auto backup o'chirilgan")
        return

    backup_timezone = timezone(
        timedelta(hours=config.AUTO_BACKUP_UTC_OFFSET_HOURS)
    )

    trigger_kwargs: dict[str, int | str | timezone] = {
        "hour": config.AUTO_BACKUP_HOUR,
        "minute": config.AUTO_BACKUP_MINUTE,
        "timezone": backup_timezone,
    }

    scheduler.add_job(
        _run_auto_backup,
        "cron",
        id="auto-backup",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        **trigger_kwargs,
    )

    logger.info(
        "Auto backup scheduler yoqildi: schedule=%s time=%02d:%02d UTC%+d",
        config.AUTO_BACKUP_SCHEDULE,
        config.AUTO_BACKUP_HOUR,
        config.AUTO_BACKUP_MINUTE,
        config.AUTO_BACKUP_UTC_OFFSET_HOURS,
    )


async def _run_auto_backup() -> None:
    try:
        backup = await backup_engine.create_backup("auto")
        cleaned = await backup_engine.cleanup_auto_backups(
            config.AUTO_BACKUP_RETENTION_COUNT
        )
        logger.info(
            "Auto backup muvaffaqiyatli: %s (cleanup=%d)",
            backup.filename,
            cleaned,
        )
    except Exception:
        logger.exception("Auto backup bajarilmadi")
