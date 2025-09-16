import asyncio
import logging
from typing import Optional
from asgiref.sync import sync_to_async
from django.conf import settings
from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError
from bot.translations import get_text

logger = logging.getLogger(__name__)


class BotNotificationService:
    """Service for sending notifications to users via Telegram bot"""
    
    def __init__(self):
        self.bot_token = settings.BOT_TOKEN
        self.bot = None
        
    async def _get_bot(self):
        """Get bot instance"""
        if not self.bot and self.bot_token:
            self.bot = Bot(token=self.bot_token)
        return self.bot
    
    async def notify_receipt_status(self, user_telegram_id: int, receipt_id: int, 
                                  status: str, user_language: str = 'uz', 
                                  rejection_reason: Optional[str] = None):
        """Notify user about receipt status change"""
        try:
            bot = await self._get_bot()
            if not bot:
                logger.error("Bot token not configured")
                return False
                
            if status == 'approved':
                message = get_text('receipt_approved', user_language)
            elif status == 'rejected':
                message = get_text('receipt_rejected', user_language, 
                                 reason=rejection_reason or "No reason provided")
            else:
                logger.warning(f"Unknown status: {status}")
                return False
                
            await bot.send_message(
                chat_id=user_telegram_id,
                text=f"Receipt #{receipt_id}\n{message}"
            )
            logger.info(f"Notification sent to user {user_telegram_id} for receipt {receipt_id}")
            return True
            
        except TelegramForbiddenError:
            logger.warning(f"User {user_telegram_id} blocked the bot")
            return False
        except TelegramRetryAfter as e:
            logger.warning(f"Rate limited, retry after {e.retry_after} seconds")
            return False
        except Exception as e:
            logger.error(f"Error sending notification to user {user_telegram_id}: {e}")
            return False
        finally:
            if self.bot:
                await self.bot.session.close()
                self.bot = None


# Global instance
notification_service = BotNotificationService()


def notify_user_sync(user_telegram_id: int, receipt_id: int, status: str, 
                    user_language: str = 'uz', rejection_reason: Optional[str] = None):
    """Synchronous wrapper for sending notifications"""
    try:
        # Run the async notification in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                notification_service.notify_receipt_status(
                    user_telegram_id, receipt_id, status, user_language, rejection_reason
                )
            )
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Error in sync notification wrapper: {e}")
        return False