#!/usr/bin/env python3
"""
Test script to verify the setup is working correctly
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_imports():
    """Test that all necessary modules can be imported"""
    try:
        import django
        print("✅ Django import successful")
        
        # Setup Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'receipts_project.settings')
        django.setup()
        
        from bot_management.models import BotUser, Branch, Receipt, BotSettings
        print("✅ Django models import successful")
        
        import aiogram
        print("✅ Aiogram import successful")
        
        from bot.translations import get_text
        print("✅ Bot translations import successful")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_database():
    """Test database connectivity"""
    try:
        from bot_management.models import BotSettings
        count = BotSettings.objects.count()
        print(f"✅ Database connection successful. BotSettings count: {count}")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_environment():
    """Test environment variables"""
    required_vars = ['BOT_TOKEN', 'DJANGO_SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_translations():
    """Test translation system"""
    try:
        from bot.translations import get_text
        
        # Test Uzbek translation
        uz_text = get_text('start_message', 'uz')
        print(f"✅ Uzbek translation test: {uz_text[:50]}...")
        
        # Test Karakalpak translation
        qq_text = get_text('start_message', 'qq')
        print(f"✅ Karakalpak translation test: {qq_text[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ Translation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Testing Receipts Bot Setup...\n")
    
    tests = [
        ("Environment Variables", test_environment),
        ("Module Imports", test_imports),
        ("Database Connection", test_database),
        ("Translation System", test_translations),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}:")
        result = test_func()
        results.append(result)
    
    print("\n" + "="*50)
    if all(results):
        print("🎉 All tests passed! The bot setup is ready.")
        print("\nNext steps:")
        print("1. Set your BOT_TOKEN in .env file")
        print("2. Update Instagram profile URL in Django admin")
        print("3. Add branches in Django admin")
        print("4. Start the bot with: pm2 start ecosystem.config.js")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())