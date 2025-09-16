import os
import django
import sys
from pathlib import Path
from asgiref.sync import sync_to_async

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'receipts_project.settings')
django.setup()

from bot_management.models import BotUser, Branch, Receipt, BotSettings
from django.core.files.base import ContentFile
from django.utils import timezone
import aiofiles
import aiohttp


# Async wrappers for Django ORM operations
@sync_to_async
def get_or_create_user(telegram_id, defaults):
    return BotUser.objects.get_or_create(telegram_id=telegram_id, defaults=defaults)

@sync_to_async
def get_user(telegram_id):
    return BotUser.objects.get(telegram_id=telegram_id)

@sync_to_async
def save_user(user):
    user.save()
    return user

@sync_to_async
def get_active_branches():
    return list(Branch.objects.filter(is_active=True))

@sync_to_async
def get_branch(branch_id):
    return Branch.objects.get(id=branch_id)

@sync_to_async
def create_receipt(user, branch, file_size):
    return Receipt.objects.create(user=user, branch=branch, file_size=file_size)

@sync_to_async
def save_receipt_file(receipt, file_name, file_data):
    receipt.file.save(file_name, ContentFile(file_data), save=True)
    return receipt

@sync_to_async
def get_bot_settings():
    return BotSettings.objects.first()

@sync_to_async
def user_exists(telegram_id):
    return BotUser.objects.filter(telegram_id=telegram_id).exists()