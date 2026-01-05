from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List, Optional, Dict
from models import Income, Expense
from services.income_service import IncomeService
from services.expense_service import ExpenseService


class BalanceService:
    @staticmethod
    def get_monthly_balance_summary(db: Session, user_id: int, year: int = None, month: int = None) -> Dict:
        """
        Calculate comprehensive balance summary for a specific month
        """
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month
            
        # Get month boundaries
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get income data
        income_data = IncomeService.get_monthly_income(db, user_id, year, month)
        total_income = income_data['total_amount']
        income_count = income_data['income_count']
        incomes = income_data['incomes']
        
        # Get expense data
        expenses = db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date,
            Expense.date <= end_date
        ).all()
        
        total_expenses = sum(exp.amount for exp in expenses)
        expense_count = len(expenses)
        
        # Calculate balance
        available_balance = total_income - total_expenses
        
        # Get previous month balance (carry-over)
        if month == 1:
            prev_year = year - 1
            prev_month = 12
        else:
            prev_year = year
            prev_month = month - 1
            
        try:
            prev_month_summary = BalanceService.get_monthly_balance_summary(
                db, user_id, prev_year, prev_month
            )
            carry_over = prev_month_summary['available_balance']
        except:
            carry_over = 0.0
        
        return {
            'year': year,
            'month': month,
            'month_name': start_date.strftime('%B %Y'),
            'start_date': start_date,
            'end_date': end_date,
            'total_income': total_income,
            'income_count': income_count,
            'incomes': incomes,
            'total_expenses': total_expenses,
            'expense_count': expense_count,
            'expenses': expenses,
            'available_balance': available_balance,
            'carry_over': carry_over,
            'next_month_starting_balance': max(0, available_balance)
        }
    
    @staticmethod
    def get_current_balance(db: Session, user_id: int) -> Dict:
        """
        Get current month balance summary
        """
        return BalanceService.get_monthly_balance_summary(db, user_id)
    
    @staticmethod
    def get_yearly_balance_summary(db: Session, user_id: int, year: int = None) -> Dict:
        """
        Get yearly balance summary with month-by-month breakdown
        """
        if year is None:
            year = date.today().year
            
        monthly_summaries = []
        total_yearly_income = 0
        total_yearly_expenses = 0
        
        for month in range(1, 13):
            try:
                monthly_summary = BalanceService.get_monthly_balance_summary(
                    db, user_id, year, month
                )
                monthly_summaries.append(monthly_summary)
                total_yearly_income += monthly_summary['total_income']
                total_yearly_expenses += monthly_summary['total_expenses']
            except:
                continue
        
        return {
            'year': year,
            'monthly_summaries': monthly_summaries,
            'total_yearly_income': total_yearly_income,
            'total_yearly_expenses': total_yearly_expenses,
            'total_yearly_balance': total_yearly_income - total_yearly_expenses
        }
