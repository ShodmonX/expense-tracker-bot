from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

def get_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="💰 Xarajat qo'shish"),
        KeyboardButton(text="💵 Kirim qo'shish")
    )
    builder.row(
        KeyboardButton(text="💳 To'lov qo'shish"),
        KeyboardButton(text="📊 Hisobotlar")
    )
    builder.row(
        KeyboardButton(text="💰 Balans"),
        KeyboardButton(text="🔔 Kelgusi to'lovlar")
    )
    builder.row(
        KeyboardButton(text="🧾 Boshqarish"),
        KeyboardButton(text="⚙️ Sozlamalar"),
        KeyboardButton(text="ℹ️ Yordam")
    )
    return builder.as_markup(resize_keyboard=True)

def get_income_categories_keyboard():
    builder = InlineKeyboardBuilder()
    categories = [
        "Maosh", "Biznes", "Investitsiya", "Gift", "Bonus", 
        "Ijaraga berish", "Qo'shimcha ish", "Boshqa"
    ]
    
    # Create rows with 2 buttons each
    for i in range(0, len(categories), 2):
        row_buttons = []
        row_buttons.append(InlineKeyboardButton(
            text=categories[i], 
            callback_data=f"income_category_{categories[i]}"
        ))
        if i + 1 < len(categories):
            row_buttons.append(InlineKeyboardButton(
                text=categories[i + 1], 
                callback_data=f"income_category_{categories[i + 1]}"
            ))
        builder.row(*row_buttons)
    
    return builder.as_markup()

def get_balance_summary_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="balance_summary"),
        InlineKeyboardButton(text="📋 Batafsil", callback_data="balance_detail")
    )
    builder.row(
        InlineKeyboardButton(text="📊 Yillik xulosa", callback_data="balance_yearly"),
        InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu")
    )
    return builder.as_markup()

def get_balance_detail_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="balance_detail"),
        InlineKeyboardButton(text="📊 Xulosa", callback_data="balance_summary")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu")
    )
    return builder.as_markup()

def get_income_summary_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="income_summary"),
        InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu"),
    )
    return builder.as_markup()

def get_monthly_payment_summary_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="monthly_payment_summary"),
        InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu"),
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
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📊 Bugun"),
        KeyboardButton(text="📈 Kecha")
    )
    builder.row(
        KeyboardButton(text="📅 Haftalik"),
        KeyboardButton(text="📆 Oylik")
    )
    builder.row(
        KeyboardButton(text="🎯 Yillik"),
        KeyboardButton(text="📊 Ixtiyoriy")
    )
    builder.row(
        KeyboardButton(text="🔙 Ortga")
    )
    return builder.as_markup(resize_keyboard=True)

def get_manage_menu(is_admin: bool = False):
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🧾 Oxirgi xarajatlar")
    )
    builder.row(
        KeyboardButton(text="🗓 Kelajakdagi to'lovlar")
    )
    if is_admin:
        builder.row(
            KeyboardButton(text="🗄 DB backup")
        )
    builder.row(
        KeyboardButton(text="🔙 Ortga")
    )
    return builder.as_markup(resize_keyboard=True)

def get_backup_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💾 Manual backup", callback_data="adb:mk")
    )
    builder.row(
        InlineKeyboardButton(text="📂 Ro'yxat", callback_data="adb:ls:kind"),
        InlineKeyboardButton(text="♻️ Restore", callback_data="adb:rs:kind"),
    )
    builder.row(
        InlineKeyboardButton(text="🗑 O'chirish", callback_data="adb:rm:kind"),
        InlineKeyboardButton(text="🧹 Auto cleanup", callback_data="adb:cln:ask"),
    )
    builder.row(
        InlineKeyboardButton(text="ℹ️ Auto status", callback_data="adb:st")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Ortga", callback_data="adb:exit")
    )
    return builder.as_markup()

def get_backup_kind_keyboard(section: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📁 Barchasi", callback_data=f"adb:k:{section}:a:0")
    )
    builder.row(
        InlineKeyboardButton(text="🤖 Auto", callback_data=f"adb:k:{section}:u:0"),
        InlineKeyboardButton(text="👤 Manual", callback_data=f"adb:k:{section}:m:0"),
    )
    builder.row(
        InlineKeyboardButton(text="🛟 Pre-restore", callback_data=f"adb:k:{section}:p:0")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Menyu", callback_data="adb:menu")
    )
    return builder.as_markup()

