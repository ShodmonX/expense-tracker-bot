from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import config
from database import run_db
from keyboards import (
    get_main_menu,
    get_manage_menu,
    get_reports_menu,
)

router = Router()


@router.message(lambda message: message.text and message.text.startswith('/'))
async def command_handler(message: Message, state: FSMContext):
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return
    if message.text == '/start':
        await state.clear()
        from models import User

        user = await run_db(
            lambda db: db.query(User).filter(User.telegram_id == message.from_user.id).first()
        )
        if not user:
            await run_db(
                lambda db: _create_user(
                    db,
                    User,
                    message.from_user.id,
                    message.from_user.username,
                    message.from_user.full_name,
                )
            )

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
        await state.clear()
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

    if message.text == '/backup':
        from handlers.db_backup_handlers import show_backup_menu

        await show_backup_menu(message)
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


@router.message(F.text == "🧾 Boshqarish")
async def manage_menu_handler(message: Message):
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return
    is_admin = bool(config.ADMIN_ID) and message.from_user.id == config.ADMIN_ID
    await message.answer(
        "Boshqarish:",
        reply_markup=get_manage_menu(is_admin=is_admin),
    )


@router.message(F.text == "📊 Hisobotlar")
async def reports_menu_handler(message: Message):
    await message.answer(
        "Hisobotlar:",
        reply_markup=get_reports_menu(),
    )


@router.message(F.text == "🔙 Ortga")
async def main_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Asosiy menyu:",
        reply_markup=get_main_menu(),
    )


@router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Amal bekor qilindi.",
        reply_markup=get_main_menu(),
    )


@router.message(F.text == "ℹ️ Yordam")
async def help_handler(message: Message):
    help_text = (
        "🆘 **Yordam**\n\n"
        "**Qo'llanma:**\n"
        "1. Xarajat qo'shish uchun '💰 Xarajat qo'shish' tugmasini bosing\n"
        "2. To'lov qo'shish uchun '💳 To'lov qo'shish' tugmasini bosing\n"
        "3. Hisobot olish uchun kerakli davrni tanlang\n"
        "4. Excel fayl avtomatik yuklanadi\n\n"
        "**Savollar bo'lsa:** @your_username"
    )
    await message.answer(help_text, reply_markup=get_main_menu())


# Keep callback handlers for inline keyboards that still need them
@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return
    await state.clear()
    await callback.message.answer(
        "Amal bekor qilindi.",
        reply_markup=get_main_menu(),
    )


def _create_user(db, user_model, telegram_id: int, username: str | None, full_name: str | None):
    user = user_model(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
    )
    db.add(user)
    db.commit()
