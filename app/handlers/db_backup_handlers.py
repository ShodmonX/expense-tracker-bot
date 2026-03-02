from __future__ import annotations

import math

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, InaccessibleMessage

from config import config
from keyboards import (
    get_backup_confirm_keyboard,
    get_backup_kind_keyboard,
    get_backup_list_keyboard,
    get_backup_menu_keyboard,
    get_manage_menu,
)
from services.db_backup.engine import BackupMeta, backup_engine

router = Router()

PAGE_SIZE = 5
KIND_CODE_TO_VALUE = {
    "a": None,
    "u": "auto",
    "m": "manual",
    "p": "pre_restore",
}
KIND_LABEL = {
    None: "Barchasi",
    "auto": "Auto",
    "manual": "Manual",
    "pre_restore": "Pre-restore",
}
SECTION_LABEL = {
    "l": "Backup ro'yxati",
    "r": "Restore uchun backup tanlash",
    "d": "O'chirish uchun backup tanlash",
}


def _is_admin(user_id: int) -> bool:
    return bool(config.ADMIN_ID) and user_id == config.ADMIN_ID


def _human_size(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size_bytes} B"


def _format_backup_rows(items: list[BackupMeta], offset: int) -> str:
    lines: list[str] = []
    for index, item in enumerate(items, start=offset + 1):
        created = item.created_at.astimezone().strftime("%Y-%m-%d %H:%M")
        lines.append(
            f"{index}. {item.filename}\n"
            f"   turi: {item.kind} | hajmi: {_human_size(item.size_bytes)} | vaqt: {created}"
        )
    return "\n".join(lines)


async def show_backup_menu(message: Message) -> None:
    if message.from_user is None:
        return
    if not _is_admin(message.from_user.id):
        await message.answer("⛔ Sizda DB backup bo'limiga ruxsat yo'q.")
        return

    await message.answer(
        "🗄 DB backup boshqaruvi\n\nKerakli amalni tanlang.",
        reply_markup=get_backup_menu_keyboard(),
    )


@router.message(Command("backup"))
async def backup_command_handler(message: Message):
    await show_backup_menu(message)


@router.message(F.text == "🗄 DB backup")
async def backup_menu_message_handler(message: Message):
    await show_backup_menu(message)


async def _render_backup_list(
    callback: CallbackQuery,
    section: str,
    kind_code: str,
    page: int,
) -> None:
    kind = KIND_CODE_TO_VALUE.get(kind_code)
    if section not in SECTION_LABEL or kind_code not in KIND_CODE_TO_VALUE:
        if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
            await callback.answer("Xabarni ko'rish mumkin emas", show_alert=True)
        else:
            await callback.message.edit_text(
                "Noto'g'ri so'rov.", reply_markup=get_backup_menu_keyboard()
            )
        return

    backups = await backup_engine.list_backups(kind)
    total = len(backups)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))
    page = max(0, min(page, total_pages - 1))

    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_items = backups[start:end]

    if total == 0:
        body = "Backup topilmadi."
    else:
        body = _format_backup_rows(page_items, start)

    text = (
        f"{SECTION_LABEL[section]}\n"
        f"Tur: {KIND_LABEL[kind]}\n"
        f"Sahifa: {page + 1}/{total_pages}\n"
        f"Jami: {total}\n\n"
        f"{body}"
    )
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("Xabarni ko'rish mumkin emas", show_alert=True)
    else:
        await callback.message.edit_text(
            text,
            reply_markup=get_backup_list_keyboard(
                page_items,
                section,
                kind_code,
                page,
                total_pages,
            ),
    )


