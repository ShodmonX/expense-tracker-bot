from aiogram import Router, F
from aiogram.types import InaccessibleMessage, Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from datetime import date, timedelta
import os

from states import ReportStates
from keyboards import *
from services.report_service import ReportService
from services.settings_service import SettingsService
from utils.helpers import parse_date, format_report_message
from database import run_db

router = Router()


def _normalize_report_format(value: str | None) -> str:
    return "pdf" if (value or "").strip().lower() == "pdf" else "xlsx"


async def _get_report_format(user_id: int) -> str:
    settings = await run_db(SettingsService.get_or_create, user_id)
    return _normalize_report_format(settings.report_format)


async def _send_report_document(target_message: Message, report_data: dict, user_id: int, file_stem: str):
    report_format = await _get_report_format(user_id)
    if report_format == "pdf":
        try:
            filename = await ReportService.create_pdf_report(report_data, f"{file_stem}.pdf")
            caption = "📎 Yuqoridagi hisobotning PDF fayli"
        except Exception:
            filename = await ReportService.create_excel_report(report_data, f"{file_stem}.xlsx")
            caption = "📎 PDF tayyorlab bo'lmadi, Excel fayli yuborildi"
    else:
        filename = await ReportService.create_excel_report(report_data, f"{file_stem}.xlsx")
        caption = "📎 Yuqoridagi hisobotning Excel fayli"

    document = FSInputFile(filename)
    await target_message.answer_document(document=document, caption=caption)

    try:
        os.remove(filename)
    except OSError:
        pass


async def _reply_with_report(
    target_message: Message,
    report_data: dict,
    user_id: int,
    file_stem: str,
    message_text: str | None = None,
):
    text = message_text or format_report_message(report_data)
    await target_message.answer(text, parse_mode="Markdown")
    await _send_report_document(target_message, report_data, user_id, file_stem)

@router.message(F.text == "📊 Bugun")
async def today_report_message(message: Message):
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return
    report_data = await run_db(ReportService.generate_daily_report, message.from_user.id)
    await _reply_with_report(
        message,
        report_data,
        message.from_user.id,
        f"reports/today_{message.from_user.id}_{date.today().strftime('%Y%m%d')}",
    )

@router.callback_query(F.data == "today_report")
async def today_report(callback: CallbackQuery):
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return
    await callback.answer()
    report_data = await run_db(ReportService.generate_daily_report, callback.from_user.id)
    await _reply_with_report(
        callback.message,
        report_data,
        callback.from_user.id,
        f"reports/today_{callback.from_user.id}_{date.today().strftime('%Y%m%d')}",
    )


@router.callback_query(F.data == "report_today")
async def today_report_alias(callback: CallbackQuery):
    await today_report(callback)

@router.message(F.text == "📈 Kecha")
async def yesterday_report_message(message: Message):
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return
    yesterday = date.today() - timedelta(days=1)
    report_data = await run_db(ReportService.generate_daily_report, message.from_user.id, yesterday)
    await _reply_with_report(
        message,
        report_data,
        message.from_user.id,
        f"reports/yesterday_{message.from_user.id}_{yesterday.strftime('%Y%m%d')}",
    )

@router.callback_query(F.data == "yesterday_report")
async def yesterday_report(callback: CallbackQuery):
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return
    await callback.answer()
    yesterday = date.today() - timedelta(days=1)
    report_data = await run_db(ReportService.generate_daily_report, callback.from_user.id, yesterday)
    await _reply_with_report(
        callback.message,
        report_data,
        callback.from_user.id,
        f"reports/yesterday_{callback.from_user.id}_{yesterday.strftime('%Y%m%d')}",
    )


@router.callback_query(F.data == "report_yesterday")
async def yesterday_report_alias(callback: CallbackQuery):
    await yesterday_report(callback)


@router.message(F.text == "📅 Haftalik")
async def weekly_report_message(message: Message):
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return
    report_data = await run_db(ReportService.generate_weekly_report, message.from_user.id)
    await _reply_with_report(
        message,
        report_data,
        message.from_user.id,
        f"reports/weekly_{message.from_user.id}_{date.today().strftime('%Y%m%d')}",
    )

@router.callback_query(F.data == "weekly_report")
async def weekly_report(callback: CallbackQuery):
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return
    await callback.answer()
    report_data = await run_db(ReportService.generate_weekly_report, callback.from_user.id)
    await _reply_with_report(
        callback.message,
        report_data,
        callback.from_user.id,
        f"reports/weekly_{callback.from_user.id}_{date.today().strftime('%Y%m%d')}",
    )


