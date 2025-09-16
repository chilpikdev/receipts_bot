from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from .translations import get_text
from .database import Branch
from typing import List


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Get language selection keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="O'zbekcha", callback_data="lang_uz"),
        InlineKeyboardButton(text="Qaraqalpaqsha", callback_data="lang_qq")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_contact_keyboard(language: str = 'uz') -> ReplyKeyboardMarkup:
    """Get contact sharing keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(
            text=get_text('contact_button', language),
            request_contact=True
        )
    )
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_subscription_keyboard(language: str = 'uz') -> InlineKeyboardMarkup:
    """Get Instagram subscription confirmation keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=get_text('follow_button', language),
            callback_data="instagram_subscribed"
        )
    )
    return builder.as_markup()


def get_branches_keyboard(branches: List[Branch], language: str = 'uz') -> InlineKeyboardMarkup:
    """Get branches selection keyboard"""
    builder = InlineKeyboardBuilder()
    for branch in branches:
        builder.add(
            InlineKeyboardButton(
                text=branch.get_name(language),
                callback_data=f"branch_{branch.id}"
            )
        )
    builder.adjust(1)
    return builder.as_markup()


def get_main_menu_keyboard(language: str = 'uz') -> ReplyKeyboardMarkup:
    """Get main menu keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text=get_text('send_receipt_btn', language)),
        KeyboardButton(text=get_text('change_language', language))
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_back_keyboard(language: str = 'uz') -> ReplyKeyboardMarkup:
    """Get back to menu keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text=get_text('back_to_menu', language))
    )
    return builder.as_markup(resize_keyboard=True)