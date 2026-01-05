from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List, Optional
import calendar
from models import Payment, PaymentFrequency

class PaymentService:
    @staticmethod
    def _add_months(dt: date, months: int) -> date:
        month_index = (dt.month - 1) + months
        year = dt.year + month_index // 12
        month = month_index % 12 + 1
        last_day = calendar.monthrange(year, month)[1]
        day = min(dt.day, last_day)
        return date(year, month, day)

    @staticmethod
    def _next_weekday(from_date: date, weekday: int) -> date:
        days_ahead = (weekday - from_date.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return from_date + timedelta(days=days_ahead)

    @staticmethod
    def _next_month_day(from_date: date, day_of_month: int) -> date:
        last_day_this_month = calendar.monthrange(from_date.year, from_date.month)[1]
        day_this_month = min(day_of_month, last_day_this_month)
        candidate = date(from_date.year, from_date.month, day_this_month)
        if candidate <= from_date:
            next_month = PaymentService._add_months(from_date.replace(day=1), 1)
            last_day_next_month = calendar.monthrange(next_month.year, next_month.month)[1]
            day_next_month = min(day_of_month, last_day_next_month)
            return date(next_month.year, next_month.month, day_next_month)
        return candidate

    @staticmethod
    def _get_next_due_date(payment: Payment, from_date: date | None = None) -> date:
        base = from_date or date.today()

        if payment.frequency == PaymentFrequency.WEEKLY:
            next_due = payment.due_date
            if next_due is None:
                if payment.weekday is None:
                    return base
                return PaymentService._next_weekday(base, payment.weekday)
 
            while next_due <= base:
                next_due = next_due + timedelta(days=7)
            return next_due

        if payment.frequency == PaymentFrequency.BIWEEKLY:
            next_due = payment.due_date
            if next_due is None:
                if payment.weekday is None:
                    return base
                # First occurrence: pick next selected weekday, then biweekly increments will preserve weekday
                next_due = PaymentService._next_weekday(base, payment.weekday)
 
            while next_due <= base:
                next_due = next_due + timedelta(days=14)
            return next_due

        if payment.frequency == PaymentFrequency.MONTHLY:
            if payment.day_of_month is None:
                return PaymentService._next_month_day(base, payment.due_date.day)
            return PaymentService._next_month_day(base, payment.day_of_month)

        if payment.frequency == PaymentFrequency.QUARTERLY:
            next_due = payment.due_date
            while next_due <= base:
                next_due = PaymentService._add_months(next_due, 3)
            return next_due

        if payment.frequency == PaymentFrequency.YEARLY:
            next_due = payment.due_date
            while next_due <= base:
                next_due = date(next_due.year + 1, next_due.month, min(next_due.day, calendar.monthrange(next_due.year + 1, next_due.month)[1]))
            return next_due

        return payment.due_date

    @staticmethod
    def normalize_recurring_payments(db: Session, user_id: int | None = None, advance_overdue: bool = False):
        today = date.today()
        query = db.query(Payment).filter(Payment.is_paid == False)
        if user_id is not None:
            query = query.filter(Payment.user_id == user_id)

        payments = query.filter(Payment.frequency != PaymentFrequency.ONCE).all()
        updated = False

        for payment in payments:
            if advance_overdue and payment.due_date < today:
                payment.due_date = PaymentService._get_next_due_date(payment, today)
                payment.reminder_sent = False
                updated = True

        if updated:
            db.commit()

    @staticmethod
    def add_payment(
        db: Session,
        user_id: int,
        amount: float,
        category: str,
        description: str,
        due_date: date,
        frequency: PaymentFrequency = PaymentFrequency.ONCE,
        weekday: int | None = None,
        day_of_month: int | None = None,
        occurrences_left: int | None = None,
        is_paid: bool = False
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            amount=amount,
            category=category,
            description=description,
            due_date=due_date,
            frequency=frequency,
            weekday=weekday,
            day_of_month=day_of_month,
            occurrences_left=occurrences_left,
            is_paid=is_paid
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def pay_payment_and_record_expense(
        db: Session,
        payment_id: int,
        user_id: int,
        paid_amount: float | None = None,
    ) -> Optional[Payment]:
        """Mark payment as paid (for ONCE) or roll forward (for recurring), and record as expense.

        If paid_amount is provided, record expense with that amount; otherwise use planned payment.amount.
        """
        from services.expense_service import ExpenseService
        from models import ExpenseType

        payment = db.query(Payment).filter(
            Payment.id == payment_id,
            Payment.user_id == user_id,
            Payment.is_paid == False,
        ).first()
        if not payment:
            return None

        # Record as expense on the day user marks it as paid
        ExpenseService.add_expense(
            db=db,
            user_id=user_id,
            amount=paid_amount if paid_amount is not None else payment.amount,
            category=payment.category or "To'lov",
            description=payment.description or "",
            expense_date=date.today(),
            expense_type=ExpenseType.ONCE,
            is_future=False,
        )

        # Update payment state
        payment.payment_date = date.today()
        payment.reminder_sent = True
        payment.overdue_last_sent_at = None

        if payment.frequency == PaymentFrequency.ONCE:
            payment.is_paid = True
        else:
            if payment.occurrences_left is not None:
                try:
                    payment.occurrences_left = int(payment.occurrences_left) - 1
                except Exception:
                    payment.occurrences_left = payment.occurrences_left

                if payment.occurrences_left is not None and payment.occurrences_left <= 0:
                    db.delete(payment)
                    db.commit()
                    return payment

            # Keep recurring payment active; advance due date to next occurrence
            payment.due_date = PaymentService._get_next_due_date(payment, payment.due_date)
            payment.reminder_sent = False

        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def skip_payment_occurrence(db: Session, payment_id: int, user_id: int) -> Optional[Payment]:
        """Skip this period. For ONCE: mark skipped. For recurring: roll due_date forward."""
        payment = db.query(Payment).filter(
            Payment.id == payment_id,
            Payment.user_id == user_id,
            Payment.is_paid == False,
        ).first()
        if not payment:
            return None

        payment.overdue_last_sent_at = None

        if payment.frequency == PaymentFrequency.ONCE:
            payment.is_skipped = True
            payment.reminder_sent = True
        else:
            payment.due_date = PaymentService._get_next_due_date(payment, payment.due_date)
            payment.reminder_sent = False

        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def get_overdue_payments(db: Session, user_id: int) -> List[Payment]:
        today = date.today()
        return (
            db.query(Payment)
            .filter(
                Payment.user_id == user_id,
                Payment.is_paid == False,
                Payment.is_skipped == False,
                Payment.due_date < today,
            )
            .order_by(Payment.due_date.asc(), Payment.id.asc())
            .all()
        )

    @staticmethod
    def mark_overdue_sent(db: Session, payment_ids: List[int]):
        now = datetime.utcnow()
        db.query(Payment).filter(Payment.id.in_(payment_ids)).update(
            {"overdue_last_sent_at": now},
            synchronize_session=False,
        )
        db.commit()

    @staticmethod
    def mark_as_paid(db: Session, payment_id: int, user_id: int) -> Optional[Payment]:
        payment = db.query(Payment).filter(
            Payment.id == payment_id,
            Payment.user_id == user_id
        ).first()

        if payment:
            payment.is_paid = True
            payment.payment_date = date.today()
            db.commit()
            db.refresh(payment)

        return payment

    @staticmethod
    def get_upcoming_payments(db: Session, user_id: int, days_ahead: int = 30) -> List[Payment]:
        PaymentService.normalize_recurring_payments(db, user_id=user_id)
        today = date.today()
        end_date = today + timedelta(days=days_ahead)

        return db.query(Payment).filter(
            Payment.user_id == user_id,
            Payment.due_date >= today,
            Payment.due_date <= end_date,
            Payment.is_paid == False,
            Payment.is_skipped == False,
        ).order_by(Payment.due_date).all()

    @staticmethod
    def get_upcoming_payments_this_month(db: Session, user_id: int) -> List[Payment]:
        PaymentService.normalize_recurring_payments(db, user_id=user_id)
        today = date.today()
        
        # Get the last day of the current month
        if today.month == 12:
            last_day_of_month = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day_of_month = date(today.year, today.month + 1, 1) - timedelta(days=1)

        return db.query(Payment).filter(
            Payment.user_id == user_id,
            Payment.due_date >= today,
            Payment.due_date <= last_day_of_month,
            Payment.is_paid == False,
            Payment.is_skipped == False,
        ).order_by(Payment.due_date).all()

    @staticmethod
    def get_monthly_payment_summary(db: Session, user_id: int) -> dict:
        """
        Calculate minimal monthly payments for the current month
        Returns dict with total_amount, payment_count, and payments list
        """
        PaymentService.normalize_recurring_payments(db, user_id=user_id)
        today = date.today()
        
        # Get the first and last day of current month
        first_day_of_month = today.replace(day=1)
        if today.month == 12:
            last_day_of_month = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day_of_month = date(today.year, today.month + 1, 1) - timedelta(days=1)

        payments = db.query(Payment).filter(
            Payment.user_id == user_id,
            Payment.due_date >= first_day_of_month,
            Payment.due_date <= last_day_of_month,
            Payment.is_paid == False,
            Payment.is_skipped == False,
        ).order_by(Payment.due_date).all()

        total_amount = sum(p.amount for p in payments)
        
        return {
            'total_amount': total_amount,
            'payment_count': len(payments),
            'payments': payments,
            'month_name': today.strftime('%B %Y'),
            'first_day': first_day_of_month,
            'last_day': last_day_of_month
        }

    @staticmethod
    def get_payments_due_tomorrow(db: Session, user_id: int) -> List[Payment]:
        PaymentService.normalize_recurring_payments(db, user_id=user_id)
        tomorrow = date.today() + timedelta(days=1)

        return db.query(Payment).filter(
            Payment.user_id == user_id,
            Payment.due_date == tomorrow,
            Payment.is_paid == False,
            Payment.is_skipped == False,
            Payment.reminder_sent == False
        ).all()

    @staticmethod
    def get_monthly_payments_due_in_3_days(db: Session, user_id: int) -> List[Payment]:
        PaymentService.normalize_recurring_payments(db, user_id=user_id)
        today = date.today()
        for i in range(1, 4):  # Check next 3 days
            check_date = today + timedelta(days=i)
            payments = db.query(Payment).filter(
                Payment.user_id == user_id,
                Payment.due_date == check_date,
                Payment.frequency == PaymentFrequency.MONTHLY,
                Payment.is_paid == False,
                Payment.is_skipped == False,
                Payment.reminder_sent == False
            ).all()
            if payments:
                return payments
        return []

    @staticmethod
    def get_yearly_payments_due_in_week(db: Session, user_id: int) -> List[Payment]:
        PaymentService.normalize_recurring_payments(db, user_id=user_id)
        today = date.today()
        payments_due = []

        for i in range(1, 8):  # Check next 7 days
            check_date = today + timedelta(days=i)
            payments = db.query(Payment).filter(
                Payment.user_id == user_id,
                Payment.due_date == check_date,
                Payment.frequency == PaymentFrequency.YEARLY,
                Payment.is_paid == False,
                Payment.is_skipped == False,
                Payment.reminder_sent == False
            ).all()
            payments_due.extend(payments)
        
        return payments_due

    @staticmethod
    def mark_reminder_sent(db: Session, payment_ids: List[int]):
        db.query(Payment).filter(Payment.id.in_(payment_ids)).update(
            {"reminder_sent": True},
            synchronize_session=False
        )
        db.commit()

    @staticmethod
    def get_future_payments(db: Session, user_id: int, limit: int = 30) -> List[Payment]:
        PaymentService.normalize_recurring_payments(db, user_id=user_id)
        today = date.today()
        return (
            db.query(Payment)
            .filter(
                Payment.user_id == user_id,
                Payment.due_date >= today,
                Payment.is_paid == False,
                Payment.is_skipped == False,
            )
            .order_by(Payment.due_date.asc(), Payment.id.asc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def delete_payment(db: Session, user_id: int, payment_id: int) -> bool:
        payment = db.query(Payment).filter(
            Payment.id == payment_id,
            Payment.user_id == user_id,
        ).first()
        if not payment:
            return False

        db.delete(payment)
        db.commit()
        return True