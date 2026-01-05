import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler # type: ignore
import pytz
from sqlalchemy import text

from config import config
from database import engine, Base
from handlers import expense_handlers, payment_handlers, report_handlers
from handlers import main_handlers, income_handlers, balance_handlers
from keyboards import (
    get_main_menu,
    get_manage_menu,
    get_reports_menu,
    get_settings_keyboard,
    get_report_period_keyboard,
    get_expense_type_keyboard,
)
from services.reminder_service import ReminderService
from database import get_db

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import all routers
routers = [
    main_handlers.router,
    expense_handlers.router,
    payment_handlers.router,
    income_handlers.router,
    balance_handlers.router,
    report_handlers.router
]

def _ensure_payments_schema():
    """Lightweight schema migration for SQLite when new columns are added."""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(payments)"))
        existing_cols = {row[1] for row in result.fetchall()}

        if "weekday" not in existing_cols:
            conn.execute(text("ALTER TABLE payments ADD COLUMN weekday INTEGER"))
        if "day_of_month" not in existing_cols:
            conn.execute(text("ALTER TABLE payments ADD COLUMN day_of_month INTEGER"))
        if "is_skipped" not in existing_cols:
            conn.execute(text("ALTER TABLE payments ADD COLUMN is_skipped BOOLEAN DEFAULT 0"))
        if "overdue_last_sent_at" not in existing_cols:
            conn.execute(text("ALTER TABLE payments ADD COLUMN overdue_last_sent_at DATETIME"))
        if "category" not in existing_cols:
            conn.execute(text("ALTER TABLE payments ADD COLUMN category TEXT"))
        if "occurrences_left" not in existing_cols:
            conn.execute(text("ALTER TABLE payments ADD COLUMN occurrences_left INTEGER"))

        # Ensure income table exists
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'Kirim',
                date DATE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))

        conn.commit()

async def main():
    # Create database tables
    Base.metadata.create_all(bind=engine)
    _ensure_payments_schema()
    
    # Initialize bot and dispatcher
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Include routers
    for router in routers:
        dp.include_router(router)
    
    # Set bot commands
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="menu", description="Asosiy menyu"),
        BotCommand(command="today", description="Bugungi hisobot"),
        BotCommand(command="report", description="Hisobot olish"),
        BotCommand(command="help", description="Yordam")
    ]
    await bot.set_my_commands(commands)
    
    # Setup scheduler for reminders
    scheduler = AsyncIOScheduler(timezone=pytz.timezone(config.TIMEZONE))
    
    # Schedule daily reminders at 9:00 AM
    scheduler.add_job(
        send_daily_reminders,
        'cron',
        hour=9,
        minute=0,
        args=[bot]
    )

    scheduler.add_job(
        send_overdue_reminders,
        'cron',
        hour=9,
        minute=0,
        args=[bot]
    )

    scheduler.add_job(
        send_overdue_reminders,
        'cron',
        hour=18,
        minute=0,
        args=[bot]
    )
    
    # Schedule daily summary at 11:00 PM
    scheduler.add_job(
        send_daily_summary,
        'cron',
        hour=23,
        minute=0,
        args=[bot]
    )
    
    # Schedule reminder checks every hour
    scheduler.add_job(
        check_reminders,
        'interval',
        hours=1,
        args=[bot]
    )
    
    scheduler.start()
    
    # Start polling
    await dp.start_polling(bot)

async def send_daily_reminders(bot: Bot):
    """Send daily reminders"""
    db = next(get_db())
    from models import User
    users = db.query(User).all()
 
    for user in users:
        await ReminderService.send_daily_reminders(db, user.telegram_id, bot)

async def send_daily_summary(bot: Bot):
    """Send daily summary to all users"""
    db = next(get_db())
    from models import User
    users = db.query(User).all()
    
    for user in users:
        await ReminderService.send_daily_summary(db, user.telegram_id, bot)

async def check_reminders(bot: Bot):
    """Check and send all reminders"""
    db = next(get_db())
    await ReminderService.check_and_send_reminders(db, bot)

async def send_overdue_reminders(bot: Bot):
    """Send overdue payment reminders (twice per day by scheduler)."""
    db = next(get_db())
    from models import User
    users = db.query(User).all()

    for user in users:
        await ReminderService.send_overdue_reminders(db, user.telegram_id, bot)

if __name__ == "__main__":
    asyncio.run(main())