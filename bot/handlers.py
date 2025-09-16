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


def is_user_fully_registered(user) -> bool:
    """Check if user has completed all registration steps"""
    return all([
        user.language,
        user.phone_number, 
        user.instagram_username,
        user.is_subscribed_instagram
    ])


def get_next_registration_step(user):
    """Determine the next step in registration process"""
    if not user.language:
        return 'language'
    elif not user.phone_number:
        return 'contact'
    elif not user.instagram_username:
        return 'instagram'
    elif not user.is_subscribed_instagram:
        return 'subscription'
    else:
        return 'complete'


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    await state.clear()
    
    if not message.from_user:
        return
    
    # Check if user exists
    user, created = await get_or_create_user(
        telegram_id=message.from_user.id,
        defaults={
            'username': getattr(message.from_user, 'username', None),
            'first_name': getattr(message.from_user, 'first_name', None),
            'last_name': getattr(message.from_user, 'last_name', None),
        }
    )
    
    if created or not user.language:
        # New user or user without language - show language selection
        await message.answer(
            "Tilni tanlang / Tildi saylań 🌍:",
            reply_markup=get_language_keyboard()
        )
    elif is_user_fully_registered(user):
        # Fully registered user - show main menu
        await show_main_menu(message, user.language)
    else:
        # Partially registered user - continue registration from next step
        next_step = get_next_registration_step(user)
        
        if next_step == 'contact':
            await message.answer(
                get_text('share_contact', user.language),
                reply_markup=get_contact_keyboard(user.language)
            )
            await state.set_state(UserStates.waiting_for_contact)
            
        elif next_step == 'instagram':
            await message.answer(get_text('instagram_username', user.language))
            await state.set_state(UserStates.waiting_for_instagram)
            
        elif next_step == 'subscription':
            # Get Instagram profile URL from settings
            bot_settings = await get_bot_settings()
            instagram_url = bot_settings.instagram_profile_url if bot_settings else "https://instagram.com/"
            
            await message.answer(
                get_text('instagram_follow', user.language) + f"\n{instagram_url}",
                reply_markup=get_subscription_keyboard(user.language)
            )
            await state.set_state(UserStates.waiting_for_subscription)


@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery, state: FSMContext):
    """Process language selection"""
    if not callback.data or not callback.from_user:
        return
        
    language = callback.data.split("_")[1]
    
    # Update user language
    user = await get_user(telegram_id=callback.from_user.id)
    user.language = language
    await save_user(user)
    
    if callback.message:
        await callback.message.edit_text(get_text('language_selected', language))
        
        # Check what's the next step in registration
        next_step = get_next_registration_step(user)
        
        if next_step == 'contact':
            await callback.message.answer(
                get_text('share_contact', language),
                reply_markup=get_contact_keyboard(language)
            )
            await state.set_state(UserStates.waiting_for_contact)
        elif next_step == 'instagram':
            await callback.message.answer(get_text('instagram_username', language))
            await state.set_state(UserStates.waiting_for_instagram)
        elif next_step == 'subscription':
            # Get Instagram profile URL from settings
            bot_settings = await get_bot_settings()
            instagram_url = bot_settings.instagram_profile_url if bot_settings else "https://instagram.com/"
            
            await callback.message.answer(
                get_text('instagram_follow', language) + f"\n{instagram_url}",
                reply_markup=get_subscription_keyboard(language)
            )
            await state.set_state(UserStates.waiting_for_subscription)
        else:
            # User is fully registered
            await show_main_menu(callback.message, language)
    
    await callback.answer()


@router.message(F.content_type == ContentType.CONTACT, StateFilter(UserStates.waiting_for_contact))
async def process_contact(message: Message, state: FSMContext):
    """Process contact sharing"""
    if not message.contact or not message.from_user:
        return
        
    if message.contact.user_id != message.from_user.id:
        return
    
    user = await get_user(telegram_id=message.from_user.id)
    user.phone_number = message.contact.phone_number
    await save_user(user)
    
    await message.answer(
        get_text('registration_complete', user.language)
    )
    
    # Ask for Instagram username
    await message.answer(get_text('instagram_username', user.language))
    await state.set_state(UserStates.waiting_for_instagram)


@router.message(StateFilter(UserStates.waiting_for_instagram))
async def process_instagram_username(message: Message, state: FSMContext):
    """Process Instagram username"""
    if not message.text or not message.from_user:
        return
        
    username = message.text.strip()
    
    if not username.startswith('@') or len(username) < 2:
        user = await get_user(telegram_id=message.from_user.id)
        await message.answer(get_text('invalid_instagram', user.language))
        return
    
    user = await get_user(telegram_id=message.from_user.id)
    user.instagram_username = username
    await save_user(user)
    
    # Get Instagram profile URL from settings
    bot_settings = await get_bot_settings()
    instagram_url = bot_settings.instagram_profile_url if bot_settings else "https://instagram.com/"
    
    await message.answer(
        get_text('instagram_follow', user.language) + f"\n{instagram_url}",
        reply_markup=get_subscription_keyboard(user.language)
    )
    await state.set_state(UserStates.waiting_for_subscription)


@router.callback_query(F.data == "instagram_subscribed", StateFilter(UserStates.waiting_for_subscription))
async def process_instagram_subscription(callback: CallbackQuery, state: FSMContext):
    """Process Instagram subscription confirmation"""
    if not callback.from_user:
        return
        
    user = await get_user(telegram_id=callback.from_user.id)
    user.is_subscribed_instagram = True
    await save_user(user)
    
    if callback.message:
        await callback.message.edit_text(get_text('subscription_confirmed', user.language))
        await show_main_menu(callback.message, user.language)
    await state.clear()
    await callback.answer()