def get_backup_list_keyboard(items: list, section: str, kind_code: str, page: int, total_pages: int):
    builder = InlineKeyboardBuilder()

    if section in {"r", "d"}:
        action_callback = "adb:rc:" if section == "r" else "adb:dc:"
        action_prefix = "♻️" if section == "r" else "🗑"
        for item in items:
            builder.row(
                InlineKeyboardButton(
                    text=f"{action_prefix} {item.filename}",
                    callback_data=f"{action_callback}{item.filename}",
                )
            )

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Oldingi",
                callback_data=f"adb:p:{section}:{kind_code}:{page - 1}",
            )
        )
    if page + 1 < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Keyingi ➡️",
                callback_data=f"adb:p:{section}:{kind_code}:{page + 1}",
            )
        )
    if nav_buttons:
        builder.row(*nav_buttons)

    section_menu_map = {
        "l": "adb:ls:kind",
        "r": "adb:rs:kind",
        "d": "adb:rm:kind",
    }

    builder.row(
        InlineKeyboardButton(
            text="🔎 Turini o'zgartirish",
            callback_data=section_menu_map.get(section, "adb:menu"),
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Menyu", callback_data="adb:menu")
    )
    return builder.as_markup()

def get_backup_confirm_keyboard(action: str, filename: str = ""):
    builder = InlineKeyboardBuilder()

    if action == "restore":
        confirm_data = f"adb:r:{filename}"
        confirm_label = "♻️ Restore qilish"
    elif action == "delete":
        confirm_data = f"adb:d:{filename}"
        confirm_label = "🗑 O'chirish"
    else:
        confirm_data = "adb:cln:run"
        confirm_label = "🧹 Tozalash"

    builder.row(
        InlineKeyboardButton(text=confirm_label, callback_data=confirm_data),
        InlineKeyboardButton(text="❌ Bekor", callback_data="adb:menu"),
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
        InlineKeyboardButton(text="📅 Bugun", callback_data="today_report"),
        InlineKeyboardButton(text="📆 Kecha", callback_data="yesterday_report")
    )
    builder.row(
        InlineKeyboardButton(text="🗓 Hafta", callback_data="weekly_report"),
        InlineKeyboardButton(text="🎯 Oy", callback_data="monthly_report")
    )
    builder.row(
        InlineKeyboardButton(text="📈 Yil", callback_data="yearly_report"),
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

def get_settings_keyboard(
    report_format: str,
    daily_reminder_enabled: bool,
    overdue_reminder_enabled: bool,
    daily_summary_enabled: bool,
):
    normalized_format = "PDF" if (report_format or "").lower() == "pdf" else "XLSX"
    daily_status = "✅" if daily_reminder_enabled else "❌"
    overdue_status = "✅" if overdue_reminder_enabled else "❌"
    summary_status = "✅" if daily_summary_enabled else "❌"

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌐 Vaqt zonasi", callback_data="settings:timezone"),
    )
    builder.row(
        InlineKeyboardButton(
            text=f"📁 Hisobot formati: {normalized_format}",
            callback_data="settings:format",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"🔔 Kunlik eslatma: {daily_status}",
            callback_data="settings:toggle:daily",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"🚨 Overdue eslatma: {overdue_status}",
            callback_data="settings:toggle:overdue",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"📊 Kunlik hisobot: {summary_status}",
            callback_data="settings:toggle:summary",
        )
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="settings:menu"),
        InlineKeyboardButton(text="🔙 Ortga", callback_data="settings:close"),
    )
    return builder.as_markup()


def get_report_format_keyboard(current_format: str):
    normalized = (current_format or "").strip().lower()
    xlsx_mark = "✅ " if normalized != "pdf" else ""
    pdf_mark = "✅ " if normalized == "pdf" else ""

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text=f"{xlsx_mark}XLSX",
            callback_data="settings:fmt:set:xlsx",
        ),
        InlineKeyboardButton(
            text=f"{pdf_mark}PDF",
            callback_data="settings:fmt:set:pdf",
        ),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Sozlamalar", callback_data="settings:menu"),
    )
    return builder.as_markup()


def get_timezone_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇺🇿 Asia/Tashkent", callback_data="settings:tz:set:tashkent"),
    )
    builder.row(
        InlineKeyboardButton(text="🇹🇷 Europe/Istanbul", callback_data="settings:tz:set:istanbul"),
        InlineKeyboardButton(text="🇦🇪 Asia/Dubai", callback_data="settings:tz:set:dubai"),
    )
    builder.row(
        InlineKeyboardButton(text="🇪🇺 Europe/Moscow", callback_data="settings:tz:set:moscow"),
        InlineKeyboardButton(text="🌍 UTC", callback_data="settings:tz:set:utc"),
    )
    builder.row(
        InlineKeyboardButton(text="✍️ Qo'lda kiritish", callback_data="settings:tz:custom"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Sozlamalar", callback_data="settings:menu"),
    )
    return builder.as_markup()

def get_cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"))
    return builder.as_markup()

def get_today_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 Bugun", callback_data="use_today_date"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"),
    )
    return builder.as_markup()

def get_skip_description_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭ Izohni o'tkazib yuborish", callback_data="skip_income_description"),
    )
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


def get_bank_description_choice_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Shu izohni qoldirish", callback_data="bank_desc_keep"),
    )
    builder.row(
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"),
    )
    return builder.as_markup()
