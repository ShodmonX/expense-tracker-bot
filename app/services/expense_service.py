from sqlalchemy.orm import Session
from sqlalchemy import extract, func, and_, or_
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from models import Expense, ExpenseType, Payment
from utils.helpers import parse_date, format_date

class ExpenseService:
    @staticmethod
    def add_expense(
        db: Session,
        user_id: int,
        amount: float,
        category: str,
        description: str,
        expense_date: date,
        expense_type: ExpenseType = ExpenseType.ONCE,
        is_future: bool = False
    ) -> Expense:
        expense = Expense(
            user_id=user_id,
            amount=amount,
            category=category,
            description=description,
            date=expense_date,
            expense_type=expense_type,
            is_future=is_future
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense

    @staticmethod
    def get_today_expenses(db: Session, user_id: int) -> List[Expense]:
        today = date.today()
        return db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date == today,
            Expense.is_future == False
        ).all()

    @staticmethod
    def get_yesterday_expenses(db: Session, user_id: int) -> List[Expense]:
        yesterday = date.today() - timedelta(days=1)
        return db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date == yesterday,
            Expense.is_future == False
        ).all()

    @staticmethod
    def get_weekly_expenses(db: Session, user_id: int) -> List[Expense]:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        
        return db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date,
            Expense.date <= end_date,
            Expense.is_future == False
        ).all()

    @staticmethod
    def get_monthly_expenses(db: Session, user_id: int, year: int = None, month: int = None) -> List[Expense]:
        today = date.today()
        year = year or today.year
        month = month or today.month
        
        return db.query(Expense).filter(
            Expense.user_id == user_id,
            extract('year', Expense.date) == year,
            extract('month', Expense.date) == month,
            Expense.is_future == False
        ).all()

    @staticmethod
    def get_yearly_expenses(db: Session, user_id: int, year: int = None) -> List[Expense]:
        today = date.today()
        year = year or today.year
        
        return db.query(Expense).filter(
            Expense.user_id == user_id,
            extract('year', Expense.date) == year,
            Expense.is_future == False
        ).all()

    @staticmethod
    def get_expenses_by_period(db: Session, user_id: int, start_date: date, end_date: date) -> List[Expense]:
        return db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date,
            Expense.date <= end_date,
            Expense.is_future == False
        ).order_by(Expense.date).all()

    @staticmethod
    def get_future_expenses(db: Session, user_id: int) -> List[Expense]:
        today = date.today()
        return db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date > today,
            Expense.is_future == True
        ).order_by(Expense.date).all()

    @staticmethod
    def get_total_expenses(db: Session, user_id: int, expenses: List[Expense]) -> float:
        return sum(exp.amount for exp in expenses)

    @staticmethod
    def get_expenses_by_category(db: Session, user_id: int, start_date: date, end_date: date) -> Dict[str, float]:
        expenses = db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date,
            Expense.date <= end_date,
            Expense.is_future == False
        ).all()
        
        category_totals = {}
        for expense in expenses:
            category_totals[expense.category] = category_totals.get(expense.category, 0) + expense.amount
        
        return category_totals

    @staticmethod
    def get_last_expenses(db: Session, user_id: int, limit: int = 30) -> List[Expense]:
        return (
            db.query(Expense)
            .filter(
                Expense.user_id == user_id,
                Expense.is_future == False,
            )
            .order_by(Expense.date.desc(), Expense.id.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def delete_expense(db: Session, user_id: int, expense_id: int) -> bool:
        expense = db.query(Expense).filter(
            Expense.id == expense_id,
            Expense.user_id == user_id,
        ).first()
        if not expense:
            return False

        db.delete(expense)
        db.commit()
        return True