import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import Message


class SafeDeleteHandledMessagesMiddleware(BaseMiddleware):
    """Delete handled user messages to keep chat history clean."""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        result = await handler(event, data)

        if isinstance(event, Message) and result is not UNHANDLED:
            await self._safe_delete(event)

        return result

    async def _safe_delete(self, message: Message) -> None:
        # Skip bot/service messages. We only clean user-originated messages.
        if message.from_user is None or message.from_user.is_bot:
            return

        try:
            await message.delete()
        except (TelegramBadRequest, TelegramForbiddenError):
            return
        except Exception:
            logging.getLogger(__name__).debug(
                "Message safe delete failed: chat_id=%s message_id=%s",
                message.chat.id,
                message.message_id,
                exc_info=True,
            )
