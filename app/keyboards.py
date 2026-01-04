from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Harajat qo'shish", callback_data="add_expense"),
        InlineKeyboardButton(text="💳 To'lov qo'shish", callback_data="add_payment")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Hisobotlar", callback_data="reports_menu"),
        InlineKeyboardButton(text="🔔 Kelgusi to'lovlar", callback_data="upcoming_payments")
    )
    builder.row(
        InlineKeyboardButton(text="🧾 Boshqarish", callback_data="manage_menu"),
        InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="settings"),
        InlineKeyboardButton(text="ℹ️ Yordam", callback_data="help")
    )
    return builder.as_markup()

def get_upcoming_payments_keyboard(payments: list):
    builder = InlineKeyboardBuilder()

    for p in payments:
        try:
            amount_text = f"{p.amount:,.0f}".replace(",", " ")
        except Exception:
            amount_text = ""

        try:
            date_text = p.due_date.strftime("%d.%m.%Y")
        except Exception:
            date_text = ""

        desc_text = getattr(p, "description", "") or ""
        if len(desc_text) > 20:
            desc_text = desc_text[:20] + "…"

        builder.row(
            InlineKeyboardButton(
                text=f"📌 {date_text} | {amount_text} | {desc_text}",
                callback_data=f"view_upcoming_payment_{p.id}",
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="upcoming_payments"),
        InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu"),
    )
    return builder.as_markup()

def get_upcoming_payment_detail_keyboard(payment_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ To'landi", callback_data=f"confirm_pay_payment_{payment_id}"),
        InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"confirm_delete_payment_{payment_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Ortga", callback_data="upcoming_payments"),
    )
    return builder.as_markup()

def get_reports_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Bugun", callback_data="today_report"),
        InlineKeyboardButton(text="📈 Kecha", callback_data="yesterday_report"),
    )
    builder.row(
        InlineKeyboardButton(text="📅 Haftalik", callback_data="weekly_report"),
        InlineKeyboardButton(text="📆 Oylik", callback_data="monthly_report"),
    )
    builder.row(
        InlineKeyboardButton(text="🎯 Yillik", callback_data="yearly_report"),
        InlineKeyboardButton(text="📊 Ixtiyoriy", callback_data="report_custom"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu"),
    )
    return builder.as_markup()

def get_manage_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🧾 Oxirgi xarajatlar", callback_data="manage_last_expenses"),
    )
    builder.row(
        InlineKeyboardButton(text="🗓 Kelajakdagi to'lovlar", callback_data="manage_future_payments"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu"),
    )
    return builder.as_markup()

def get_manage_last_expenses_keyboard(expenses: list):
    builder = InlineKeyboardBuilder()

    for exp in expenses:
        try:
            amount_text = f"{exp.amount:,.0f}".replace(",", " ")
        except Exception:
            amount_text = ""

        try:
            date_text = exp.date.strftime("%d.%m.%Y")
        except Exception:
            date_text = ""

        category_text = getattr(exp, "category", "") or ""

        builder.row(
            InlineKeyboardButton(
                text=f"🗑 {date_text} | {amount_text} | {category_text}",
                callback_data=f"delete_expense_{exp.id}",
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="manage_last_expenses"),
        InlineKeyboardButton(text="🔙 Ortga", callback_data="manage_menu"),
    )
    return builder.as_markup()

def get_manage_future_payments_keyboard(payments: list):
    builder = InlineKeyboardBuilder()

    for p in payments:
        try:
            amount_text = f"{p.amount:,.0f}".replace(",", " ")
        except Exception:
            amount_text = ""

        try:
            date_text = p.due_date.strftime("%d.%m.%Y")
        except Exception:
            date_text = ""

        builder.row(
            InlineKeyboardButton(
                text=f"✅ {date_text} | {amount_text}",
                callback_data=f"confirm_pay_payment_{p.id}",
            ),
            InlineKeyboardButton(
                text="🗑",
                callback_data=f"confirm_delete_payment_{p.id}",
            ),
        )

    builder.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="manage_future_payments"),
        InlineKeyboardButton(text="🔙 Ortga", callback_data="manage_menu"),
    )
    return builder.as_markup()

