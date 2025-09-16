#!/usr/bin/env python3
"""
Script to create test data for testing receipt approval functionality
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

import django
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'receipts_project.settings')
django.setup()

from bot_management.models import BotUser, Branch, Receipt, BotSettings
from django.core.files.base import ContentFile


def create_test_data():
    """Create test data for the receipt system"""
    
    # Create bot settings if not exists
    bot_settings, created = BotSettings.objects.get_or_create(
        defaults={'instagram_profile_url': 'https://instagram.com/test_profile'}
    )
    if created:
        print("✅ Created bot settings")
    
    # Create test branches
    branch1, created = Branch.objects.get_or_create(
        name_uz="Toshkent filiali",
        defaults={
            'name_qq': "Toshkent filialı",
            'address_uz': "Toshkent shahar, Yunusobod tumani",
            'address_qq': "Toshkent qala, Yunusobod rayonı",
            'is_active': True
        }
    )
    if created:
        print("✅ Created Tashkent branch")
    
    branch2, created = Branch.objects.get_or_create(
        name_uz="Samarqand filiali",
        defaults={
            'name_qq': "Samarqand filialı",
            'address_uz': "Samarqand shahar, Markaz",
            'address_qq': "Samarqand qala, Merkez",
            'is_active': True
        }
    )
    if created:
        print("✅ Created Samarkand branch")
    
    # Create test user
    test_user, created = BotUser.objects.get_or_create(
        telegram_id=123456789,
        defaults={
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '+998901234567',
            'language': 'uz',
            'instagram_username': '@testuser',
            'is_subscribed_instagram': True
        }
    )
    if created:
        print("✅ Created test user")
    
    # Create test receipts
    # Create a pending receipt
    test_content = b"This is a test receipt file content"
    receipt1, created = Receipt.objects.get_or_create(
        user=test_user,
        branch=branch1,
        status='pending',
        defaults={
            'file_size': len(test_content)
        }
    )
    if created:
        receipt1.file.save('test_receipt_1.pdf', ContentFile(test_content), save=True)
        print("✅ Created test pending receipt")
    
    # Create another pending receipt
    receipt2, created = Receipt.objects.get_or_create(
        user=test_user,
        branch=branch2,
        status='pending',
        defaults={
            'file_size': len(test_content)
        }
    )
    if created:
        receipt2.file.save('test_receipt_2.jpg', ContentFile(test_content), save=True)
        print("✅ Created another test pending receipt")
    
    print("\n🎉 Test data created successfully!")
    print(f"📊 Statistics:")
    print(f"   - Users: {BotUser.objects.count()}")
    print(f"   - Branches: {Branch.objects.count()}")
    print(f"   - Receipts: {Receipt.objects.count()}")
    print(f"   - Pending receipts: {Receipt.objects.filter(status='pending').count()}")
    
    print(f"\n🌐 Access admin interface at: http://localhost:8000/admin/")
    print(f"   Username: admin")
    print(f"   Password: admin123")


if __name__ == '__main__':
    create_test_data()