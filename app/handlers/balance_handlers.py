from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from datetime import date

from keyboards import *
from services.balance_service import BalanceService
from database import run_db

router = Router()

@router.message(F.text == "💰 Balans")
async def show_balance_summary_message(message: Message):
    if message.from_user is None:
        await message.answer("Iltimos, botga kirish qiling.")
        return
    balance = await run_db(BalanceService.get_current_balance, message.from_user.id)
    
    # Format balance summary message
    message_text = f"💰 **{balance['month_name']} oylik balans xulosasi**\n\n"
    
    # Income section
    message_text += f"💵 **KIRIMLAR:**\n"
    message_text += f"   Jami kirim: {balance['total_income']:,.0f} so'm\n"
    message_text += f"   Kirimlar soni: {balance['income_count']} ta\n"
    
    if balance['carry_over'] > 0:
        message_text += f"   O'tgan oydan qolgan: {balance['carry_over']:,.0f} so'm\n"
    
    # Expense section
    message_text += f"\n💸 **XARAJATLAR:**\n"
    message_text += f"   Jami xarajat: {balance['total_expenses']:,.0f} so'm\n"
    message_text += f"   Xarajatlar soni: {balance['expense_count']} ta\n"
    
    # Balance section
    message_text += f"\n📊 **BALANS:**\n"
    if balance['available_balance'] >= 0:
        message_text += f"   ✅ Mavjud mablag': {balance['available_balance']:,.0f} so'm\n"
    else:
        message_text += f"   ❌ Kamomad: {abs(balance['available_balance']):,.0f} so'm\n"
    
    message_text += f"\n🔄 **Keyingi oy boshlang'ich balans:** {balance['next_month_starting_balance']:,.0f} so'm"
    
    # Add recent transactions summary
    if balance['incomes'] or balance['expenses']:
        message_text += f"\n\n**Oxirgi operatsiyalar:**\n"
        
        # Show last 3 incomes
        for i, income in enumerate(balance['incomes'][:3], 1):
            amount_text = f"{income.amount:,.0f}".replace(",", " ")
            date_text = income.date.strftime("%d.%m")
            category = income.category or "Kirim"
            message_text += f"   💵 {date_text} | {amount_text} | {category}\n"
        
        # Show last 3 expenses
        for i, expense in enumerate(balance['expenses'][:3], 1):
            amount_text = f"{expense.amount:,.0f}".replace(",", " ")
            date_text = expense.date.strftime("%d.%m")
            category = expense.category or "Xarajat"
            message_text += f"   💸 {date_text} | {amount_text} | {category}\n"
    
    await message.answer(
        message_text,
        reply_markup=get_balance_summary_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "balance_summary")
async def show_balance_summary(callback: CallbackQuery):
    await callback.answer()
    balance = await run_db(BalanceService.get_current_balance, callback.from_user.id)
    
    # Format balance summary message
    message_text = f"💰 **{balance['month_name']} oylik balans xulosasi**\n\n"
    
    # Income section
    message_text += f"💵 **KIRIMLAR:**\n"
    message_text += f"   Jami kirim: {balance['total_income']:,.0f} so'm\n"
    message_text += f"   Kirimlar soni: {balance['income_count']} ta\n"
    
    if balance['carry_over'] > 0:
        message_text += f"   O'tgan oydan qolgan: {balance['carry_over']:,.0f} so'm\n"
    
    # Expense section
    message_text += f"\n💸 **XARAJATLAR:**\n"
    message_text += f"   Jami xarajat: {balance['total_expenses']:,.0f} so'm\n"
    message_text += f"   Xarajatlar soni: {balance['expense_count']} ta\n"
    
    # Balance section
    message_text += f"\n📊 **BALANS:**\n"
    if balance['available_balance'] >= 0:
        message_text += f"   ✅ Mavjud mablag': {balance['available_balance']:,.0f} so'm\n"
    else:
        message_text += f"   ❌ Kamomad: {abs(balance['available_balance']):,.0f} so'm\n"
    
    message_text += f"\n🔄 **Keyingi oy boshlang'ich balans:** {balance['next_month_starting_balance']:,.0f} so'm"
    
    # Add recent transactions summary
    if balance['incomes'] or balance['expenses']:
        message_text += f"\n\n**Oxirgi operatsiyalar:**\n"
        
        # Show last 3 incomes
        for i, income in enumerate(balance['incomes'][:3], 1):
            amount_text = f"{income.amount:,.0f}".replace(",", " ")
            date_text = income.date.strftime("%d.%m")
            message_text += f"💵 {date_text} | {amount_text} so'm | {income.category}\n"
        
        # Show last 3 expenses
        for i, expense in enumerate(balance['expenses'][:3], 1):
            amount_text = f"{expense.amount:,.0f}".replace(",", " ")
            date_text = expense.date.strftime("%d.%m")
            message_text += f"💸 {date_text} | {amount_text} so'm | {expense.category}\n"
    
    if callback.message is None:
        await callback.answer("Xabarni ko'rish mumkin emas.")
        return
    await callback.message.answer(
        message_text,
        reply_markup=get_balance_summary_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "balance_yearly")
