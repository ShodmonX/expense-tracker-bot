from sqlalchemy.orm import Session
from datetime import datetime, date
from config import config
import pytz

class ReminderService:
    @staticmethod
    async def check_and_send_reminders(db: Session, bot):
        """Check and send all types of reminders"""
        # Get all users
        from models import User
        users = db.query(User).all()
        
        for user in users:
            # Daily reminders (1 day before)
            await ReminderService.send_daily_reminders(db, user.telegram_id, bot)
            
            # Monthly reminders (last 3 days)
            await ReminderService.send_monthly_reminders(db, user.telegram_id, bot)
            
            # Yearly reminders (last 7 days)
            await ReminderService.send_yearly_reminders(db, user.telegram_id, bot)

    @staticmethod
    async def send_daily_reminders(db: Session, user_id: int, bot):
        """Send reminders for payments due tomorrow"""
        from services.payment_service import PaymentService
        from keyboards import get_payment_reminder_actions_keyboard
        
        payments = PaymentService.get_payments_due_tomorrow(db, user_id)
        
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
                    PaymentService.mark_reminder_sent(db, [payment.id])
                except Exception as e:
                    print(f"Error sending reminder to {user_id}: {e}")

    @staticmethod
    async def send_monthly_reminders(db: Session, user_id: int, bot):
        """Send reminders for monthly payments in last 3 days"""
        from services.payment_service import PaymentService
        from keyboards import get_payment_reminder_actions_keyboard
        
        payments = PaymentService.get_monthly_payments_due_in_3_days(db, user_id)
        
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
            
            # Mark as reminder sent
            payment_ids = [p.id for p in payments]
            PaymentService.mark_reminder_sent(db, payment_ids)

    @staticmethod
    async def send_yearly_reminders(db: Session, user_id: int, bot):
        """Send reminders for yearly payments in last 7 days"""
        from services.payment_service import PaymentService
        from keyboards import get_payment_reminder_actions_keyboard
        
        payments = PaymentService.get_yearly_payments_due_in_week(db, user_id)
        
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
            
            # Mark as reminder sent
            payment_ids = [p.id for p in payments]
            PaymentService.mark_reminder_sent(db, payment_ids)

    @staticmethod
    async def send_daily_summary(db: Session, user_id: int, bot):
        """Send daily expense summary at end of day"""
        from services.expense_service import ExpenseService
        
        today = date.today()
        expenses = ExpenseService.get_today_expenses(db, user_id)
        
        if expenses:
            total = ExpenseService.get_total_expenses(db, user_id, expenses)
            category_totals = ExpenseService.get_expenses_by_category(db, user_id, today, today)
            
            message = f"📊 **KUNLIK HISOBOT - {today.strftime('%d.%m.%Y')}**\n\n"
            message += f"📈 Jami xarajat: {total:,.0f} so'm\n"
            message += f"📝 Xarajatlar soni: {len(expenses)}\n\n"
            message += "📋 **Kategoriyalar bo'yicha:**\n"
            
            for category, amount in category_totals.items():
                percentage = (amount / total * 100) if total > 0 else 0
                message += f"• {category}: {amount:,.0f} so'm ({percentage:.1f}%)\n"
            
            message += f"\n⏰ Hisobot vaqti: {datetime.now(pytz.timezone(config.TIMEZONE)).strftime('%H:%M')}"
            
            try:
                await bot.send_message(user_id, message, parse_mode="Markdown")
            except Exception as e:
                print(f"Error sending daily summary to {user_id}: {e}")

    @staticmethod
    async def send_overdue_reminders(db: Session, user_id: int, bot):
        """Send reminders for overdue payments (due_date < today)."""
        from services.payment_service import PaymentService
        from keyboards import get_payment_reminder_actions_keyboard

        now_utc = datetime.utcnow()
        payments = PaymentService.get_overdue_payments(db, user_id)
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

        PaymentService.mark_overdue_sent(db, [p.id for p in to_send])
