from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List, Dict
from models import Expense, Income
from utils.excel_generator import generate_excel_report
from services.expense_service import ExpenseService
from services.income_service import IncomeService

class ReportService:
    @staticmethod
    def generate_daily_report(db: Session, user_id: int, report_date: date = None) -> Dict:
        if report_date is None:
            report_date = date.today()
        
        # Get expenses
        expenses = ExpenseService.get_expenses_by_period(
            db, user_id, report_date, report_date
        )
        total_expenses = ExpenseService.get_total_expenses(db, user_id, expenses)
        category_totals = ExpenseService.get_expenses_by_category(
            db, user_id, report_date, report_date
        )
        
        # Get income
        income_data = IncomeService.get_monthly_income(
            db, user_id, report_date.year, report_date.month
        )
        daily_incomes = [inc for inc in income_data['incomes'] if inc.date == report_date]
        total_income = sum(inc.amount for inc in daily_incomes)
        
        return {
            "period": f"Kunlik hisobot - {report_date.strftime('%d.%m.%Y')}",
            "expenses": expenses,
            "total_expenses": total_expenses,
            "category_totals": category_totals,
            "incomes": daily_incomes,
            "total_income": total_income,
            "balance": total_income - total_expenses,
            "start_date": report_date,
            "end_date": report_date
        }

    @staticmethod
    def generate_weekly_report(db: Session, user_id: int) -> Dict:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        
        # Get expenses
        expenses = ExpenseService.get_expenses_by_period(db, user_id, start_date, end_date)
        total_expenses = ExpenseService.get_total_expenses(db, user_id, expenses)
        category_totals = ExpenseService.get_expenses_by_category(db, user_id, start_date, end_date)
        
        # Get income for the week
        total_income = 0
        weekly_incomes = []
        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)
            income_data = IncomeService.get_monthly_income(
                db, user_id, current_date.year, current_date.month
            )
            daily_incomes = [inc for inc in income_data['incomes'] if inc.date == current_date]
            total_income += sum(inc.amount for inc in daily_incomes)
            weekly_incomes.extend(daily_incomes)
        
        return {
            "period": f"Haftalik hisobot - {start_date.strftime('%d.%m.%Y')} dan {end_date.strftime('%d.%m.%Y')} gacha",
            "expenses": expenses,
            "total_expenses": total_expenses,
            "category_totals": category_totals,
            "incomes": weekly_incomes,
            "total_income": total_income,
            "balance": total_income - total_expenses,
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
        
        # Get expenses
        expenses = ExpenseService.get_expenses_by_period(db, user_id, start_date, end_date)
        total_expenses = ExpenseService.get_total_expenses(db, user_id, expenses)
        category_totals = ExpenseService.get_expenses_by_category(db, user_id, start_date, end_date)
        
        # Get income
        income_data = IncomeService.get_monthly_income(db, user_id, year, month)
        total_income = income_data['total_amount']
        incomes = income_data['incomes']
        
        return {
            "period": f"Oylik hisobot - {start_date.strftime('%B %Y')}",
            "expenses": expenses,
            "total_expenses": total_expenses,
            "category_totals": category_totals,
            "incomes": incomes,
            "total_income": total_income,
            "balance": total_income - total_expenses,
            "start_date": start_date,
            "end_date": end_date
        }

    @staticmethod
    def generate_yearly_report(db: Session, user_id: int, year: int = None) -> Dict:
        today = date.today()
        year = year or today.year
        
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        # Get expenses
        expenses = ExpenseService.get_expenses_by_period(db, user_id, start_date, end_date)
        total_expenses = ExpenseService.get_total_expenses(db, user_id, expenses)
        category_totals = ExpenseService.get_expenses_by_category(db, user_id, start_date, end_date)
        
        # Get income
        total_income = 0
        yearly_incomes = []
        for month in range(1, 13):
            income_data = IncomeService.get_monthly_income(db, user_id, year, month)
            total_income += income_data['total_amount']
            yearly_incomes.extend(income_data['incomes'])
        
        # Get monthly breakdown
        monthly_totals = {}
        for month in range(1, 13):
            month_expenses = ExpenseService.get_monthly_expenses(db, user_id, year, month)
            month_income_data = IncomeService.get_monthly_income(db, user_id, year, month)
            month_total_expenses = ExpenseService.get_total_expenses(db, user_id, month_expenses)
            monthly_totals[month] = {
                'expenses': month_total_expenses,
                'income': month_income_data['total_amount'],
                'balance': month_income_data['total_amount'] - month_total_expenses
            }
        
        return {
            "period": f"Yillik hisobot - {year}",
            "expenses": expenses,
            "total_expenses": total_expenses,
            "category_totals": category_totals,
            "incomes": yearly_incomes,
            "total_income": total_income,
            "balance": total_income - total_expenses,
            "monthly_totals": monthly_totals,
            "start_date": start_date,
            "end_date": end_date
        }

    @staticmethod
    def generate_custom_report(db: Session, user_id: int, start_date: date, end_date: date) -> Dict:
        # Get expenses
        expenses = ExpenseService.get_expenses_by_period(db, user_id, start_date, end_date)
        total_expenses = ExpenseService.get_total_expenses(db, user_id, expenses)
        category_totals = ExpenseService.get_expenses_by_category(db, user_id, start_date, end_date)
        
        # Get income for custom period
        total_income = 0
        custom_incomes = []
        current_date = start_date
        while current_date <= end_date:
            income_data = IncomeService.get_monthly_income(
                db, user_id, current_date.year, current_date.month
            )
            daily_incomes = [inc for inc in income_data['incomes'] if start_date <= inc.date <= end_date]
            total_income += sum(inc.amount for inc in daily_incomes)
            custom_incomes.extend(daily_incomes)
            current_date = current_date + timedelta(days=1)
        
        return {
            "period": f"Hisobot - {start_date.strftime('%d.%m.%Y')} dan {end_date.strftime('%d.%m.%Y')} gacha",
            "expenses": expenses,
            "total_expenses": total_expenses,
            "category_totals": category_totals,
            "incomes": custom_incomes,
            "total_income": total_income,
            "balance": total_income - total_expenses,
            "start_date": start_date,
            "end_date": end_date
        }

    @staticmethod
    async def create_excel_report(report_data: Dict, filename: str) -> str:
        return await generate_excel_report(report_data, filename)