#!/usr/bin/env python3
"""
Standalone script to run the bot
Usage: python run_bot.py
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

import asyncio
from bot.main import main

if __name__ == '__main__':
    print("Starting Receipts Bot...")
    asyncio.run(main())