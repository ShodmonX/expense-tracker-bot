from datetime import datetime, date
import pytz

from config import config
from database import run_db


class ReminderService:
    @staticmethod
    async def _get_user_settings(user_id: int):
        from services.settings_service import SettingsService

        return await run_db(SettingsService.get_or_create, user_id)

    @staticmethod
    async def check_and_send_reminders(bot):
        """Check and send all types of reminders"""
        from models import User

        users = await run_db(lambda db: db.query(User).all())

        for user in users:
            await ReminderService.send_daily_reminders(user.telegram_id, bot)
            await ReminderService.send_monthly_reminders(user.telegram_id, bot)
            await ReminderService.send_yearly_reminders(user.telegram_id, bot)

    @staticmethod
    async def send_daily_reminders(user_id: int, bot):
        """Send reminders for payments due tomorrow"""
        from services.payment_service import PaymentService
        from keyboards import get_payment_reminder_actions_keyboard

        settings = await ReminderService._get_user_settings(user_id)
        if not settings.daily_reminder_enabled:
            return

        payments = await run_db(PaymentService.get_payments_due_tomorrow, user_id)

        if payments:
            for payment in payments:
                message = "📢 **ERTAGA TO'LOV ESLATMASI:**\n\n"
                message += f"📝 {payment.description}\n"
                message += f"💰 {payment.amount:,.0f} so'm\n"
                message += f"📅 Sana: {payment.due_date.strftime('%d.%m.%Y')}\n"

                try:
                    await bot.send_message(
                        user_id,
                        message,
                        parse_mode="Markdown",
                        reply_markup=get_payment_reminder_actions_keyboard(payment.id),
                    )
                    await run_db(PaymentService.mark_reminder_sent, [payment.id])
                except Exception as e:
                    print(f"Error sending reminder to {user_id}: {e}")

    @staticmethod
    async def send_monthly_reminders(user_id: int, bot):
        """Send reminders for monthly payments in last 3 days"""
        from services.payment_service import PaymentService
        from keyboards import get_payment_reminder_actions_keyboard

        settings = await ReminderService._get_user_settings(user_id)
        if not settings.daily_reminder_enabled:
            return

        payments = await run_db(PaymentService.get_monthly_payments_due_in_3_days, user_id)

        if payments:
            today = date.today()
            for payment in payments:
                days_left = (payment.due_date - today).days
                message = f"⏰ **OYLIK TO'LOV ESLATMASI:**\n\n"
                message += f"{payment.description} to'lovi {days_left} kun qoldi\n"
                message += f"Miqdori: {payment.amount:,.0f} so'm\n"
                message += f"To'lov sanasi: {payment.due_date.strftime('%d.%m.%Y')}"

                try:
                    await bot.send_message(
                        user_id,
                        message,
                        parse_mode="Markdown",
                        reply_markup=get_payment_reminder_actions_keyboard(payment.id),
                    )
                except Exception as e:
                    print(f"Error sending monthly reminder to {user_id}: {e}")

            payment_ids = [p.id for p in payments]
            await run_db(PaymentService.mark_reminder_sent, payment_ids)

    @staticmethod
    async def send_yearly_reminders(user_id: int, bot):
        """Send reminders for yearly payments in last 7 days"""
        from services.payment_service import PaymentService
        from keyboards import get_payment_reminder_actions_keyboard

        settings = await ReminderService._get_user_settings(user_id)
        if not settings.daily_reminder_enabled:
            return

        payments = await run_db(PaymentService.get_yearly_payments_due_in_week, user_id)

        if payments:
            today = date.today()
            for payment in payments:
                days_left = (payment.due_date - today).days
                message = f"🎯 **YILLIK TO'LOV ESLATMASI:**\n\n"
                message += f"{payment.description} to'lovi {days_left} kun qoldi\n"
                message += f"Miqdori: {payment.amount:,.0f} so'm\n"
                message += f"To'lov sanasi: {payment.due_date.strftime('%d.%m.%Y')}"

                try:
                    await bot.send_message(
                        user_id,
                        message,
                        parse_mode="Markdown",
                        reply_markup=get_payment_reminder_actions_keyboard(payment.id),
                    )
                except Exception as e:
                    print(f"Error sending yearly reminder to {user_id}: {e}")

            payment_ids = [p.id for p in payments]
            await run_db(PaymentService.mark_reminder_sent, payment_ids)

    @staticmethod
    async def send_daily_summary(user_id: int, bot):
        """Send daily expense summary at end of day"""
        from services.expense_service import ExpenseService

        settings = await ReminderService._get_user_settings(user_id)
        if not settings.daily_summary_enabled:
            return

        today = date.today()
        expenses = await run_db(ExpenseService.get_today_expenses, user_id)

        if expenses:
            total = sum(exp.amount for exp in expenses)
            category_totals = await run_db(
                ExpenseService.get_expenses_by_category,
                user_id,
                today,
                today,
            )

            message = f"📊 **KUNLIK HISOBOT - {today.strftime('%d.%m.%Y')}**\n\n"
            message += f"📈 Jami xarajat: {total:,.0f} so'm\n"
            message += f"📝 Xarajatlar soni: {len(expenses)}\n\n"
            message += "📋 **Kategoriyalar bo'yicha:**\n"

            for category, amount in category_totals.items():
                percentage = (amount / total * 100) if total > 0 else 0
                message += f"• {category}: {amount:,.0f} so'm ({percentage:.1f}%)\n"

            timezone_name = settings.timezone or config.TIMEZONE
            message += (
                f"\n⏰ Hisobot vaqti: "
                f"{datetime.now(pytz.timezone(timezone_name)).strftime('%H:%M')}"
            )

            try:
                await bot.send_message(user_id, message, parse_mode="Markdown")
            except Exception as e:
                print(f"Error sending daily summary to {user_id}: {e}")

    @staticmethod
    async def send_overdue_reminders(user_id: int, bot):
        """Send reminders for overdue payments (due_date < today)."""
        from services.payment_service import PaymentService
        from keyboards import get_payment_reminder_actions_keyboard

        settings = await ReminderService._get_user_settings(user_id)
        if not settings.overdue_reminder_enabled:
            return

        now_utc = datetime.utcnow()
        payments = await run_db(PaymentService.get_overdue_payments, user_id)
        if not payments:
            return

        # Rate-limit: at most once per ~8 hours per payment (scheduler is 2x/day)
        to_send = []
        for p in payments:
            last = getattr(p, "overdue_last_sent_at", None)
            if last is None:
                to_send.append(p)
                continue
            try:
                if (now_utc - last).total_seconds() >= 8 * 3600:
                    to_send.append(p)
            except Exception:
                to_send.append(p)

        if not to_send:
            return

        for payment in to_send:
            days_overdue = (date.today() - payment.due_date).days
            message = "🔴 **MUDDATI O'TGAN TO'LOV!**\n\n"
            message += f"📝 {payment.description}\n"
            message += f"💰 {payment.amount:,.0f} so'm\n"
            message += f"📅 Sana: {payment.due_date.strftime('%d.%m.%Y')}\n"
            message += f"⏰ {days_overdue} kun o'tdi\n"

            try:
                await bot.send_message(
                    user_id,
                    message,
                    parse_mode="Markdown",
                    reply_markup=get_payment_reminder_actions_keyboard(payment.id),
                )
            except Exception as e:
                print(f"Error sending overdue reminder to {user_id}: {e}")

        await run_db(PaymentService.mark_overdue_sent, [p.id for p in to_send])