@router.callback_query(F.data == "report_week")
async def weekly_report_alias(callback: CallbackQuery):
    await weekly_report(callback)


@router.message(F.text == "📆 Oylik")
async def monthly_report_message(message: Message):
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return
    report_data = await run_db(ReportService.generate_monthly_report, message.from_user.id)
    await _reply_with_report(
        message,
        report_data,
        message.from_user.id,
        f"reports/monthly_{message.from_user.id}_{date.today().strftime('%Y%m%d')}",
    )

@router.callback_query(F.data == "monthly_report")
async def monthly_report(callback: CallbackQuery):
    if callback.from_user is None:
        await callback.answer("❌ Foydalanuvchi ma'lumotlari topilmadi.", show_alert=True)
        return
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return
    await callback.answer()
    report_data = await run_db(ReportService.generate_monthly_report, callback.from_user.id)
    await _reply_with_report(
        callback.message,
        report_data,
        callback.from_user.id,
        f"reports/monthly_{callback.from_user.id}_{date.today().strftime('%Y%m%d')}",
    )


@router.callback_query(F.data == "report_month")
async def monthly_report_alias(callback: CallbackQuery):
    await monthly_report(callback)


@router.message(F.text == "🎯 Yillik")
async def yearly_report_message(message: Message):
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return
    report_data = await run_db(ReportService.generate_yearly_report, message.from_user.id)
    
    message_text = format_report_message(report_data)
    
    # Add monthly breakdown to message
    if report_data.get("monthly_totals"):
        message_text += "\n\n📈 **Oylik hisobot:**\n"
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
                message_text += f"• {month_name}: {status} {abs(balance):,.0f} so'm\n"
            else:
                # Old format (just total)
                message_text += f"• {date(2024, month, 1).strftime('%B')}: {data:,.0f} so'm\n"
    
    await _reply_with_report(
        message,
        report_data,
        message.from_user.id,
        f"reports/yearly_{message.from_user.id}_{date.today().strftime('%Y%m%d')}",
        message_text=message_text,
    )

@router.callback_query(F.data == "yearly_report")
async def yearly_report(callback: CallbackQuery):
    if callback.from_user is None:
        await callback.answer("❌ Foydalanuvchi ma'lumotlari topilmadi.", show_alert=True)
        return
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return
    await callback.answer()
    report_data = await run_db(ReportService.generate_yearly_report, callback.from_user.id)
    
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
    
    await _reply_with_report(
        callback.message,
        report_data,
        callback.from_user.id,
        f"reports/yearly_{callback.from_user.id}_{date.today().strftime('%Y%m%d')}",
        message_text=message,
    )


@router.callback_query(F.data == "report_year")
async def yearly_report_alias(callback: CallbackQuery):
    await yearly_report(callback)


@router.message(F.text == "📊 Ixtiyoriy")
async def custom_report_start_message(message: Message, state: FSMContext):
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return
    await message.answer(
        "Boshlang'ich sanani kiriting (DD.MM.YYYY):\n\nMasalan: 01.01.2026",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ReportStates.waiting_for_start_date)

@router.callback_query(F.data == "report_custom")
async def custom_report_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user is None:
        await callback.answer("❌ Foydalanuvchi ma'lumotlari topilmadi.", show_alert=True)
        return
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer(
        "Boshlang'ich sanani kiriting (DD.MM.YYYY):\n\nMasalan: 01.01.2026",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ReportStates.waiting_for_start_date)

@router.message(ReportStates.waiting_for_start_date)
async def process_start_date(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("❌ Xabar matni topilmadi.")
        return
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
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return
    if message.text is None:
        await message.answer("❌ Xabar matni topilmadi.")
        return
    end_date = parse_date(message.text)
    
    if end_date is None:
        await message.answer(
            "❌ Noto'g'ri sana formati. Iltimos, DD.MM.YYYY formatida kiriting:\n\nMasalan: 31.01.2026",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    data = await state.get_data()
    start_date = data.get('start_date')
    if start_date is None:
        await message.answer("❌ Boshlang'ich sana aniqlanmadi.", reply_markup=get_cancel_keyboard())
        return
    
    if end_date < start_date:
        await message.answer(
            "❌ Yakuniy sana boshlang'ich sanadan oldin bo'lishi mumkin emas!",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    report_data = await run_db(
        ReportService.generate_custom_report,
        message.from_user.id,
        start_date,
        end_date,
    )
    await _reply_with_report(
        message,
        report_data,
        message.from_user.id,
        f"reports/custom_{message.from_user.id}_{date.today().strftime('%Y%m%d')}",
    )
    
    await state.clear()
