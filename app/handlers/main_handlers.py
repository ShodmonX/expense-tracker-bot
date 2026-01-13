from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import get_db
from keyboards import (
    get_main_menu,
    get_manage_menu,
    get_reports_menu,
    get_settings_keyboard,
)

router = Router()


@router.message(lambda message: message.text and message.text.startswith('/'))
async def command_handler(message: Message):
    if message.text == '/start':
        db = next(get_db())
        from models import User

        user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name,
            )
            db.add(user)
            db.commit()

        welcome_message = (
            "👋 Assalomu alaykum! Xarajatlar va to'lovlarni boshqarish botiga xush kelibsiz!\n\n"
            "📊 **Bot imkoniyatlari:**\n"
            "• Kunlik, haftalik, oylik, yillik xarajatlar\n"
            "• Kelajakdagi xarajatlar va to'lovlar\n"
            "• Avtomatik eslatmalar (kunlik, oylik, yillik)\n"
            "• Excel formatida hisobotlar\n"
            "• Kategoriyalar bo'yicha tahlillar\n\n"
            "Quyidagi tugmalardan foydalanishingiz mumkin:"
        )
        await message.answer(welcome_message, reply_markup=get_main_menu())
        return

    if message.text == '/menu':
        await message.answer("Asosiy menyu:", reply_markup=get_main_menu())
        return

    if message.text == '/today':
        from handlers.report_handlers import today_report
        from aiogram.types import CallbackQuery

        callback = CallbackQuery(
            id="0",
            from_user=message.from_user,
            chat_instance="0",
            message=message,
            data="today_report",
        )
        await today_report(callback)
        return

    if message.text == '/report':
        await message.answer(
            "Hisobot turini tanlang:",
            reply_markup=get_reports_menu(),
        )
        return

    if message.text == '/help':
        help_text = (
            "🆘 **Yordam**\n\n"
            "**Asosiy funksiyalar:**\n"
            "1. **Xarajat qo'shish** - kunlik, haftalik, oylik, yillik xarajatlar\n"
            "2. **To'lov qo'shish** - oylik, yillik, choraklik to'lovlar\n"
            "3. **Hisobotlar** - kunlik, haftalik, oylik, yillik hisobotlar\n"
            "4. **Eslatmalar** - to'lovlar uchun avtomatik eslatmalar\n\n"
            "**Foydalanish:**\n"
            "• Xarajat qo'shish uchun 'Xarajat qo'shish' tugmasini bosing\n"
            "• Hisobot olish uchun kerakli davrni tanlang\n"
            "• Excel fayl avtomatik yuklanadi\n\n"
            "**Eslatmalar:**\n"
            "• Kunlik to'lovlar: 1 kun oldin\n"
            "• Oylik to'lovlar: oxirgi 3 kun har kuni\n"
            "• Yillik to'lovlar: oxirgi 1 hafta har kuni\n"
            "• Kunlik hisobot: har kuni soat 23:00 da"
        )
        await message.answer(help_text, reply_markup=get_main_menu())


@router.callback_query(F.data == "manage_menu")
async def manage_menu_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Boshqarish:",
        reply_markup=get_manage_menu(),
    )


@router.callback_query(F.data == "reports_menu")
async def reports_menu_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Hisobotlar:",
        reply_markup=get_reports_menu(),
    )


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Asosiy menyu:",
        reply_markup=get_main_menu(),
    )


@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "Amal bekor qilindi.",
        reply_markup=get_main_menu(),
    )


@router.callback_query(F.data == "settings")
async def settings_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Sozlamalar:",
        reply_markup=get_settings_keyboard(),
    )


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    await callback.answer()
    help_text = (
        "🆘 **Yordam**\n\n"
        "**Qo'llanma:**\n"
        "1. Xarajat qo'shish uchun 'Xarajat qo'shish' tugmasini bosing\n"
        "2. To'lov qo'shish uchun 'To'lov qo'shish' tugmasini bosing\n"
        "3. Hisobot olish uchun kerakli davrni tanlang\n"
        "4. Excel fayl avtomatik yuklanadi\n\n"
        "**Savollar bo'lsa:** @your_username"
    )
    await callback.message.edit_text(help_text, reply_markup=get_main_menu())
