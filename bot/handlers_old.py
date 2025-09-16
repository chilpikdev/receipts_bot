import re
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from django.core.files.base import ContentFile
from django.utils import timezone
from asgiref.sync import sync_to_async

from .database import (
    get_or_create_user, get_user, save_user, get_active_branches,
    get_branch, create_receipt, save_receipt_file, get_bot_settings
)
from .keyboards import (
    get_language_keyboard, get_contact_keyboard, get_subscription_keyboard,
    get_branches_keyboard, get_main_menu_keyboard, get_back_keyboard
)
from .translations import get_text

router = Router()


class UserStates(StatesGroup):
    waiting_for_contact = State()
    waiting_for_instagram = State()
    waiting_for_subscription = State()
    waiting_for_branch = State()
    waiting_for_receipt = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    await state.clear()
    
    # Check if user exists
    user, created = await get_or_create_user(
        telegram_id=message.from_user.id,
        defaults={
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_name': message.from_user.last_name,
        }
    )
    
    if created or not user.language:
        # New user or user without language - show language selection
        await message.answer(
            get_text('start_message'),
            reply_markup=get_language_keyboard()
        )
    else:
        # Existing user - show main menu
        await show_main_menu(message, user.language)


@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery, state: FSMContext):
    """Process language selection"""
    language = callback.data.split("_")[1]
    
    # Update user language
    user = await get_user(telegram_id=callback.from_user.id)
    user.language = language
    await save_user(user)
    
    await callback.message.edit_text(get_text('language_selected', language))
    
    # Check if user has contact info
    if not user.phone_number:
        await callback.message.answer(
            get_text('share_contact', language),
            reply_markup=get_contact_keyboard(language)
        )
        await state.set_state(UserStates.waiting_for_contact)
    else:
        await show_main_menu(callback.message, language)
    
    await callback.answer()


@router.message(F.content_type == ContentType.CONTACT, StateFilter(UserStates.waiting_for_contact))
async def process_contact(message: Message, state: FSMContext):
    """Process contact sharing"""
    if message.contact.user_id != message.from_user.id:
        return
    
    user = await get_user(telegram_id=message.from_user.id)
    user.phone_number = message.contact.phone_number
    await save_user(user)
    
    await message.answer(
        get_text('registration_complete', user.language),
        reply_markup=get_main_menu_keyboard(user.language)
    )
    
    # Ask for Instagram username
    await message.answer(get_text('instagram_username', user.language))
    await state.set_state(UserStates.waiting_for_instagram)


@router.message(StateFilter(UserStates.waiting_for_instagram))
async def process_instagram_username(message: Message, state: FSMContext):
    """Process Instagram username"""
    username = message.text.strip()
    
    if not username.startswith('@') or len(username) < 2:
        user = BotUser.objects.get(telegram_id=message.from_user.id)
        await message.answer(get_text('invalid_instagram', user.language))
        return
    
    user = BotUser.objects.get(telegram_id=message.from_user.id)
    user.instagram_username = username
    user.save()
    
    # Get Instagram profile URL from settings
    bot_settings = BotSettings.objects.first()
    instagram_url = bot_settings.instagram_profile_url if bot_settings else "https://instagram.com/"
    
    await message.answer(
        get_text('instagram_follow', user.language) + f"\n{instagram_url}",
        reply_markup=get_subscription_keyboard(user.language)
    )
    await state.set_state(UserStates.waiting_for_subscription)


@router.callback_query(F.data == "instagram_subscribed", StateFilter(UserStates.waiting_for_subscription))
async def process_instagram_subscription(callback: CallbackQuery, state: FSMContext):
    """Process Instagram subscription confirmation"""
    user = BotUser.objects.get(telegram_id=callback.from_user.id)
    user.is_subscribed_instagram = True
    user.save()
    
    await callback.message.edit_text(get_text('subscription_confirmed', user.language))
    await show_main_menu(callback.message, user.language)
    await state.clear()
    await callback.answer()


