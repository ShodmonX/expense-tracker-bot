from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import date, timedelta, datetime
import calendar
import pytz

from states import PaymentStates
from keyboards import *
from services.payment_service import PaymentService
from models import PaymentFrequency, Payment
from config import config
from utils.helpers import parse_amount, parse_date
from database import get_db

router = Router()

@router.callback_query(F.data == "add_payment")
async def add_payment(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(user_id=callback.from_user.id)
    await callback.message.edit_text(
        "To'lov chastotasini tanlang:",
        reply_markup=get_payment_frequency_keyboard()
    )

@router.callback_query(F.data.startswith("payment_"))
async def process_payment_frequency(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    frequency_map = {
        "payment_weekly": PaymentFrequency.WEEKLY,
        "payment_biweekly": PaymentFrequency.BIWEEKLY,
        "payment_monthly": PaymentFrequency.MONTHLY,
        "payment_yearly": PaymentFrequency.YEARLY,
        "payment_quarterly": PaymentFrequency.QUARTERLY,
        "payment_once": PaymentFrequency.ONCE
    }
    
    frequency = frequency_map.get(callback.data)
    await state.update_data(frequency=frequency)
    
    if frequency in (PaymentFrequency.WEEKLY, PaymentFrequency.BIWEEKLY):
        await callback.message.edit_text(
            "Haftaning qaysi kunida to'lov qilasiz?",
            reply_markup=get_weekday_keyboard()
        )
        await state.set_state(PaymentStates.waiting_for_weekday)
        return

    if frequency == PaymentFrequency.MONTHLY:
        await callback.message.edit_text(
            "Oyning qaysi sanasida to'lov qilasiz?",
            reply_markup=get_day_of_month_keyboard()
        )
        await state.set_state(PaymentStates.waiting_for_day_of_month)
        return

    if frequency != PaymentFrequency.ONCE:
        await callback.message.edit_text(
            "Bu to'lovni nechchi marta qilasiz? (masalan: 4)\n\n"
            "Agar o'tkazib yuborsangiz, to'lov cheklanmaydi va avtomatik o'chmaydi.",
            reply_markup=get_skip_payment_occurrences_keyboard(),
        )
        await state.set_state(PaymentStates.waiting_for_occurrences)
        return

    await callback.message.edit_text(
        "To'lov miqdorini kiriting (so'm):\n\nMasalan: 500000 yoki 500 000",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(PaymentStates.waiting_for_amount)

@router.callback_query(PaymentStates.waiting_for_weekday, F.data.startswith("weekday_"))
async def process_payment_weekday(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        weekday = int(callback.data.replace("weekday_", ""))
    except ValueError:
        return

    today = date.today()
    days_ahead = (weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    due_date = today + timedelta(days=days_ahead)

    await state.update_data(weekday=weekday, due_date=due_date)

    await callback.message.edit_text(
        "Bu to'lovni nechchi marta qilasiz? (masalan: 4)\n\n"
        "Agar o'tkazib yuborsangiz, to'lov cheklanmaydi va avtomatik o'chmaydi.",
        reply_markup=get_skip_payment_occurrences_keyboard(),
    )
    await state.set_state(PaymentStates.waiting_for_occurrences)

@router.callback_query(PaymentStates.waiting_for_day_of_month, F.data.startswith("monthday_"))
async def process_payment_day_of_month(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        day_of_month = int(callback.data.replace("monthday_", ""))
    except ValueError:
        return

    today = date.today()
    last_day_this_month = calendar.monthrange(today.year, today.month)[1]
    day_this_month = min(day_of_month, last_day_this_month)
    candidate = date(today.year, today.month, day_this_month)
    if candidate <= today:
        if today.month == 12:
            next_month_year, next_month = today.year + 1, 1
        else:
            next_month_year, next_month = today.year, today.month + 1
        last_day_next_month = calendar.monthrange(next_month_year, next_month)[1]
        day_next_month = min(day_of_month, last_day_next_month)
        candidate = date(next_month_year, next_month, day_next_month)

    await state.update_data(day_of_month=day_of_month, due_date=candidate)

    await callback.message.edit_text(
        "Bu to'lovni nechchi marta qilasiz? (masalan: 4)\n\n"
        "Agar o'tkazib yuborsangiz, to'lov cheklanmaydi va avtomatik o'chmaydi.",
        reply_markup=get_skip_payment_occurrences_keyboard(),
    )
    await state.set_state(PaymentStates.waiting_for_occurrences)


@router.callback_query(PaymentStates.waiting_for_occurrences, F.data == "skip_payment_occurrences")
async def skip_payment_occurrences(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(occurrences_left=None)
    await callback.message.edit_text(
        "To'lov miqdorini kiriting (so'm):\n\nMasalan: 500000 yoki 500 000",
        reply_markup=get_cancel_keyboard(),
    )
    await state.set_state(PaymentStates.waiting_for_amount)


@router.message(PaymentStates.waiting_for_occurrences)
async def process_payment_occurrences(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    try:
        occurrences = int(text)
    except ValueError:
        await message.answer(
            "❌ Noto'g'ri qiymat. Iltimos, butun son kiriting (masalan: 4)\n"
            "Yoki 'O'tkazib yuborish' tugmasini bosing.",
            reply_markup=get_skip_payment_occurrences_keyboard(),
        )
        return

    if occurrences <= 0:
        await message.answer(
            "❌ Son 1 dan katta bo'lishi kerak.",
            reply_markup=get_skip_payment_occurrences_keyboard(),
        )
        return

    await state.update_data(occurrences_left=occurrences)
    await message.answer(
        "To'lov miqdorini kiriting (so'm):\n\nMasalan: 500000 yoki 500 000",
        reply_markup=get_cancel_keyboard(),
    )
    await state.set_state(PaymentStates.waiting_for_amount)

@router.message(PaymentStates.waiting_for_amount)
async def process_payment_amount(message: Message, state: FSMContext):
    amount = parse_amount(message.text)
    
    if amount is None or amount <= 0:
        await message.answer(
            "❌ Noto'g'ri format. Iltimos, raqam kiriting:\n\nMasalan: 500000 yoki 500 000",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(amount=amount)
    await message.answer(
        "Kategoriyani tanlang:",
        reply_markup=get_categories_keyboard()
    )
    await state.set_state(PaymentStates.waiting_for_category)


@router.callback_query(PaymentStates.waiting_for_category, F.data.startswith("cat_"))
async def process_payment_category(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    category = callback.data.replace("cat_", "")
    await state.update_data(category=category)

    await callback.message.edit_text(
        "To'lov haqida izoh bering (ixtiyoriy):\n\nMasalan: Kvartira ijara to'lovi",
        reply_markup=get_skip_payment_description_keyboard(),
    )
    await state.set_state(PaymentStates.waiting_for_description)

@router.message(PaymentStates.waiting_for_description)
async def process_payment_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    
    data = await state.get_data()
    frequency = data.get('frequency')

    if frequency in (PaymentFrequency.WEEKLY, PaymentFrequency.BIWEEKLY, PaymentFrequency.MONTHLY):
        await save_payment(message, state)
        return

    await message.answer(
        "To'lov sanasini kiriting (DD.MM.YYYY):\n\nMasalan: 01.02.2026\n"
        "Yoki: bugun, ertaga, kecha, +7 (7 kun keyin)",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(PaymentStates.waiting_for_date)


@router.callback_query(PaymentStates.waiting_for_description, F.data == "skip_payment_description")
async def skip_payment_description(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    await state.update_data(description=data.get("category", ""))

    frequency = data.get('frequency')
    if frequency in (PaymentFrequency.WEEKLY, PaymentFrequency.BIWEEKLY, PaymentFrequency.MONTHLY):
        await save_payment(callback.message, state)
        return

    await callback.message.edit_text(
        "To'lov sanasini kiriting (DD.MM.YYYY):\n\nMasalan: 01.02.2026\n"
        "Yoki: bugun, ertaga, kecha, +7 (7 kun keyin)",
        reply_markup=get_cancel_keyboard(),
    )
    await state.set_state(PaymentStates.waiting_for_date)

@router.message(PaymentStates.waiting_for_date)
async def process_payment_date(message: Message, state: FSMContext):
    due_date = parse_date(message.text)
    
    if due_date is None:
        await message.answer(
            "❌ Noto'g'ri sana formati. Iltimos, quyidagi formatlardan birida kiriting:\n\n"
            "DD.MM.YYYY (01.02.2026)\n"
            "bugun, ertaga, kecha\n"
            "+7 (7 kun keyin)",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(due_date=due_date)
    await save_payment(message, state)

async def save_payment(message: Message, state: FSMContext):
    data = await state.get_data()
    
    db = next(get_db())
    payment = PaymentService.add_payment(
        db=db,
        user_id=data.get('user_id') or message.from_user.id,
        amount=data['amount'],
        category=data.get('category') or "To'lov",
        description=data['description'],
        due_date=data['due_date'],
        frequency=data['frequency'],
        weekday=data.get('weekday'),
        day_of_month=data.get('day_of_month'),
        occurrences_left=data.get('occurrences_left'),
        is_paid=False
    )
    
    # Format message
    frequency_names = {
        PaymentFrequency.WEEKLY: "haftalik",
        PaymentFrequency.BIWEEKLY: "har 2 haftada",
        PaymentFrequency.MONTHLY: "oylik",
        PaymentFrequency.YEARLY: "yillik",
        PaymentFrequency.QUARTERLY: "choraklik",
        PaymentFrequency.ONCE: "bir martalik"
    }
    
    message_text = f"✅ To'lov muvaffaqiyatli qo'shildi!\n\n"
    message_text += f"💰 Miqdor: {data['amount']:,.0f} so'm\n"
    message_text += f"📂 Kategoriya: {data.get('category') or 'To\'lov'}\n"
    message_text += f"📝 Izoh: {data['description']}\n"
    message_text += f"📅 To'lov sanasi: {data['due_date'].strftime('%d.%m.%Y')}\n"
    message_text += f"📊 Chastota: {frequency_names[data['frequency']]}"
    
    await message.answer(message_text, reply_markup=get_main_menu())
    await state.clear()

@router.callback_query(F.data == "monthly_payment_summary")
async def show_monthly_payment_summary(callback: CallbackQuery):
    await callback.answer()
    db = next(get_db())
    summary = PaymentService.get_monthly_payment_summary(db, callback.from_user.id)
    
    # Format the summary message
    message_text = f"💵 **{summary['month_name']} oylik to'lovlar reja**\n\n"
    
    if summary['payment_count'] == 0:
        message_text += "🎉 Bu oy uchun to'lovlar rejalashtirilmagan!"
    else:
        message_text += f"📊 Jami to'lovlar soni: {summary['payment_count']} ta\n"
        message_text += f"💰 Jami summa: {summary['total_amount']:,.0f} so'm\n\n"
        
        message_text += "**To'lovlar ro'yxati:**\n"
        for i, payment in enumerate(summary['payments'], 1):
            amount_text = f"{payment.amount:,.0f}".replace(",", " ")
            date_text = payment.due_date.strftime("%d.%m.%Y")
            desc_text = getattr(payment, "description", "") or payment.title
            
            message_text += f"{i}. 📅 {date_text} | 💵 {amount_text} so'm\n"
            message_text += f"   📝 {desc_text}\n"
    
    await callback.message.edit_text(
        message_text,
        reply_markup=get_monthly_payment_summary_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "upcoming_payments")
async def show_upcoming_payments(callback: CallbackQuery):
    await callback.answer()
    db = next(get_db())
    payments = PaymentService.get_upcoming_payments(db, callback.from_user.id, days_ahead=30)
    
    if not payments:
        await callback.message.edit_text(
            "🔔 Keyingi 30 kun ichida to'lovlar topilmadi.",
            reply_markup=get_main_menu(),
        )
        return

    await callback.message.edit_text(
        "🔔 Kelgusi to'lovlar (30 kun):\n\nTo'lovni ko'rish uchun tanlang:",
        reply_markup=get_upcoming_payments_keyboard(payments),
    )


@router.callback_query(F.data.startswith("view_upcoming_payment_"))
async def view_upcoming_payment(callback: CallbackQuery):
    await callback.answer()
    try:
        payment_id = int(callback.data.replace("view_upcoming_payment_", ""))
    except ValueError:
        return

    db = next(get_db())
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == callback.from_user.id,
        Payment.is_paid == False,
    ).first()

    if not payment:
        await callback.message.edit_text(
            "❌ To'lov topilmadi yoki allaqachon bajarilgan.",
            reply_markup=get_main_menu(),
        )
        return

    today = _local_today()
    days_left = (payment.due_date - today).days
    if days_left < 0:
        status = f"🔴 {abs(days_left)} kun o'tib ketgan"
    elif days_left == 0:
        status = "🟠 Bugun"
    else:
        status = f"🟢 {days_left} kun qoldi"

    text = "🔔 **To'lov ma'lumotlari:**\n\n"
    text += f"📝 {payment.description}\n"
    text += f"📂 {payment.category or 'To\'lov'}\n"
    text += f"💰 {payment.amount:,.0f} so'm\n"
    text += f"📅 Sana: {payment.due_date.strftime('%d.%m.%Y')}\n"
    text += f"⏰ Holat: {status}"

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_upcoming_payment_detail_keyboard(payment.id),
    )

@router.callback_query(F.data == "manage_future_payments")
async def manage_future_payments(callback: CallbackQuery):
    await callback.answer()
    db = next(get_db())
    payments = PaymentService.get_future_payments(db, callback.from_user.id, limit=30)

    if not payments:
        await callback.message.edit_text(
            "Kelajakdagi to'lovlar topilmadi.",
            reply_markup=get_manage_menu(),
        )
        return

    await callback.message.edit_text(
        "Kelajakdagi to'lovlar:\n\nTo'lovni ko'rish uchun tanlang:",
        reply_markup=get_manage_future_payments_list_keyboard(payments),
    )


@router.callback_query(F.data.startswith("view_manage_future_payment_"))
async def view_manage_future_payment(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        payment_id = int(callback.data.replace("view_manage_future_payment_", ""))
    except ValueError:
        return

    db = next(get_db())
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == callback.from_user.id,
        Payment.is_paid == False,
    ).first()

    if not payment:
        await callback.message.edit_text(
            "❌ To'lov topilmadi yoki allaqachon bajarilgan.",
            reply_markup=get_manage_menu(),
        )
        return

    await state.update_data(
        pay_origin_manage=True,
        user_id=callback.from_user.id,
    )

    today = _local_today()
    days_left = (payment.due_date - today).days
    if days_left < 0:
        status = f"🔴 {abs(days_left)} kun o'tib ketgan"
    elif days_left == 0:
        status = "🟠 Bugun"
    else:
        status = f"🟢 {days_left} kun qoldi"

    text = "🗓 **Kelajakdagi to'lov:**\n\n"
    text += f"📝 {payment.description}\n"
    text += f"📂 {payment.category or 'To\'lov'}\n"
    text += f"💰 {payment.amount:,.0f} so'm\n"
    text += f"📅 Sana: {payment.due_date.strftime('%d.%m.%Y')}\n"
    text += f"⏰ Holat: {status}"

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_manage_future_payment_detail_keyboard(payment.id),
    )


def _is_manage_future_payments_message(text: str | None) -> bool:
    return bool(text) and "Kelajakdagi to'lovlar" in text


def _local_today() -> date:
    return datetime.now(pytz.timezone(config.TIMEZONE)).date()


@router.callback_query(F.data.startswith("confirm_pay_payment_"))
async def confirm_pay_payment_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        payment_id = int(callback.data.replace("confirm_pay_payment_", ""))
    except ValueError:
        return

    db = next(get_db())
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == callback.from_user.id,
        Payment.is_paid == False,
    ).first()
    if not payment:
        await callback.message.edit_text(
            "❌ To'lov topilmadi yoki allaqachon bajarilgan.",
            reply_markup=get_main_menu(),
        )
        return

    msg = "✅ To'lovni 'To\'landi' deb belgilaysizmi?\n\n"
    msg += f"📝 {payment.description}\n"
    msg += f"💰 {payment.amount:,.0f} so'm\n"
    msg += f"📅 Reja sanasi: {payment.due_date.strftime('%d.%m.%Y')}\n"
    msg += "\nEslatma: harajat bugungi sana bilan yoziladi."

    prev = await state.get_data()
    await state.update_data(
        pay_payment_id=payment_id,
        pay_origin_manage=bool(prev.get("pay_origin_manage", False))
        or _is_manage_future_payments_message(callback.message.text if callback.message else None),
        user_id=callback.from_user.id,
    )

    await callback.message.edit_text(
        msg,
        reply_markup=get_confirm_pay_payment_keyboard(payment_id),
    )


@router.callback_query(F.data.startswith("ask_pay_amount_"))
async def ask_pay_amount_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        payment_id = int(callback.data.replace("ask_pay_amount_", ""))
    except ValueError:
        return

    db = next(get_db())
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == callback.from_user.id,
        Payment.is_paid == False,
    ).first()
    if not payment:
        await callback.message.edit_text(
            "❌ To'lov topilmadi yoki allaqachon bajarilgan.",
            reply_markup=get_main_menu(),
        )
        return

    data = await state.get_data()
    await state.update_data(
        pay_payment_id=payment_id,
        user_id=callback.from_user.id,
        pay_origin_manage=data.get("pay_origin_manage", False),
    )

    msg = "✍️ To'langan summani kiriting (so'm):\n\n"
    msg += f"📝 {payment.description}\n"
    msg += f"📂 {payment.category or 'To\'lov'}\n"
    msg += f"📅 Reja sanasi: {payment.due_date.strftime('%d.%m.%Y')}\n"
    msg += f"💰 Reja summa: {payment.amount:,.0f} so'm\n\n"
    msg += "Masalan: 450000 yoki 450 000"

    await callback.message.edit_text(
        msg,
        reply_markup=get_cancel_keyboard(),
    )
    await state.set_state(PaymentStates.waiting_for_pay_amount)


@router.message(PaymentStates.waiting_for_pay_amount)
async def process_custom_pay_amount(message: Message, state: FSMContext):
    amount = parse_amount(message.text)
    if amount is None or amount <= 0:
        await message.answer(
            "❌ Noto'g'ri format. Iltimos, raqam kiriting:\n\nMasalan: 450000 yoki 450 000",
            reply_markup=get_cancel_keyboard(),
        )
        return

    data = await state.get_data()
    payment_id = data.get("pay_payment_id")
    if not payment_id:
        await state.clear()
        await message.answer("❌ Xatolik: payment topilmadi.", reply_markup=get_main_menu())
        return

    await state.update_data(pay_amount=amount)

    msg = f"✅ Summa: {amount:,.0f} so'm\n\nTasdiqlaysizmi?"
    await message.answer(
        msg,
        reply_markup=get_confirm_custom_pay_payment_keyboard(int(payment_id)),
    )


@router.callback_query(F.data.startswith("do_pay_payment_custom_"))
async def do_pay_payment_custom_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        payment_id = int(callback.data.replace("do_pay_payment_custom_", ""))
    except ValueError:
        return

    data = await state.get_data()
    paid_amount = data.get("pay_amount")
    origin_manage = bool(data.get("pay_origin_manage", False))
    if paid_amount is None:
        await callback.message.edit_text(
            "❌ Summa topilmadi. Qaytadan urinib ko'ring.",
            reply_markup=get_main_menu(),
        )
        await state.clear()
        return

    db = next(get_db())
    paid = PaymentService.pay_payment_and_record_expense(
        db,
        payment_id,
        callback.from_user.id,
        paid_amount=float(paid_amount),
    )

    await state.clear()

    if origin_manage:
        payments = PaymentService.get_future_payments(db, callback.from_user.id, limit=30)
        if payments:
            await callback.message.edit_text(
                "Kelajakdagi to'lovlar:\n\nTo'lovni ko'rish uchun tanlang:",
                reply_markup=get_manage_future_payments_list_keyboard(payments),
            )
        else:
            await callback.message.edit_text(
                "Kelajakdagi to'lovlar topilmadi.",
                reply_markup=get_manage_menu(),
            )
        return

    if paid:
        await callback.message.edit_text(
            "✅ To'lov belgilandi va harajatlar ro'yxatiga qo'shildi.",
            reply_markup=get_main_menu(),
        )
    else:
        await callback.message.edit_text(
            "❌ To'lov topilmadi yoki allaqachon bajarilgan.",
            reply_markup=get_main_menu(),
        )


@router.callback_query(F.data.startswith("do_pay_payment_"))
async def do_pay_payment_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    try:
        payment_id = int(callback.data.replace("do_pay_payment_", ""))
    except ValueError:
        return

    data = await state.get_data()
    origin_manage = bool(data.get("pay_origin_manage", False))

    db = next(get_db())
    paid = PaymentService.pay_payment_and_record_expense(db, payment_id, callback.from_user.id)

    await state.clear()

    payments = PaymentService.get_future_payments(db, callback.from_user.id, limit=30)
    if origin_manage or _is_manage_future_payments_message(callback.message.text if callback.message else None):
        if not payments:
            await callback.message.edit_text(
                "Kelajakdagi to'lovlar topilmadi.",
                reply_markup=get_manage_menu(),
            )
        else:
            await callback.message.edit_text(
                "Kelajakdagi to'lovlar:\n\nTo'lovni ko'rish uchun tanlang:",
                reply_markup=get_manage_future_payments_list_keyboard(payments),
            )
        return

    if paid:
        await callback.message.edit_text(
            "✅ To'lov belgilandi va harajatlar ro'yxatiga qo'shildi.",
            reply_markup=get_main_menu(),
        )
    else:
        await callback.message.edit_text(
            "❌ To'lov topilmadi yoki allaqachon bajarilgan.",
            reply_markup=get_main_menu(),
        )


@router.callback_query(F.data.startswith("cancel_pay_payment_"))
async def cancel_pay_payment_callback(callback: CallbackQuery):
    await callback.answer()
    db = next(get_db())
    payments = PaymentService.get_future_payments(db, callback.from_user.id, limit=30)
    if payments:
        await callback.message.edit_text(
            "Kelajakdagi to'lovlar:\n\nTo'lovni ko'rish uchun tanlang:",
            reply_markup=get_manage_future_payments_list_keyboard(payments),
        )
    else:
        await callback.message.edit_text(
            "Amal bekor qilindi.",
            reply_markup=get_main_menu(),
        )


@router.callback_query(F.data.startswith("skip_payment_"))
async def skip_payment_callback(callback: CallbackQuery):
    await callback.answer()
    try:
        payment_id = int(callback.data.replace("skip_payment_", ""))
    except ValueError:
        return

    db = next(get_db())
    skipped = PaymentService.skip_payment_occurrence(db, payment_id, callback.from_user.id)

    payments = PaymentService.get_future_payments(db, callback.from_user.id, limit=30)
    if payments and callback.message and callback.message.text and "Kelajakdagi to'lovlar" in callback.message.text:
        await callback.message.edit_text(
            "Kelajakdagi to'lovlar (o'chirish uchun tanlang):",
            reply_markup=get_manage_future_payments_keyboard(payments),
        )
        return

    if skipped:
        await callback.message.edit_text(
            "⏭ To'lov shu davr uchun o'tkazib yuborildi.",
            reply_markup=get_main_menu(),
        )
    else:
        await callback.message.edit_text(
            "❌ To'lov topilmadi yoki allaqachon bajarilgan.",
            reply_markup=get_main_menu(),
        )

@router.callback_query(F.data.startswith("confirm_delete_payment_"))
async def confirm_delete_payment_callback(callback: CallbackQuery):
    await callback.answer()
    try:
        payment_id = int(callback.data.replace("confirm_delete_payment_", ""))
    except ValueError:
        return

    db = next(get_db())
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == callback.from_user.id,
        Payment.is_paid == False,
    ).first()
    if not payment:
        await callback.message.edit_text(
            "❌ To'lov topilmadi yoki allaqachon bajarilgan.",
            reply_markup=get_manage_menu(),
        )
        return

    msg = "🗑 To'lovni o'chirishni tasdiqlaysizmi?\n\n"
    msg += f"📝 {payment.description}\n"
    msg += f"💰 {payment.amount:,.0f} so'm\n"
    msg += f"📅 Sana: {payment.due_date.strftime('%d.%m.%Y')}"

    await callback.message.edit_text(
        msg,
        reply_markup=get_confirm_delete_payment_keyboard(payment_id),
    )


@router.callback_query(F.data.startswith("do_delete_payment_"))
async def do_delete_payment_callback(callback: CallbackQuery):
    await callback.answer()
    try:
        payment_id = int(callback.data.replace("do_delete_payment_", ""))
    except ValueError:
        return

    db = next(get_db())
    deleted = PaymentService.delete_payment(db, callback.from_user.id, payment_id)

    payments = PaymentService.get_future_payments(db, callback.from_user.id, limit=30)
    if payments:
        await callback.message.edit_text(
            "Kelajakdagi to'lovlar:\n\nTo'lovni ko'rish uchun tanlang:",
            reply_markup=get_manage_future_payments_list_keyboard(payments),
        )
        return

    text = "Kelajakdagi to'lovlar topilmadi." if deleted else "To'lov topilmadi yoki o'chirish mumkin emas."
    await callback.message.edit_text(
        text,
        reply_markup=get_manage_menu(),
    )


@router.callback_query(F.data.startswith("cancel_delete_payment_"))
async def cancel_delete_payment_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    origin_manage = bool(data.get("pay_origin_manage", False))
    await state.clear()

    db = next(get_db())
    payments = PaymentService.get_future_payments(db, callback.from_user.id, limit=30)
    if origin_manage:
        if payments:
            await callback.message.edit_text(
                "Kelajakdagi to'lovlar:\n\nTo'lovni ko'rish uchun tanlang:",
                reply_markup=get_manage_future_payments_list_keyboard(payments),
            )
        else:
            await callback.message.edit_text(
                "Kelajakdagi to'lovlar topilmadi.",
                reply_markup=get_manage_menu(),
            )
        return

    if payments:
        await callback.message.edit_text(
            "Kelajakdagi to'lovlar:\n\nTo'lovni ko'rish uchun tanlang:",
            reply_markup=get_manage_future_payments_list_keyboard(payments),
        )
    else:
        await callback.message.edit_text(
            "Amal bekor qilindi.",
            reply_markup=get_main_menu(),
        )