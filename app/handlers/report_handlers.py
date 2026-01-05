from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from datetime import date, timedelta
import os

from states import ReportStates
from keyboards import *
from services.report_service import ReportService
from utils.helpers import parse_date, format_report_message
from database import get_db

router = Router()

@router.callback_query(F.data == "today_report")
async def today_report(callback: CallbackQuery):
    await callback.answer()
    db = next(get_db())
    report_data = ReportService.generate_daily_report(db, callback.from_user.id)
    
    message = format_report_message(report_data)
    
    # Generate Excel file
    filename = await ReportService.create_excel_report(
        report_data,
        f"reports/today_{callback.from_user.id}_{date.today().strftime('%Y%m%d')}.xlsx"
    )
    
    await callback.message.answer(message, parse_mode="Markdown")
    
    # Send Excel file
    document = FSInputFile(filename)
    await callback.message.answer_document(
        document=document,
        caption="📎 Yuqoridagi hisobotning Excel fayli"
    )
    
    # Clean up
    try:
        os.remove(filename)
    except:
        pass

@router.callback_query(F.data == "yesterday_report")
async def yesterday_report(callback: CallbackQuery):
    await callback.answer()
    db = next(get_db())
    yesterday = date.today() - timedelta(days=1)
    report_data = ReportService.generate_daily_report(db, callback.from_user.id, yesterday)
    
    message = format_report_message(report_data)
    
    # Generate Excel file
    filename = await ReportService.create_excel_report(
        report_data,
        f"reports/yesterday_{callback.from_user.id}_{yesterday.strftime('%Y%m%d')}.xlsx"
    )
    
    await callback.message.answer(message, parse_mode="Markdown")
    
    # Send Excel file
    document = FSInputFile(filename)
    await callback.message.answer_document(
        document=document,
        caption="📎 Yuqoridagi hisobotning Excel fayli"
    )
    
    # Clean up
    try:
        os.remove(filename)
    except:
        pass

@router.callback_query(F.data == "weekly_report")
async def weekly_report(callback: CallbackQuery):
    await callback.answer()
    db = next(get_db())
    report_data = ReportService.generate_weekly_report(db, callback.from_user.id)
    
    message = format_report_message(report_data)
    
    # Generate Excel file
    filename = await ReportService.create_excel_report(
        report_data,
        f"reports/weekly_{callback.from_user.id}_{date.today().strftime('%Y%m%d')}.xlsx"
    )
    
    await callback.message.answer(message, parse_mode="Markdown")
    
    # Send Excel file
    document = FSInputFile(filename)
    await callback.message.answer_document(
        document=document,
        caption="📎 Yuqoridagi hisobotning Excel fayli"
    )
    
    # Clean up
    try:
        os.remove(filename)
    except:
        pass

@router.callback_query(F.data == "monthly_report")
async def monthly_report(callback: CallbackQuery):
    await callback.answer()
    db = next(get_db())
    report_data = ReportService.generate_monthly_report(db, callback.from_user.id)
    
    message = format_report_message(report_data)
    
    # Generate Excel file
    filename = await ReportService.create_excel_report(
        report_data,
        f"reports/monthly_{callback.from_user.id}_{date.today().strftime('%Y%m%d')}.xlsx"
    )
    
    await callback.message.answer(message, parse_mode="Markdown")
    
    # Send Excel file
    document = FSInputFile(filename)
    await callback.message.answer_document(
        document=document,
        caption="📎 Yuqoridagi hisobotning Excel fayli"
    )
    
    # Clean up
    try:
        os.remove(filename)
    except:
        pass

@router.callback_query(F.data == "yearly_report")
async def yearly_report(callback: CallbackQuery):
    await callback.answer()
    db = next(get_db())
    report_data = ReportService.generate_yearly_report(db, callback.from_user.id)
    
    message = format_report_message(report_data)
    
    # Add monthly breakdown to message
    if report_data.get("monthly_totals"):
        message += "\n\n📈 **Oylik hisobot:**\n"
        monthly_totals = report_data.get("monthly_totals", {})
        for month, data in monthly_totals.items():
            if isinstance(data, dict):
                # New format with income, expenses, and balance
                balance = data.get('balance', 0)
                if balance >= 0:
                    status = "✅"
                else:
                    status = "❌"
                month_name = date(2024, month, 1).strftime("%B")
                message += f"• {month_name}: {status} {abs(balance):,.0f} so'm\n"
            else:
                # Old format (backward compatibility)
                if data > 0:
                    month_name = date(2024, month, 1).strftime("%B")
                    message += f"• {month_name}: {data:,.0f} so'm\n"
    
    # Generate Excel file
    filename = await ReportService.create_excel_report(
        report_data,
        f"reports/yearly_{callback.from_user.id}_{date.today().strftime('%Y%m%d')}.xlsx"
    )
    
    await callback.message.answer(message, parse_mode="Markdown")
    
    # Send Excel file
    document = FSInputFile(filename)
    await callback.message.answer_document(
        document=document,
        caption="📎 Yuqoridagi hisobotning Excel fayli"
    )
    
    # Clean up
    try:
        os.remove(filename)
    except:
        pass

@router.callback_query(F.data == "report_custom")
async def custom_report_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "Boshlang'ich sanani kiriting (DD.MM.YYYY):\n\nMasalan: 01.01.2026",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ReportStates.waiting_for_start_date)

@router.message(ReportStates.waiting_for_start_date)
async def process_start_date(message: Message, state: FSMContext):
    start_date = parse_date(message.text)
    
    if start_date is None:
        await message.answer(
            "❌ Noto'g'ri sana formati. Iltimos, DD.MM.YYYY formatida kiriting:\n\nMasalan: 01.01.2026",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(start_date=start_date)
    await message.answer(
        "Yakuniy sanani kiriting (DD.MM.YYYY):\n\nMasalan: 31.01.2026",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ReportStates.waiting_for_end_date)

@router.message(ReportStates.waiting_for_end_date)
async def process_end_date(message: Message, state: FSMContext):
    end_date = parse_date(message.text)
    
    if end_date is None:
        await message.answer(
            "❌ Noto'g'ri sana formati. Iltimos, DD.MM.YYYY formatida kiriting:\n\nMasalan: 31.01.2026",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    data = await state.get_data()
    start_date = data.get('start_date')
    
    if end_date < start_date:
        await message.answer(
            "❌ Yakuniy sana boshlang'ich sanadan oldin bo'lishi mumkin emas!",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    db = next(get_db())
    report_data = ReportService.generate_custom_report(
        db, message.from_user.id, start_date, end_date
    )
    
    message_text = format_report_message(report_data)
    
    # Generate Excel file
    filename = await ReportService.create_excel_report(
        report_data,
        f"reports/custom_{message.from_user.id}_{date.today().strftime('%Y%m%d')}.xlsx"
    )
    
    await message.answer(message_text, parse_mode="Markdown")
    
    # Send Excel file
    document = FSInputFile(filename)
    await message.answer_document(
        document=document,
        caption="📎 Yuqoridagi hisobotning Excel fayli"
    )
    
    # Clean up
    try:
        os.remove(filename)
    except:
        pass
    
    await state.clear()