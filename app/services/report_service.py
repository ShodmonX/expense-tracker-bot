from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List, Dict
from models import Expense
from utils.excel_generator import generate_excel_report
from services.expense_service import ExpenseService

class ReportService:
    @staticmethod
    def generate_daily_report(db: Session, user_id: int, report_date: date = None) -> Dict:
        if report_date is None:
            report_date = date.today()
        
        expenses = ExpenseService.get_expenses_by_period(
            db, user_id, report_date, report_date
        )
        
        total = ExpenseService.get_total_expenses(db, user_id, expenses)
        category_totals = ExpenseService.get_expenses_by_category(
            db, user_id, report_date, report_date
        )
        
        return {
            "period": f"Kunlik hisobot - {report_date.strftime('%d.%m.%Y')}",
            "expenses": expenses,
            "total": total,
            "category_totals": category_totals,
            "start_date": report_date,
            "end_date": report_date
        }

    @staticmethod
    def generate_weekly_report(db: Session, user_id: int) -> Dict:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        
        expenses = ExpenseService.get_expenses_by_period(db, user_id, start_date, end_date)
        total = ExpenseService.get_total_expenses(db, user_id, expenses)
        category_totals = ExpenseService.get_expenses_by_category(db, user_id, start_date, end_date)
        
        return {
            "period": f"Haftalik hisobot - {start_date.strftime('%d.%m.%Y')} dan {end_date.strftime('%d.%m.%Y')} gacha",
            "expenses": expenses,
            "total": total,
            "category_totals": category_totals,
            "start_date": start_date,
            "end_date": end_date
        }

    @staticmethod
    def generate_monthly_report(db: Session, user_id: int, year: int = None, month: int = None) -> Dict:
        today = date.today()
        year = year or today.year
        month = month or today.month
        
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        start_date = date(year, month, 1)
        
        expenses = ExpenseService.get_expenses_by_period(db, user_id, start_date, end_date)
        total = ExpenseService.get_total_expenses(db, user_id, expenses)
        category_totals = ExpenseService.get_expenses_by_category(db, user_id, start_date, end_date)
        
        return {
            "period": f"Oylik hisobot - {start_date.strftime('%B %Y')}",
            "expenses": expenses,
            "total": total,
            "category_totals": category_totals,
            "start_date": start_date,
            "end_date": end_date
        }

    @staticmethod
    def generate_yearly_report(db: Session, user_id: int, year: int = None) -> Dict:
        today = date.today()
        year = year or today.year
        
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        expenses = ExpenseService.get_expenses_by_period(db, user_id, start_date, end_date)
        total = ExpenseService.get_total_expenses(db, user_id, expenses)
        category_totals = ExpenseService.get_expenses_by_category(db, user_id, start_date, end_date)
        
        # Get monthly breakdown
        monthly_totals = {}
        for month in range(1, 13):
            month_expenses = ExpenseService.get_monthly_expenses(db, user_id, year, month)
            monthly_totals[month] = ExpenseService.get_total_expenses(db, user_id, month_expenses)
        
        return {
            "period": f"Yillik hisobot - {year}",
            "expenses": expenses,
            "total": total,
            "category_totals": category_totals,
            "monthly_totals": monthly_totals,
            "start_date": start_date,
            "end_date": end_date
        }

    @staticmethod
    def generate_custom_report(db: Session, user_id: int, start_date: date, end_date: date) -> Dict:
        expenses = ExpenseService.get_expenses_by_period(db, user_id, start_date, end_date)
        total = ExpenseService.get_total_expenses(db, user_id, expenses)
        category_totals = ExpenseService.get_expenses_by_category(db, user_id, start_date, end_date)
        
        return {
            "period": f"Hisobot - {start_date.strftime('%d.%m.%Y')} dan {end_date.strftime('%d.%m.%Y')} gacha",
            "expenses": expenses,
            "total": total,
            "category_totals": category_totals,
            "start_date": start_date,
            "end_date": end_date
        }

    @staticmethod
    async def create_excel_report(report_data: Dict, filename: str) -> str:
        return await generate_excel_report(report_data, filename)