async def show_yearly_balance(callback: CallbackQuery):
    await callback.answer()
    yearly_balance = await run_db(BalanceService.get_yearly_balance_summary, callback.from_user.id)
    
    message_text = f"📊 **{yearly_balance['year']} yillik balans xulosasi**\n\n"
    message_text += f"💵 Jami yillik kirim: {yearly_balance['total_yearly_income']:,.0f} so'm\n"
    message_text += f"💸 Jami yillik xarajat: {yearly_balance['total_yearly_expenses']:,.0f} so'm\n"
    message_text += f"📊 Yillik balans: {yearly_balance['total_yearly_balance']:,.0f} so'm\n\n"
    
    message_text += "**Oylik ko'rsatkichlar:**\n"
    for monthly in yearly_balance['monthly_summaries']:
        month_balance = monthly['available_balance']
        if month_balance >= 0:
            status = "✅"
        else:
            status = "❌"
        message_text += f"{status} {monthly['month_name']}: {month_balance:,.0f} so'm\n"
    if callback.message is None:
        await callback.answer("Xabarni ko'rish mumkin emas.")
        return
    await callback.message.answer(
        message_text,
        reply_markup=get_balance_summary_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "balance_detail")
async def show_balance_detail(callback: CallbackQuery):
    await callback.answer()
    balance = await run_db(BalanceService.get_current_balance, callback.from_user.id)
    
    message_text = f"📋 **{balance['month_name']} batafsil balans**\n\n"
    
    # Detailed income list
    message_text += "💵 **KIRIMLAR DETALI:**\n"
    if balance['incomes']:
        for i, income in enumerate(balance['incomes'], 1):
            amount_text = f"{income.amount:,.0f}".replace(",", " ")
            date_text = income.date.strftime("%d.%m.%Y")
            message_text += f"{i}. 📅 {date_text} | 💵 {amount_text} so'm\n"
            message_text += f"   📂 {income.category} | 📝 {income.description}\n"
    else:
        message_text += "   Bu oy kirimlar kiritilmagan.\n"
    
    # Detailed expense list
    message_text += "\n💸 **XARAJATLAR DETALI:**\n"
    if balance['expenses']:
        for i, expense in enumerate(balance['expenses'], 1):
            amount_text = f"{expense.amount:,.0f}".replace(",", " ")
            date_text = expense.date.strftime("%d.%m.%Y")
            message_text += f"{i}. 📅 {date_text} | 💸 {amount_text} so'm\n"
            message_text += f"   📂 {expense.category} | 📝 {expense.description}\n"
    else:
        message_text += "   Bu oy xarajatlar kiritilmagan.\n"
    
    # Summary
    message_text += f"\n📊 **JAMI:**\n"
    message_text += f"💵 Kirimlar: {balance['total_income']:,.0f} so'm ({balance['income_count']} ta)\n"
    message_text += f"💸 Xarajatlar: {balance['total_expenses']:,.0f} so'm ({balance['expense_count']} ta)\n"
    message_text += f"📊 Balans: {balance['available_balance']:,.0f} so'm\n"
    
    if callback.message is None:
        await callback.answer("Xabarni ko'rish mumkin emas.")
        return
    await callback.message.answer(
        message_text,
        reply_markup=get_balance_detail_keyboard(),
        parse_mode="Markdown"
    )
