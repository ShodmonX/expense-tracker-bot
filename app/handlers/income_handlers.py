from aiogram import Router, F
from aiogram.types import InaccessibleMessage, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import date, datetime

from states import IncomeStates
from keyboards import *
from services.income_service import IncomeService
from utils.helpers import parse_amount, parse_date
from database import run_db

router = Router()

@router.message(F.text == "💵 Kirim qo'shish")
async def add_income_message(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(IncomeStates.waiting_for_amount)
    
    await message.answer(
        "💰 **Kirim miqdorini kiriting:**\n\n"
        "Masalan: 50000",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "add_income")
async def add_income_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await state.set_state(IncomeStates.waiting_for_amount)
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return
    await callback.message.answer(
        "💰 **Kirim miqdorini kiriting:**\n\n"
        "Masalan: 50000",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )

@router.message(IncomeStates.waiting_for_amount)
async def process_income_amount(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("❌ Xabarni to'ldirish kerak. Iltimos, miqdorni kiriting:")
        return
    try:
        amount = parse_amount(message.text)
        if amount is None:
            await message.answer("❌ Noto'g'ri miqdor formati. Iltimos, faqat raqamlarni kiriting:")
            return
        if amount <= 0:
            await message.answer("❌ Miqdor 0 dan katta bo'lishi kerak. Qaytadan kiriting:")
            return
            
        await state.update_data(amount=amount)
        await state.set_state(IncomeStates.waiting_for_category)
        
        await message.answer(
            "📂 **Kirim kategoriyasini tanlang:**\n\n"
            "Yoki o'zingiz yozing:",
            reply_markup=get_income_categories_keyboard()
        )
    except ValueError:
        await message.answer("❌ Noto'g'ri miqdor. Iltimos, faqat raqamlarni kiriting:")

@router.message(IncomeStates.waiting_for_category)
async def process_income_category(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("❌ Xabarni to'ldirish kerak. Iltimos, kategoriyani kiriting:")
        return
    category = message.text.strip() or "Kirim"
    await state.update_data(category=category)
    await state.set_state(IncomeStates.waiting_for_description)
    
    await message.answer(
        "📝 **Kirim haqida izoh qoldiring:**\n\n"
        "Yoki 'O'tkazish' tugmasini bosing:",
        reply_markup=get_skip_description_keyboard()
    )

@router.callback_query(F.data == "skip_income_description")
async def skip_income_description_s(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    category = data.get('category', 'Kirim')
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return
    
    await state.update_data(description=category)
    await state.set_state(IncomeStates.waiting_for_date)
    
    await callback.message.edit_text(
        "📅 **Kirim sanasini kiriting:**\n\n"
        "Format: DD.MM.YYYY\n"
        "Masalan: 05.01.2026\n\n"
        "Yoki 'Bugun' tugmasini bosing:",
        reply_markup=get_today_keyboard()
    )

@router.message(IncomeStates.waiting_for_description)
async def process_income_description(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("❌ Xabarni to'ldirish kerak. Iltimos, izohni kiriting:")
        return
    description = message.text.strip()
    await state.update_data(description=description)
    await state.set_state(IncomeStates.waiting_for_date)
    
    await message.answer(
        "📅 **Kirim sanasini kiriting:**\n\n"
        "Format: DD.MM.YYYY\n"
        "Masalan: 05.01.2026\n\n"
        "Yoki 'Bugun' tugmasini bosing:",
        reply_markup=get_today_keyboard()
    )

@router.callback_query(F.data == "use_today_date")
async def use_today_date_income(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    # Debug: Check what data is in state
    data = await state.get_data()
    print(f"DEBUG: State data before save_income: {data}")
    
    await save_income(callback, state, date.today())

@router.message(IncomeStates.waiting_for_date)
async def process_income_date(message: Message, state: FSMContext):
    if message.text is None:
        await message.answer("❌ Xabarni to'ldirish kerak. Iltimos, sanani kiriting:")
        return
    try:
        income_date = parse_date(message.text)
        if income_date is None:
            await message.answer(
                "❌ Noto'g'ri sana formati. Iltimos, DD.MM.YYYY formatida kiriting:\n\n"
                "Masalan: 05.01.2026"
            )
            return
        await save_income(message, state, income_date)
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri sana formati. Iltimos, DD.MM.YYYY formatida kiriting:\n\n"
            "Masalan: 05.01.2026"
        )

async def save_income(message_or_callback, state: FSMContext, income_date: date):
    data = await state.get_data()
    print(f"DEBUG: save_income called with data: {data}")
    
    # Check if all required data is present
    required_fields = ['amount', 'description', 'category']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        error_msg = f"❌ Ma'lumotlar to'liq emas. Yetishmayotgan maydonlar: {', '.join(missing_fields)}"
        print(f"DEBUG: Missing fields: {missing_fields}")
        if hasattr(message_or_callback, 'message'):
            await message_or_callback.message.edit_text(error_msg, reply_markup=get_main_menu())
        else:
            await message_or_callback.answer(error_msg, reply_markup=get_main_menu())
        await state.clear()
        return
    
    income = await run_db(
        IncomeService.add_income,
        user_id=message_or_callback.from_user.id,
        amount=data['amount'],
        description=data['description'],
        category=data['category'],
        income_date=income_date,
    )
    
    # Format success message
    message_text = f"✅ **Kirim muvaffaqiyatli qo'shildi!**\n\n"
    message_text += f"💰 Miqdor: {income.amount:,.0f} so'm\n"
    message_text += f"📂 Kategoriya: {income.category}\n"
    message_text += f"📝 Izoh: {income.description}\n"
    message_text += f"📅 Sana: {income.date.strftime('%d.%m.%Y')}"
    
    if hasattr(message_or_callback, 'message'):
        # Callback query
        await message_or_callback.message.edit_text(
            message_text,
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
    else:
        # Regular message
        await message_or_callback.answer(
            message_text,
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
    
    await state.clear()

@router.callback_query(F.data == "income_summary")
async def show_income_summary(callback: CallbackQuery):
    await callback.answer()
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return
    summary = await run_db(IncomeService.get_monthly_income, callback.from_user.id)
    
    message_text = f"💵 **{summary['month_name']} oylik kirim xulosasi**\n\n"
    
    if summary['income_count'] == 0:
        message_text += "📊 Bu oy kirimlar kiritilmagan."
    else:
        message_text += f"📊 Jami kirimlar soni: {summary['income_count']} ta\n"
        message_text += f"💰 Jami summa: {summary['total_amount']:,.0f} so'm\n\n"
        
        message_text += "**Kirimlar ro'yxati:**\n"
        for i, income in enumerate(summary['incomes'], 1):
            amount_text = f"{income.amount:,.0f}".replace(",", " ")
            date_text = income.date.strftime("%d.%m.%Y")
            
            message_text += f"{i}. 📅 {date_text} | 💵 {amount_text} so'm\n"
            message_text += f"   📂 {income.category} | 📝 {income.description}\n"
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_income_summary_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "skip_income_description")
async def skip_income_description(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return
    
    data = await state.get_data()
    category = data.get('category', 'Kirim')
    
    await state.update_data(description=category)
    await state.set_state(IncomeStates.waiting_for_date)
    
    await callback.message.edit_text(
        "📅 **Kirim sanasini kiriting:**\n\n"
        "Format: DD.MM.YYYY\n"
        "Masalan: 05.01.2026\n\n"
        "Yoki 'Bugun' tugmasini bosing:",
        reply_markup=get_today_keyboard()
    )

@router.callback_query(IncomeStates.waiting_for_category, F.data.startswith("income_category_"))
async def process_income_category_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return
    if callback.data is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return
    category = callback.data.replace("income_category_", "")
    await state.update_data(category=category)
    await state.set_state(IncomeStates.waiting_for_description)
    
    await callback.message.edit_text(
        "📝 **Kirim haqida izoh qoldiring:**\n\n"
        "Yoki 'O'tkazish' tugmasini bosing:",
        reply_markup=get_skip_description_keyboard()
    )

@router.callback_query(F.data == "cancel")
async def cancel_income(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        "❌ Bekor qilindi.",
        reply_markup=get_main_menu() # type: ignore
    )