@router.message(F.text)
async def handle_menu_buttons(message: Message, state: FSMContext):
    """Handle menu button presses"""
    if not message.from_user or not message.text:
        return
        
    try:
        user = await get_user(telegram_id=message.from_user.id)
        if not user or not user.language:
            return
            
        text = message.text.strip()
        
        # Check for receipt submission button
        receipt_btn_text = get_text('send_receipt_btn', user.language)
        if text == receipt_btn_text:
            await start_receipt_process(message, state)
            return
            
        # Check for language change button  
        lang_btn_text = get_text('change_language', user.language)
        if text == lang_btn_text:
            await change_language(message, state)
            return
            
        # Check for back to menu button
        back_btn_text = get_text('back_to_menu', user.language)
        if text == back_btn_text:
            await back_to_menu(message, state)
            return
            
    except Exception:
        # If user not found or any error, let unrecognized handler take care of it
        pass


async def start_receipt_process(message: Message, state: FSMContext):
    """Start receipt submission process"""
    if not message.from_user:
        return
        
    user = await get_user(telegram_id=message.from_user.id)
    
    # Check if user is fully registered
    if not is_user_fully_registered(user):
        await message.answer(
            get_text('registration_incomplete', user.language)
        )
        return
    
    # Get active branches
    branches = await get_active_branches()
    
    if not branches:
        await message.answer("No branches available")
        return
    
    await message.answer(
        get_text('choose_branch', user.language),
        reply_markup=get_branches_keyboard(branches, user.language)
    )
    await state.set_state(UserStates.waiting_for_branch)


async def change_language(message: Message, state: FSMContext):
    """Handle language change"""
    await state.clear()
    
    if not message.from_user:
        return
        
    # Get current user language to show language-specific text
    user = await get_user(telegram_id=message.from_user.id)
    
    # Show language selection in current user's language
    await message.answer(
        get_text('choose_language', user.language),
        reply_markup=get_language_keyboard()
    )


async def back_to_menu(message: Message, state: FSMContext):
    """Handle back to menu"""
    if not message.from_user:
        return
        
    await state.clear()
    user = await get_user(telegram_id=message.from_user.id)
    await show_main_menu(message, user.language)


@router.callback_query(F.data.startswith("branch_"), StateFilter(UserStates.waiting_for_branch))
async def process_branch_selection(callback: CallbackQuery, state: FSMContext):
    """Process branch selection"""
    if not callback.data or not callback.from_user:
        return
        
    branch_id = int(callback.data.split("_")[1])
    branch = await get_branch(branch_id=branch_id)
    
    user = await get_user(telegram_id=callback.from_user.id)
    
    await state.update_data(branch_id=branch_id)
    
    if callback.message:
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
    if not message.from_user:
        return
        
    user = await get_user(telegram_id=message.from_user.id)
    data = await state.get_data()
    branch_id = data.get('branch_id')
    
    if not branch_id:
        await message.answer(get_text('select_branch_first', user.language))
        return
    
    branch = await get_branch(branch_id=branch_id)
    
    # Get file info
    if message.document:
        file_info = message.document
        file_name = message.document.file_name or f"document_{message.document.file_id}.pdf"
    elif message.photo:
        file_info = message.photo[-1]  # Get highest resolution
        file_name = f"photo_{message.photo[-1].file_id}.jpg"
    else:
        return
    
    # Check file size (2MB limit)
    if file_info.file_size and file_info.file_size > 2 * 1024 * 1024:
        await message.answer(get_text('file_too_large', user.language))
        return
    
    # Check file extension
    if message.document and file_name:
        allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png']
        file_extension = file_name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            await message.answer(get_text('invalid_file_format', user.language))
            return
    
    # Download file
    file = await message.bot.get_file(file_info.file_id)
    file_data = await message.bot.download_file(file.file_path)
    
    # Save receipt to database
    receipt = await create_receipt(
        user=user,
        branch=branch,
        file_size=file_info.file_size or 0
    )
    
    # Save file
    await save_receipt_file(receipt, file_name, file_data.read())
    
    await message.answer(get_text('receipt_received', user.language))
    await show_main_menu(message, user.language)
    await state.clear()


# Receipt processing continues from state handlers


async def show_main_menu(message: Message, language: str = 'uz'):
    """Show main menu"""
    await message.answer(
        get_text('start_message', language),
        reply_markup=get_main_menu_keyboard(language)
    )


@router.message()
async def handle_unrecognized_message(message: Message, state: FSMContext):
    """Handle any unrecognized messages"""
    if not message.from_user:
        return
    
    try:
        # Get user to determine language
        user = await get_user(telegram_id=message.from_user.id)
        if user and user.language:
            # Show help message in user's language
            await message.answer(
                get_text('unrecognized_message', user.language),
                reply_markup=get_main_menu_keyboard(user.language)
            )
        else:
            # User not found or no language set - show language selection
            await message.answer(
                "Tilni tanlang / Tildi saylań 🌍:",
                reply_markup=get_language_keyboard()
            )
    except Exception as e:
        # Fallback response if there's any error
        await message.answer(
            "Sorry, I didn't understand that. Please use the menu buttons or type /start to begin."
        )


# Notification functions for admin
async def notify_user_receipt_status(bot, user_id: int, status: str, reason: str = None):
    """Notify user about receipt status change"""
    try:
        user = await get_user(telegram_id=user_id)
        if status == 'approved':
            text = get_text('receipt_approved', user.language)
        elif status == 'rejected':
            text = get_text('receipt_rejected', user.language, reason=reason or "")
        else:
            return
        
        await bot.send_message(user_id, text)
    except Exception as e:
        print(f"Error notifying user {user_id}: {e}")