def get_manage_future_payments_list_keyboard(payments: list):
    builder = InlineKeyboardBuilder()

    for p in payments:
        try:
            amount_text = f"{p.amount:,.0f}".replace(",", " ")
        except Exception:
            amount_text = ""

        try:
            date_text = p.due_date.strftime("%d.%m.%Y")
        except Exception:
            date_text = ""

        desc_text = getattr(p, "description", "") or ""
        if len(desc_text) > 20:
            desc_text = desc_text[:20] + "…"

        builder.row(
            InlineKeyboardButton(
                text=f"📌 {date_text} | {amount_text} | {desc_text}",
                callback_data=f"view_manage_future_payment_{p.id}",
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="manage_future_payments"),
        InlineKeyboardButton(text="🔙 Ortga", callback_data="manage_menu"),
    )
    return builder.as_markup()

def get_manage_future_payment_detail_keyboard(payment_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ To'landi", callback_data=f"confirm_pay_payment_{payment_id}"),
        InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"confirm_delete_payment_{payment_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Ortga", callback_data="manage_future_payments"),
    )
    return builder.as_markup()

def get_payment_reminder_actions_keyboard(payment_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ To'landi", callback_data=f"confirm_pay_payment_{payment_id}"),
        InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data=f"skip_payment_{payment_id}"),
    )
    return builder.as_markup()

def get_confirm_pay_payment_keyboard(payment_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Reja bo'yicha", callback_data=f"do_pay_payment_{payment_id}"),
        InlineKeyboardButton(text="✍️ Narx kiritish", callback_data=f"ask_pay_amount_{payment_id}"),
    )
    builder.row(
        InlineKeyboardButton(text="❌ Bekor", callback_data=f"cancel_pay_payment_{payment_id}"),
    )
    return builder.as_markup()

def get_confirm_custom_pay_payment_keyboard(payment_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"do_pay_payment_custom_{payment_id}"),
        InlineKeyboardButton(text="❌ Bekor", callback_data=f"cancel_pay_payment_{payment_id}"),
    )
    return builder.as_markup()

def get_confirm_delete_payment_keyboard(payment_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🗑 O'chirishni tasdiqlash", callback_data=f"do_delete_payment_{payment_id}"),
        InlineKeyboardButton(text="❌ Bekor", callback_data=f"cancel_delete_payment_{payment_id}"),
    )
    return builder.as_markup()

def get_expense_date_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Bugun", callback_data="expense_date_today"),
        InlineKeyboardButton(text="📆 Kecha", callback_data="expense_date_yesterday"),
    )
    builder.row(
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"),
    )
    return builder.as_markup()

def get_expense_type_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Kunlik", callback_data="expense_daily"),
        InlineKeyboardButton(text="📆 Haftalik", callback_data="expense_weekly")
    )
    builder.row(
        InlineKeyboardButton(text="🗓 Oylik", callback_data="expense_monthly"),
        InlineKeyboardButton(text="🎯 Yillik", callback_data="expense_yearly")
    )
    builder.row(
        InlineKeyboardButton(text="✅ Bir martalik", callback_data="expense_once"),
        InlineKeyboardButton(text="⏳ Kelajakdagi", callback_data="expense_future")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu")
    )
    return builder.as_markup()

