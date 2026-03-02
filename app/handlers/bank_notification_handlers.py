from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import re

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InaccessibleMessage, Message

from database import run_db
from keyboards import (
    get_bank_description_choice_keyboard,
    get_categories_keyboard,
    get_income_categories_keyboard,
    get_main_menu,
)
from models import ExpenseType
from services.expense_service import ExpenseService
from services.income_service import IncomeService
from states import BankMessageStates

router = Router()

BANK_SIGNED_AMOUNT_RE = re.compile(
    r"^\s*(?P<sign>[➖➕+-])\s*(?P<amount>[0-9][0-9\.\s,]*)\s*UZS\b",
    re.IGNORECASE | re.MULTILINE,
)
BANK_DESCRIPTION_RE = re.compile(r"^\s*📍\s*(?P<desc>.+?)\s*$", re.MULTILINE)
BANK_DATE_RE = re.compile(r"\b(?P<date>\d{2}\.\d{2}\.\d{4})\b")


@dataclass(slots=True)
class ParsedBankMessage:
    kind: str
    amount: float
    operation_date: date
    description: str


def _format_money_uzs(amount: float) -> str:
    if abs(amount - round(amount)) < 1e-9:
        return f"{amount:,.0f}".replace(",", " ")
    return f"{amount:,.2f}".replace(",", " ").replace(".", ",")


def _parse_localized_amount(raw_amount: str) -> float | None:
    cleaned = re.sub(r"[^\d,\.]", "", raw_amount)
    if not cleaned:
        return None

    if "," in cleaned:
        int_part, frac_part = cleaned.rsplit(",", 1)
        int_digits = re.sub(r"\D", "", int_part)
        frac_digits = re.sub(r"\D", "", frac_part)
        if not int_digits:
            return None
        frac_digits = (frac_digits + "00")[:2]
        return float(f"{int_digits}.{frac_digits}")

    digits = re.sub(r"\D", "", cleaned)
    if not digits:
        return None
    return float(digits)


def _detect_kind(text: str) -> str | None:
    first_line = (text.strip().splitlines() or [""])[0].lower()
    if "💸" in first_line and "amaliyot" in first_line:
        return "expense"
    if "🎉" in first_line and "ldirish" in first_line:
        return "income"

    for match in BANK_SIGNED_AMOUNT_RE.finditer(text):
        sign = match.group("sign")
        if sign in {"➖", "-"}:
            return "expense"
        if sign in {"➕", "+"}:
            return "income"
    return None


def _parse_bank_message(text: str) -> ParsedBankMessage | None:
    kind = _detect_kind(text)
    if kind is None:
        return None

    signed_amount_matches = list(BANK_SIGNED_AMOUNT_RE.finditer(text))
    selected_amount_raw: str | None = None

    for match in signed_amount_matches:
        sign = match.group("sign")
        if kind == "expense" and sign in {"➖", "-"}:
            selected_amount_raw = match.group("amount")
            break
        if kind == "income" and sign in {"➕", "+"}:
            selected_amount_raw = match.group("amount")
            break

    if selected_amount_raw is None and signed_amount_matches:
        selected_amount_raw = signed_amount_matches[0].group("amount")

    if selected_amount_raw is None:
        return None

    amount = _parse_localized_amount(selected_amount_raw)
    if amount is None or amount <= 0:
        return None

    description_match = BANK_DESCRIPTION_RE.search(text)
    description = (
        description_match.group("desc").strip()
        if description_match
        else ("Bank to'ldirish" if kind == "income" else "Bank amaliyoti")
    )

    date_matches = BANK_DATE_RE.findall(text)
    operation_date = date.today()
    if date_matches:
        try:
            operation_date = datetime.strptime(date_matches[-1], "%d.%m.%Y").date()
        except ValueError:
            operation_date = date.today()

    return ParsedBankMessage(
        kind=kind,
        amount=amount,
        operation_date=operation_date,
        description=description,
    )


