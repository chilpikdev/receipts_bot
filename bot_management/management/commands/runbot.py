import asyncio
import os
import sys
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

# Add bot directory to path
bot_dir = Path(settings.BASE_DIR) / 'bot'
sys.path.append(str(bot_dir))

from bot.main import main


class Command(BaseCommand):
    help = 'Run the Telegram bot'

    def add_arguments(self, parser):
        parser.add_argument(
            '--token',
            type=str,
            help='Bot token (overrides environment variable)',
        )

    def handle(self, *args, **options):
        if options['token']:
            os.environ['BOT_TOKEN'] = options['token']
        
        self.stdout.write(
            self.style.SUCCESS('Starting Telegram bot...')
        )
        
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS('Bot stopped successfully')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Bot error: {e}')
            )