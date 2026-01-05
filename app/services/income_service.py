from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
from typing import List, Optional
from models import Income


class IncomeService:
    @staticmethod
    def add_income(db: Session, user_id: int, amount: float, description: str, category: str = "Kirim", income_date: date = None) -> Income:
        if income_date is None:
            income_date = date.today()
            
        income = Income(
            user_id=user_id,
            amount=amount,
            description=description,
            category=category,
            date=income_date
        )
        
        db.add(income)
        db.commit()
        db.refresh(income)
        return income
    
    @staticmethod
    def get_total_income(db: Session, user_id: int, start_date: date = None, end_date: date = None) -> float:
        query = db.query(Income).filter(Income.user_id == user_id)
        
        if start_date:
            query = query.filter(Income.date >= start_date)
        if end_date:
            query = query.filter(Income.date <= end_date)
            
        incomes = query.all()
        return sum(income.amount for income in incomes)
    
    @staticmethod
    def get_monthly_income(db: Session, user_id: int, year: int = None, month: int = None) -> dict:
        if year is None:
            year = date.today().year
        if month is None:
            month = date.today().month
            
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
            
        incomes = db.query(Income).filter(
            Income.user_id == user_id,
            Income.date >= start_date,
            Income.date <= end_date
        ).order_by(Income.date.desc()).all()
        
        total_amount = sum(income.amount for income in incomes)
        
        return {
            'total_amount': total_amount,
            'income_count': len(incomes),
            'incomes': incomes,
            'month_name': start_date.strftime('%B %Y'),
            'start_date': start_date,
            'end_date': end_date
        }
    
    @staticmethod
    def get_recent_incomes(db: Session, user_id: int, limit: int = 10) -> List[Income]:
        return db.query(Income).filter(
            Income.user_id == user_id
        ).order_by(Income.date.desc()).limit(limit).all()
    
    @staticmethod
    def delete_income(db: Session, user_id: int, income_id: int) -> bool:
        income = db.query(Income).filter(
            Income.id == income_id,
            Income.user_id == user_id
        ).first()
        
        if income:
            db.delete(income)
            db.commit()
            return True
        return False