async def _ask_description_choice_by_message(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    parsed_description = (data.get("bank_description") or "").strip()
    if not parsed_description:
        parsed_description = (data.get("bank_category") or "").strip()

    text = (
        "📝 Bank xabaridan olingan izoh:\n"
        f"{parsed_description}\n\n"
        "✅ Shu izohni qoldirish tugmasini bosing yoki shu yerga yangi izoh yozib yuboring."
    )
    await message.answer(text, reply_markup=get_bank_description_choice_keyboard())
    await state.set_state(BankMessageStates.waiting_for_description_choice)


async def _ask_description_choice_by_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return

    data = await state.get_data()
    parsed_description = (data.get("bank_description") or "").strip()
    if not parsed_description:
        parsed_description = (data.get("bank_category") or "").strip()

    text = (
        "📝 Bank xabaridan olingan izoh:\n"
        f"{parsed_description}\n\n"
        "✅ Shu izohni qoldirish tugmasini bosing yoki shu yerga yangi izoh yozib yuboring."
    )
    await callback.message.edit_text(text, reply_markup=get_bank_description_choice_keyboard())
    await state.set_state(BankMessageStates.waiting_for_description_choice)


async def _save_bank_operation(
    reply_message: Message,
    state: FSMContext,
    user_id: int,
    custom_description: str | None = None,
) -> None:
    data = await state.get_data()

    kind = str(data.get("bank_kind") or "").strip().lower()
    amount = float(data.get("bank_amount") or 0)
    date_raw = str(data.get("bank_date") or "")
    category = str(data.get("bank_category") or "").strip()

    if kind not in {"expense", "income"} or amount <= 0 or not date_raw:
        await state.clear()
        await reply_message.answer(
            "❌ Bank xabarini saqlashda xatolik yuz berdi. Qaytadan yuboring.",
            reply_markup=get_main_menu(),
        )
        return

    try:
        operation_date = date.fromisoformat(date_raw)
    except ValueError:
        operation_date = date.today()

    description = (custom_description or "").strip()
    if not description:
        description = str(data.get("bank_description") or "").strip()
    if not description:
        description = category

    if not category:
        category = "Kirim" if kind == "income" else "Boshqa"

    if kind == "expense":
        await run_db(
            ExpenseService.add_expense, # pyright: ignore[reportArgumentType]
            user_id=user_id,
            amount=amount,
            category=category,
            description=description,
            expense_date=operation_date,
            expense_type=ExpenseType.ONCE,
            is_future=False,
        )
        success_text = (
            "✅ Bank xabaridan xarajat saqlandi!\n\n"
            f"💰 Miqdor: {_format_money_uzs(amount)} so'm\n"
            f"📂 Kategoriya: {category}\n"
            f"📝 Izoh: {description}\n"
            f"📅 Sana: {operation_date.strftime('%d.%m.%Y')}"
        )
    else:
        await run_db(
            IncomeService.add_income,  # pyright: ignore[reportArgumentType]
            user_id=user_id,
            amount=amount,
            description=description,
            category=category,
            income_date=operation_date,
        )
        success_text = (
            "✅ Bank xabaridan kirim saqlandi!\n\n"
            f"💰 Miqdor: {_format_money_uzs(amount)} so'm\n"
            f"📂 Kategoriya: {category}\n"
            f"📝 Izoh: {description}\n"
            f"📅 Sana: {operation_date.strftime('%d.%m.%Y')}"
        )

    await state.clear()
    await reply_message.answer(success_text, reply_markup=get_main_menu())


@router.message(StateFilter("*"), F.text.regexp(r"^\s*(💸\s*Amaliyot|🎉\s*To['’`]?ldirish)\b"))
async def capture_bank_notification(message: Message, state: FSMContext):
    if message.from_user is None or message.text is None:
        return

    parsed = _parse_bank_message(message.text)
    if parsed is None:
        return

    await state.clear()
    await state.update_data(
        bank_kind=parsed.kind,
        bank_amount=parsed.amount,
        bank_date=parsed.operation_date.isoformat(),
        bank_description=parsed.description,
    )

    operation_title = "Xarajat" if parsed.kind == "expense" else "Kirim"
    prompt = (
        "🏦 Bank xabari aniqlandi\n\n"
        f"🔖 Turi: {operation_title}\n"
        f"💰 Miqdor: {_format_money_uzs(parsed.amount)} UZS\n"
        f"📅 Sana: {parsed.operation_date.strftime('%d.%m.%Y')}\n"
        f"📝 Izoh: {parsed.description}\n\n"
        "📂 Endi kategoriyani tanlang:"
    )

    if parsed.kind == "expense":
        markup = get_categories_keyboard()
    else:
        markup = get_income_categories_keyboard()

    await message.answer(prompt, reply_markup=markup)
    await state.set_state(BankMessageStates.waiting_for_category)


@router.callback_query(BankMessageStates.waiting_for_category, F.data.startswith("cat_"))
async def bank_category_expense_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data is None:
        return

    data = await state.get_data()
    if data.get("bank_kind") != "expense":
        return

    category = callback.data.replace("cat_", "")
    await state.update_data(bank_category=category)
    await _ask_description_choice_by_callback(callback, state)


@router.callback_query(BankMessageStates.waiting_for_category, F.data.startswith("income_category_"))
async def bank_category_income_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data is None:
        return

    data = await state.get_data()
    if data.get("bank_kind") != "income":
        return

    category = callback.data.replace("income_category_", "")
    await state.update_data(bank_category=category)
    await _ask_description_choice_by_callback(callback, state)


@router.message(BankMessageStates.waiting_for_category)
async def bank_category_text(message: Message, state: FSMContext):
    if message.from_user is None:
        return

    category = (message.text or "").strip()
    if not category:
        await message.answer("❌ Kategoriya kiriting yoki tugmadan tanlang.")
        return

    await state.update_data(bank_category=category)
    await _ask_description_choice_by_message(message, state)


@router.callback_query(BankMessageStates.waiting_for_description_choice, F.data == "bank_desc_keep")
async def bank_description_keep(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if isinstance(callback.message, InaccessibleMessage) or callback.message is None:
        await callback.answer("❌ Xabarni ko'rish mumkin emas.", show_alert=True)
        return

    await _save_bank_operation(callback.message, state, callback.from_user.id)


@router.message(BankMessageStates.waiting_for_description_choice)
async def bank_description_custom_text(message: Message, state: FSMContext):
    if message.from_user is None:
        return

    custom_description = (message.text or "").strip()
    if not custom_description:
        await message.answer("❌ Izoh bo'sh bo'lmasligi kerak. Yangi izohni yozing yoki tugmani bosing.")
        return

    await _save_bank_operation(
        message,
        state,
        message.from_user.id,
        custom_description=custom_description,
    )