def get_categories_keyboard():
    categories = [
        "🍽 Ovqatlanish", "☕️ Kafe/Restoran",
        "🚗 Transport", "⛽️ Yoqilg'i",
        "🏠 Uy", "💡 Kommunal",
        "📶 Internet", "📱 Aloqa",
        "🛍 Xaridlar", "🧺 Maishiy buyumlar",
        "👕 Kiyim", "👟 Oyoq kiyim",
        "💊 Sog'liq", "🦷 Stomatolog",
        "🎮 O'yin", "🎬 Ko'ngilochar",
        "💻 Texnika", "🧰 Ta'mirlash",
        "✈️ Sayohat", "🚕 Taksi",
        "📚 Ta'lim", "📌 Obuna/Servis",
        "👶 Farzandlar", "🐾 Uy hayvonlari",
        "🎁 Sovg'a", "🤝 Hayriya",
        "⚽️ Sport", "🧴 Go'zallik",
        "💳 Kredit/Qarz", "🧾 Soliq/Jarima",
        "Boshqa"
    ]
    
    builder = InlineKeyboardBuilder()
    for i in range(0, len(categories), 2):
        if i + 1 < len(categories):
            builder.row(
                InlineKeyboardButton(text=categories[i], callback_data=f"cat_{categories[i]}"),
                InlineKeyboardButton(text=categories[i+1], callback_data=f"cat_{categories[i+1]}")
            )
        else:
            builder.row(InlineKeyboardButton(text=categories[i], callback_data=f"cat_{categories[i]}"))
    
    builder.row(InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu"))
    return builder.as_markup()

def get_payment_frequency_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📆 Haftalik", callback_data="payment_weekly"),
        InlineKeyboardButton(text="📅 Har 2 haftada", callback_data="payment_biweekly"),
    )
    builder.row(
        InlineKeyboardButton(text="🗓 Oylik", callback_data="payment_monthly"),
        InlineKeyboardButton(text="🎯 Yillik", callback_data="payment_yearly")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Choraklik", callback_data="payment_quarterly"),
        InlineKeyboardButton(text="✅ Bir martalik", callback_data="payment_once")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu")
    )
    return builder.as_markup()

def get_weekday_keyboard():
    weekdays = [
        ("Dushanba", 0),
        ("Seshanba", 1),
        ("Chorshanba", 2),
        ("Payshanba", 3),
        ("Juma", 4),
        ("Shanba", 5),
        ("Yakshanba", 6),
    ]
 
    builder = InlineKeyboardBuilder()
    for i in range(0, len(weekdays), 2):
        name1, val1 = weekdays[i]
        if i + 1 < len(weekdays):
            name2, val2 = weekdays[i + 1]
            builder.row(
                InlineKeyboardButton(text=name1, callback_data=f"weekday_{val1}"),
                InlineKeyboardButton(text=name2, callback_data=f"weekday_{val2}"),
            )
        else:
            builder.row(InlineKeyboardButton(text=name1, callback_data=f"weekday_{val1}"))
 
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"))
    return builder.as_markup()

def get_day_of_month_keyboard():
    builder = InlineKeyboardBuilder()
 
    # 1..31
    for day in range(1, 32):
        builder.button(text=str(day), callback_data=f"monthday_{day}")
    builder.adjust(7)
 
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"))
    return builder.as_markup()

def get_report_period_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Bugun", callback_data="report_today"),
        InlineKeyboardButton(text="📆 Kecha", callback_data="report_yesterday")
    )
    builder.row(
        InlineKeyboardButton(text="🗓 Hafta", callback_data="report_week"),
        InlineKeyboardButton(text="🎯 Oy", callback_data="report_month")
    )
    builder.row(
        InlineKeyboardButton(text="📈 Yil", callback_data="report_year"),
        InlineKeyboardButton(text="📊 Ixtiyoriy", callback_data="report_custom")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu")
    )
    return builder.as_markup()

def get_confirmation_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Ha", callback_data="confirm_yes"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data="confirm_no")
    )
    return builder.as_markup()

def get_settings_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🕐 Vaqt zonasini o'zgartirish", callback_data="change_timezone"),
        InlineKeyboardButton(text="📊 Kategoriyalarni boshqarish", callback_data="manage_categories")
    )
    builder.row(
        InlineKeyboardButton(text="🔔 Eslatmalarni sozlash", callback_data="notification_settings"),
        InlineKeyboardButton(text="📁 Hisobot formatini tanlash", callback_data="report_format")
    )
    builder.row(InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu"))
    return builder.as_markup()

def get_cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"))
    return builder.as_markup()

def get_skip_expense_description_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭ Izohni o'tkazib yuborish", callback_data="skip_expense_description"),
    )
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"))
    return builder.as_markup()

def get_skip_payment_description_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭ Izohni o'tkazib yuborish", callback_data="skip_payment_description"),
    )
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"))
    return builder.as_markup()

def get_skip_payment_occurrences_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data="skip_payment_occurrences"),
    )
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"))
    return builder.as_markup()