from datetime import datetime, date, timedelta
from typing import Optional, Tuple
import re

def parse_date(date_str: str) -> Optional[date]:
    """Parse date from various formats"""
    formats = [
        "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y",
        "%Y.%m.%d", "%Y/%m/%d", "%Y-%m-%d",
        "%d.%m.%y", "%d/%m/%y", "%d-%m-%y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    # Try relative dates
    date_str = date_str.lower().strip()
    today = date.today()
    
    if date_str == "bugun" or date_str == "today":
        return today
    elif date_str == "ertaga" or date_str == "tomorrow":
        return today + timedelta(days=1)
    elif date_str == "kecha" or date_str == "yesterday":
        return today - timedelta(days=1)
    elif date_str.startswith("+"):
        try:
            days = int(date_str[1:])
            return today + timedelta(days=days)
        except:
            pass
    
    return None

def format_date(dt: date, format_str: str = "%d.%m.%Y") -> str:
    """Format date to string"""
    return dt.strftime(format_str)

def format_amount(amount: float) -> str:
    """Format amount with thousand separators"""
    return f"{amount:,.0f}".replace(",", " ")

def parse_amount(amount_str: str) -> Optional[float]:
    """Parse amount from string, remove spaces and commas"""
    try:
        # Remove spaces, commas, and non-digit characters except dot
        cleaned = re.sub(r'[^\d.]', '', amount_str)
        return float(cleaned)
    except:
        return None

def get_week_range(date_obj: date = None) -> Tuple[date, date]:
    """Get start and end dates of week"""
    if date_obj is None:
        date_obj = date.today()
    
    start = date_obj - timedelta(days=date_obj.weekday())
    end = start + timedelta(days=6)
    return start, end

def get_month_range(year: int = None, month: int = None) -> Tuple[date, date]:
    """Get start and end dates of month"""
    today = date.today()
    year = year or today.year
    month = month or today.month
    
    if month == 12:
        start = date(year, month, 1)
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        start = date(year, month, 1)
        end = date(year, month + 1, 1) - timedelta(days=1)
    
    return start, end

def format_report_message(report_data: dict) -> str:
    """Format report data into readable message"""
    period = report_data.get("period", "")
    total_expenses = report_data.get("total_expenses", 0)
    total_income = report_data.get("total_income", 0)
    balance = report_data.get("balance", 0)
    category_totals = report_data.get("category_totals", {})
    
    message = f"📊 **{period}**\n\n"
    
    # Income section
    message += f"💵 **Jami kirim:** {format_amount(total_income)} so'm\n"
    message += f"📝 **Kirimlar soni:** {len(report_data.get('incomes', []))}\n\n"
    
    # Expense section
    message += f"💸 **Jami harajat:** {format_amount(total_expenses)} so'm\n"
    message += f"📝 **Harajatlar soni:** {len(report_data.get('expenses', []))}\n\n"
    
    # Balance section
    if balance >= 0:
        message += f"✅ **Balans:** {format_amount(balance)} so'm\n\n"
    else:
        message += f"❌ **Kamomad:** {format_amount(abs(balance))} so'm\n\n"
    
    # Category breakdown (only for expenses)
    if category_totals:
        message += "📋 **Harajatlar kategoriyalar bo'yicha:**\n"
        for category, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
            message += f"• {category}: {format_amount(amount)} so'm ({percentage:.1f}%)\n"
    
    return message