@router.callback_query(F.data.startswith("adb:"))
async def db_backup_callback_handler(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("Xabarni ko'rish mumkin emas", show_alert=True)
        return
    await callback.answer()
    data = callback.data
    if data is None:
        await callback.answer("Xato: ma'lumot yo'q", show_alert=True)
        return

    try:
        if data == "adb:menu":
            await callback.message.edit_text(
                "🗄 DB backup boshqaruvi\n\nKerakli amalni tanlang.",
                reply_markup=get_backup_menu_keyboard(),
            )
            return

        if data == "adb:exit":
            await callback.message.edit_text("DB backup menyusi yopildi.")
            await callback.message.answer(
                "Boshqarish:",
                reply_markup=get_manage_menu(is_admin=True),
            )
            return

        if data == "adb:mk":
            backup = await backup_engine.create_backup("manual")
            await callback.message.edit_text(
                "✅ Manual backup yaratildi.\n"
                f"Fayl: {backup.filename}\n"
                f"Hajmi: {_human_size(backup.size_bytes)}",
                reply_markup=get_backup_menu_keyboard(),
            )
            return

        if data == "adb:st":
            auto_backups = await backup_engine.list_backups("auto")
            latest = auto_backups[0].filename if auto_backups else "yo'q"
            await callback.message.edit_text(
                "ℹ️ Auto backup holati\n"
                f"Yoqilgan: {'ha' if config.AUTO_BACKUP_ENABLED else 'yo\'q'}\n"
                f"Jadval: {config.AUTO_BACKUP_SCHEDULE}\n"
                f"Vaqt: {config.AUTO_BACKUP_HOUR:02d}:{config.AUTO_BACKUP_MINUTE:02d} (UTC+{config.AUTO_BACKUP_UTC_OFFSET_HOURS})\n"
                f"Retention: oxirgi {config.AUTO_BACKUP_RETENTION_COUNT} ta auto backup\n"
                f"Oxirgi auto backup: {latest}",
                reply_markup=get_backup_menu_keyboard(),
            )
            return

        if data == "adb:ls:kind":
            await callback.message.edit_text(
                "Backup ro'yxati uchun tur tanlang:",
                reply_markup=get_backup_kind_keyboard("l"),
            )
            return

        if data == "adb:rs:kind":
            await callback.message.edit_text(
                "Restore uchun tur tanlang:",
                reply_markup=get_backup_kind_keyboard("r"),
            )
            return

        if data == "adb:rm:kind":
            await callback.message.edit_text(
                "O'chirish uchun tur tanlang:",
                reply_markup=get_backup_kind_keyboard("d"),
            )
            return

        if data == "adb:cln:ask":
            await callback.message.edit_text(
                f"Auto backup cleanup bajarilsinmi?\n"
                f"Retention: oxirgi {config.AUTO_BACKUP_RETENTION_COUNT} ta auto backup",
                reply_markup=get_backup_confirm_keyboard("cleanup"),
            )
            return

        if data == "adb:cln:run":
            removed = await backup_engine.cleanup_auto_backups(
                config.AUTO_BACKUP_RETENTION_COUNT
            )
            await callback.message.edit_text(
                f"✅ Cleanup yakunlandi. O'chirilgan auto backup soni: {removed}",
                reply_markup=get_backup_menu_keyboard(),
            )
            return

        if data.startswith("adb:k:"):
            parts = data.split(":")
            if len(parts) != 5:
                raise ValueError("Noto'g'ri callback format")

            _, _, section, kind_code, page_str = parts
            await _render_backup_list(callback, section, kind_code, int(page_str))
            return

        if data.startswith("adb:p:"):
            parts = data.split(":")
            if len(parts) != 5:
                raise ValueError("Noto'g'ri callback format")

            _, _, section, kind_code, page_str = parts
            await _render_backup_list(callback, section, kind_code, int(page_str))
            return

        if data.startswith("adb:rc:"):
            filename = data.removeprefix("adb:rc:")
            await callback.message.edit_text(
                "⚠️ Restore qilish tasdiqlansinmi?\n"
                f"Tanlangan backup: {filename}\n\n"
                "Restore oldidan avtomatik pre-restore backup olinadi.",
                reply_markup=get_backup_confirm_keyboard("restore", filename),
            )
            return

        if data.startswith("adb:r:"):
            filename = data.removeprefix("adb:r:")
            result = await backup_engine.restore_backup(filename)
            await callback.message.edit_text(
                "✅ Restore muvaffaqiyatli yakunlandi.\n"
                f"Manba backup: {result.restored_from.filename}\n"
                f"Safety backup: {result.safety_backup.filename}",
                reply_markup=get_backup_menu_keyboard(),
            )
            return

        if data.startswith("adb:dc:"):
            filename = data.removeprefix("adb:dc:")
            await callback.message.edit_text(
                "⚠️ Backup faylini o'chirish tasdiqlansinmi?\n"
                f"Fayl: {filename}",
                reply_markup=get_backup_confirm_keyboard("delete", filename),
            )
            return

        if data.startswith("adb:d:"):
            filename = data.removeprefix("adb:d:")
            deleted = await backup_engine.delete_backup(filename)
            await callback.message.edit_text(
                (
                    f"✅ Backup o'chirildi: {filename}"
                    if deleted
                    else f"ℹ️ Backup topilmadi: {filename}"
                ),
                reply_markup=get_backup_menu_keyboard(),
            )
            return

        await callback.message.edit_text(
            "Noma'lum amal.",
            reply_markup=get_backup_menu_keyboard(),
        )
    except Exception as exc:
        await callback.message.edit_text(
            f"❌ Amal bajarilmadi: {exc}",
            reply_markup=get_backup_menu_keyboard(),
        )
