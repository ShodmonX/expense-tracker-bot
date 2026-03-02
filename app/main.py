import asyncio
import logging

import pytz
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore

from config import config
from database import run_db
from handlers import (
    balance_handlers,
    bank_notification_handlers,
    db_backup_handlers,
    expense_handlers,
    income_handlers,
    main_handlers,
    payment_handlers,
    report_handlers,
    settings_handlers,
)
from services.db_backup.scheduler import setup_backup_scheduler
from services.reminder_service import ReminderService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

routers = [
    bank_notification_handlers.router,
    main_handlers.router,
    settings_handlers.router,
    db_backup_handlers.router,
    expense_handlers.router,
    payment_handlers.router,
    income_handlers.router,
    balance_handlers.router,
    report_handlers.router,
]


async def main():
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    for router in routers:
        dp.include_router(router)

    user_commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="menu", description="Asosiy menyu"),
        BotCommand(command="today", description="Bugungi hisobot"),
        BotCommand(command="report", description="Hisobot olish"),
        BotCommand(command="help", description="Yordam"),
    ]
    await bot.set_my_commands(user_commands)

    if config.ADMIN_ID:
        admin_commands = user_commands.copy()
        admin_commands.append(BotCommand(command="backup", description="DB backup (admin)"))
        await bot.set_my_commands(
            admin_commands,
            scope=BotCommandScopeChat(chat_id=config.ADMIN_ID),
        )

    scheduler = AsyncIOScheduler(timezone=pytz.timezone(config.TIMEZONE))
    setup_backup_scheduler(scheduler)

    scheduler.add_job(send_daily_reminders, 'cron', hour=9, minute=0, args=[bot])
    scheduler.add_job(send_overdue_reminders, 'cron', hour=9, minute=0, args=[bot])
    scheduler.add_job(send_overdue_reminders, 'cron', hour=18, minute=0, args=[bot])
    scheduler.add_job(send_daily_summary, 'cron', hour=23, minute=0, args=[bot])
    scheduler.add_job(check_reminders, 'interval', hours=1, args=[bot])
    scheduler.start()

    await dp.start_polling(bot)


async def send_daily_reminders(bot: Bot):
    from models import User

    users = await run_db(lambda db: db.query(User).all())
    for user in users:
        await ReminderService.send_daily_reminders(user.telegram_id, bot)


async def send_daily_summary(bot: Bot):
    from models import User

    users = await run_db(lambda db: db.query(User).all())
    for user in users:
        await ReminderService.send_daily_summary(user.telegram_id, bot)


async def check_reminders(bot: Bot):
    await ReminderService.check_and_send_reminders(bot)


async def send_overdue_reminders(bot: Bot):
    from models import User

    users = await run_db(lambda db: db.query(User).all())
    for user in users:
        await ReminderService.send_overdue_reminders(user.telegram_id, bot)


if __name__ == "__main__":
    asyncio.run(main())
