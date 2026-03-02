from __future__ import annotations

import pytz
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from database import run_db
from keyboards import (
    get_main_menu,
    get_report_format_keyboard,
    get_settings_keyboard,
    get_timezone_keyboard,
)
from services.settings_service import SettingsService
from states import SettingsStates

router = Router()

TIMEZONE_MAP = {
    "tashkent": "Asia/Tashkent",
    "istanbul": "Europe/Istanbul",
    "dubai": "Asia/Dubai",
    "moscow": "Europe/Moscow",
    "utc": "UTC",
}


def _status_text(enabled: bool) -> str:
    return "✅ Yoqilgan" if enabled else "❌ O'chirilgan"


def _render_settings_text(settings) -> str:
    report_format = "PDF" if (settings.report_format or "").lower() == "pdf" else "XLSX"
    return (
        "⚙️ **Sozlamalar**\n\n"
        f"🌐 Vaqt zonasi: `{settings.timezone}`\n"
        f"📁 Hisobot formati: **{report_format}**\n"
        f"🔔 Kunlik eslatma: {_status_text(bool(settings.daily_reminder_enabled))}\n"
        f"🚨 Overdue eslatma: {_status_text(bool(settings.overdue_reminder_enabled))}\n"
        f"📊 Kunlik hisobot: {_status_text(bool(settings.daily_summary_enabled))}"
    )


async def _show_settings(message: Message, user_id: int) -> None:
    settings = await run_db(SettingsService.get_or_create, user_id) # pyright: ignore[reportArgumentType]
    await message.answer(
        _render_settings_text(settings),
        parse_mode="Markdown",
        reply_markup=get_settings_keyboard(
            settings.report_format,
            bool(settings.daily_reminder_enabled),
            bool(settings.overdue_reminder_enabled),
            bool(settings.daily_summary_enabled),
        ),
    )


async def _edit_settings(callback: CallbackQuery, user_id: int) -> None:
    settings = await run_db(SettingsService.get_or_create, user_id) # pyright: ignore[reportArgumentType]
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return

    await callback.message.edit_text(
        _render_settings_text(settings),
        parse_mode="Markdown",
        reply_markup=get_settings_keyboard(
            settings.report_format,
            bool(settings.daily_reminder_enabled),
            bool(settings.overdue_reminder_enabled),
            bool(settings.daily_summary_enabled),
        ),
    )


@router.callback_query(F.data == "settings:format")
async def settings_report_format_callback(callback: CallbackQuery):
    await callback.answer()
    settings = await run_db(SettingsService.get_or_create, callback.from_user.id) # pyright: ignore[reportArgumentType]

    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return

    await callback.message.edit_text(
        "📁 Hisobot formatini tanlang:",
        reply_markup=get_report_format_keyboard(settings.report_format),
    )


@router.callback_query(F.data.startswith("settings:fmt:set:"))
async def settings_report_format_set_callback(callback: CallbackQuery):
    await callback.answer()
    if callback.data is None:
        return

    format_value = callback.data.rsplit(":", 1)[-1]
    await run_db(SettingsService.set_report_format, callback.from_user.id, format_value) # pyright: ignore[reportArgumentType]
    await _edit_settings(callback, callback.from_user.id)


@router.message(F.text == "⚙️ Sozlamalar")
async def settings_message_handler(message: Message, state: FSMContext):
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return

    await state.clear()
    await _show_settings(message, message.from_user.id)


@router.callback_query(F.data == "settings:menu")
async def settings_menu_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await _edit_settings(callback, callback.from_user.id)


@router.callback_query(F.data == "settings:close")
async def settings_close_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()

    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        return

    await callback.message.edit_text("Sozlamalar yopildi.")
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu())


@router.callback_query(F.data == "settings:toggle:daily")
async def settings_toggle_daily_callback(callback: CallbackQuery):
    await callback.answer()
    await run_db(SettingsService.toggle_daily_reminder, callback.from_user.id) # pyright: ignore[reportArgumentType]
    await _edit_settings(callback, callback.from_user.id)


@router.callback_query(F.data == "settings:toggle:overdue")
async def settings_toggle_overdue_callback(callback: CallbackQuery):
    await callback.answer()
    await run_db(SettingsService.toggle_overdue_reminder, callback.from_user.id) # pyright: ignore[reportArgumentType]
    await _edit_settings(callback, callback.from_user.id)


@router.callback_query(F.data == "settings:toggle:summary")
async def settings_toggle_summary_callback(callback: CallbackQuery):
    await callback.answer()
    await run_db(SettingsService.toggle_daily_summary, callback.from_user.id) # pyright: ignore[reportArgumentType]
    await _edit_settings(callback, callback.from_user.id)


@router.callback_query(F.data == "settings:timezone")
async def settings_timezone_callback(callback: CallbackQuery):
    await callback.answer()

    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return

    await callback.message.edit_text(
        "🌐 Vaqt zonasini tanlang:",
        reply_markup=get_timezone_keyboard(),
    )


@router.callback_query(F.data.startswith("settings:tz:set:"))
async def settings_timezone_set_callback(callback: CallbackQuery):
    await callback.answer()
    if callback.data is None:
        return

    key = callback.data.rsplit(":", 1)[-1]
    timezone_name = TIMEZONE_MAP.get(key)
    if not timezone_name:
        await callback.answer("❌ Noma'lum vaqt zonasi", show_alert=True)
        return

    await run_db(SettingsService.set_timezone, callback.from_user.id, timezone_name) # pyright: ignore[reportArgumentType]
    await _edit_settings(callback, callback.from_user.id)


@router.callback_query(F.data == "settings:tz:custom")
async def settings_timezone_custom_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return

    await state.set_state(SettingsStates.waiting_for_timezone)
    await callback.message.edit_text(
        "Vaqt zonasini kiriting.\n\n"
        "Masalan: `Asia/Tashkent`, `Europe/Istanbul`, `UTC`",
        parse_mode="Markdown",
    )


@router.message(SettingsStates.waiting_for_timezone)
async def settings_timezone_input_handler(message: Message, state: FSMContext):
    if message.from_user is None:
        await message.answer("❌ Foydalanuvchi ma'lumotlari topilmadi.")
        return

    timezone_name = (message.text or "").strip()
    if not timezone_name:
        await message.answer("❌ Vaqt zonasi kiriting. Masalan: Asia/Tashkent")
        return

    try:
        pytz.timezone(timezone_name)
    except Exception:
        await message.answer(
            "❌ Noto'g'ri vaqt zonasi. Masalan: `Asia/Tashkent`",
            parse_mode="Markdown",
        )
        return

    await run_db(SettingsService.set_timezone, message.from_user.id, timezone_name) # pyright: ignore[reportArgumentType]
    await state.clear()
    await _show_settings(message, message.from_user.id)