@router.message(F.text.in_(["📄 Chek yuborish", "📄 Chek jiberew"]))
async def start_receipt_process(message: Message, state: FSMContext):
    """Start receipt submission process"""
    user = BotUser.objects.get(telegram_id=message.from_user.id)
    
    # Get active branches
    branches = Branch.objects.filter(is_active=True)
    
    if not branches:
        await message.answer("No branches available")
        return
    
    await message.answer(
        get_text('choose_branch', user.language),
        reply_markup=get_branches_keyboard(list(branches), user.language)
    )
    await state.set_state(UserStates.waiting_for_branch)


@router.callback_query(F.data.startswith("branch_"), StateFilter(UserStates.waiting_for_branch))
async def process_branch_selection(callback: CallbackQuery, state: FSMContext):
    """Process branch selection"""
    branch_id = int(callback.data.split("_")[1])
    branch = Branch.objects.get(id=branch_id)
    
    user = BotUser.objects.get(telegram_id=callback.from_user.id)
    
    await state.update_data(branch_id=branch_id)
    
    await callback.message.edit_text(
        f"{get_text('choose_branch', user.language)}\n✅ {branch.get_name(user.language)}"
    )
    
    await callback.message.answer(
        get_text('send_receipt', user.language),
        reply_markup=get_back_keyboard(user.language)
    )
    await state.set_state(UserStates.waiting_for_receipt)
    await callback.answer()


@router.message(F.content_type.in_([ContentType.DOCUMENT, ContentType.PHOTO]), StateFilter(UserStates.waiting_for_receipt))
async def process_receipt(message: Message, state: FSMContext):
    """Process receipt file"""
    user = BotUser.objects.get(telegram_id=message.from_user.id)
    data = await state.get_data()
    branch_id = data.get('branch_id')
    
    if not branch_id:
        await message.answer(get_text('select_branch_first', user.language))
        return
    
    branch = Branch.objects.get(id=branch_id)
    
    # Get file info
    if message.document:
        file_info = message.document
        file_name = message.document.file_name
    else:
        file_info = message.photo[-1]  # Get highest resolution
        file_name = f"photo_{message.photo[-1].file_id}.jpg"
    
    # Check file size (2MB limit)
    if file_info.file_size > 2 * 1024 * 1024:
        await message.answer(get_text('file_too_large', user.language))
        return
    
    # Check file extension
    if message.document:
        allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png']
        file_extension = file_name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            await message.answer(get_text('invalid_file_format', user.language))
            return
    
    # Download file
    file = await message.bot.get_file(file_info.file_id)
    file_data = await message.bot.download_file(file.file_path)
    
    # Save receipt to database
    receipt = Receipt.objects.create(
        user=user,
        branch=branch,
        file_size=file_info.file_size
    )
    
    # Save file
    receipt.file.save(
        file_name,
        ContentFile(file_data.read()),
        save=True
    )
    
    await message.answer(get_text('receipt_received', user.language))
    await show_main_menu(message, user.language)
    await state.clear()


@router.message(F.text.in_(["🌐 Tilni o'zgartirish", "🌐 Tildi ózgertew"]))
async def change_language(message: Message, state: FSMContext):
    """Handle language change"""
    await state.clear()
    await message.answer(
        get_text('choose_language'),
        reply_markup=get_language_keyboard()
    )


@router.message(F.text.in_(["🔙 Asosiy menyu", "🔙 Basqı menyu"]))
async def back_to_menu(message: Message, state: FSMContext):
    """Handle back to menu"""
    await state.clear()
    user = BotUser.objects.get(telegram_id=message.from_user.id)
    await show_main_menu(message, user.language)


async def show_main_menu(message: Message, language: str = 'uz'):
    """Show main menu"""
    await message.answer(
        get_text('start_message', language),
        reply_markup=get_main_menu_keyboard(language)
    )


# Notification functions for admin
async def notify_user_receipt_status(bot, user_id: int, status: str, reason: str = None):
    """Notify user about receipt status change"""
    try:
        user = BotUser.objects.get(telegram_id=user_id)
        if status == 'approved':
            text = get_text('receipt_approved', user.language)
        elif status == 'rejected':
            text = get_text('receipt_rejected', user.language, reason=reason or "")
        else:
            return
        
        await bot.send_message(user_id, text)
    except Exception as e:
        print(f"Error notifying user {user_id}: {e}")