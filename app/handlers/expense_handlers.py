from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import date, timedelta

from states import ExpenseStates
from keyboards import *
from services.expense_service import ExpenseService
from models import ExpenseType
from utils.helpers import parse_amount, parse_date
from database import get_db

router = Router()

@router.callback_query(F.data == "add_expense")
async def add_expense(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(user_id=callback.from_user.id)
    await callback.message.edit_text(
        "Harajat miqdorini kiriting (so'm):\n\nMasalan: 150000 yoki 150 000",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(ExpenseStates.waiting_for_amount)

@router.message(ExpenseStates.waiting_for_amount)
async def process_expense_amount(message: Message, state: FSMContext):
    amount = parse_amount(message.text)
    
    if amount is None or amount <= 0:
        await message.answer(
            "❌ Noto'g'ri format. Iltimos, raqam kiriting:\n\nMasalan: 150000 yoki 150 000",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(amount=amount)
    await message.answer(
        "Kategoriyani tanlang:",
        reply_markup=get_categories_keyboard()
    )
    await state.set_state(ExpenseStates.waiting_for_category)

@router.callback_query(ExpenseStates.waiting_for_category, F.data.startswith("cat_"))
async def process_expense_category(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    category = callback.data.replace("cat_", "")
    await state.update_data(category=category)
    
    await callback.message.edit_text(
        "Sana tanlang yoki DD.MM.YYYY formatida yozing:",
        reply_markup=get_expense_date_keyboard()
    )
    await state.set_state(ExpenseStates.waiting_for_date)


@router.callback_query(ExpenseStates.waiting_for_date, F.data == "expense_date_today")
async def expense_date_today(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(date=date.today())
    await callback.message.edit_text(
        "Izoh qoldiring (ixtiyoriy):\n\nMasalan: Do'konda oziq-ovqat",
        reply_markup=get_skip_expense_description_keyboard(),
    )
    await state.set_state(ExpenseStates.waiting_for_description)


@router.callback_query(ExpenseStates.waiting_for_date, F.data == "expense_date_yesterday")
async def expense_date_yesterday(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(date=date.today() - timedelta(days=1))
    await callback.message.edit_text(
        "Izoh qoldiring (ixtiyoriy):\n\nMasalan: Do'konda oziq-ovqat",
        reply_markup=get_skip_expense_description_keyboard(),
    )
    await state.set_state(ExpenseStates.waiting_for_description)


@router.message(ExpenseStates.waiting_for_date)
async def process_expense_date(message: Message, state: FSMContext):
    expense_date = parse_date(message.text)
 
    if expense_date is None:
        await message.answer(
            "❌ Noto'g'ri sana formati. Iltimos, DD.MM.YYYY formatida kiriting (masalan: 03.01.2026).",
            reply_markup=get_cancel_keyboard(),
        )
        return
 
    if expense_date > date.today():
        await message.answer(
            "❌ Kelajakdagi sana qabul qilinmaydi. Iltimos, bugun yoki undan oldingi sanani kiriting.",
            reply_markup=get_cancel_keyboard(),
        )
        return

    await state.update_data(date=expense_date)
    await message.answer(
        "Izoh qoldiring (ixtiyoriy):\n\nMasalan: Do'konda oziq-ovqat",
        reply_markup=get_skip_expense_description_keyboard(),
    )
    await state.set_state(ExpenseStates.waiting_for_description)


@router.callback_query(ExpenseStates.waiting_for_description, F.data == "skip_expense_description")
async def skip_expense_description(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    await state.update_data(description=data.get("category", ""))

    # Use a lightweight message object compatible with save_expense
    await save_expense(callback.message, state)

@router.message(ExpenseStates.waiting_for_description)
async def process_expense_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    
    await save_expense(message, state)

async def save_expense(message: Message, state: FSMContext):
    data = await state.get_data()
    
    db = next(get_db())
    expense = ExpenseService.add_expense(
        db=db,
        user_id=data.get('user_id') or message.from_user.id,
        amount=data['amount'],
        category=data['category'],
        description=data.get('description', ''),
        expense_date=data.get('date', date.today()),
        expense_type=ExpenseType.ONCE,
        is_future=False
    )
    
    message_text = f"✅ Harajat muvaffaqiyatli qo'shildi!\n\n"
    message_text += f"💰 Miqdor: {data['amount']:,.0f} so'm\n"
    message_text += f"📂 Kategoriya: {data['category']}\n"
    if data.get('description'):
        message_text += f"📝 Izoh: {data['description']}\n"
    message_text += f"📅 Sana: {data.get('date', date.today()).strftime('%d.%m.%Y')}"
    
    await message.answer(message_text, reply_markup=get_main_menu())
    await state.clear()


@router.callback_query(F.data == "manage_last_expenses")
async def manage_last_expenses(callback: CallbackQuery):
    await callback.answer()
    db = next(get_db())
    expenses = ExpenseService.get_last_expenses(db, callback.from_user.id, limit=30)

    if not expenses:
        await callback.message.edit_text(
            "Oxirgi xarajatlar topilmadi.",
            reply_markup=get_manage_menu(),
        )
        return

    await callback.message.edit_text(
        "Oxirgi xarajatlar (o'chirish uchun tanlang):",
        reply_markup=get_manage_last_expenses_keyboard(expenses),
    )


@router.callback_query(F.data.startswith("delete_expense_"))
async def delete_expense_callback(callback: CallbackQuery):
    await callback.answer()
    try:
        expense_id = int(callback.data.replace("delete_expense_", ""))
    except ValueError:
        return

    db = next(get_db())
    deleted = ExpenseService.delete_expense(db, callback.from_user.id, expense_id)

    expenses = ExpenseService.get_last_expenses(db, callback.from_user.id, limit=30)
    if not expenses:
        text = "Oxirgi xarajatlar topilmadi." if deleted else "Xarajat topilmadi yoki o'chirish mumkin emas."
        await callback.message.edit_text(
            text,
            reply_markup=get_manage_menu(),
        )
        return

    await callback.message.edit_text(
        "Oxirgi xarajatlar (o'chirish uchun tanlang):",
        reply_markup=get_manage_last_expenses_keyboard(expenses),
    )