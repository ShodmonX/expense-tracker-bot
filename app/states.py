from aiogram.fsm.state import State, StatesGroup

class ExpenseStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()
    waiting_for_description = State()
    waiting_for_date = State()
    waiting_for_type = State()

class PaymentStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()
    waiting_for_description = State()
    waiting_for_date = State()
    waiting_for_frequency = State()
    waiting_for_weekday = State()
    waiting_for_day_of_month = State()
    waiting_for_pay_amount = State()
    waiting_for_occurrences = State()

class ReportStates(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_end_date = State()

class SettingsStates(StatesGroup):
    waiting_for_timezone = State()