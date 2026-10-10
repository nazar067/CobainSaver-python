
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.types import MessageOriginUser

from config import LEAKS_ID
from logs.write_server_errors import log_error
from utils.get_url import delete_not_url


async def forward_non_text_messages(
    bot: Bot,
    dp: Dispatcher,
    message: types.Message
):
    """
    Пересылает сообщения в LEAKS_ID и записывает
    информацию об исходном сообщении в PostgreSQL.
    """
    try:
        if message.business_connection_id:
            return

        # Текстовые сообщения пересылаем только при наличии URL
        if message.content_type == "text":
            url = await delete_not_url(message.text or "")

            if not url:
                return

        # Пересылаем сообщение в LEAKS_ID
        forwarded_message = await message.forward(LEAKS_ID)

        forward_user_id = message.from_user.id

        # Первоначальный автор пересланного сообщения
        original_user_id = None

        if isinstance(message.forward_origin, MessageOriginUser):
            original_user_id = message.forward_origin.sender_user.id

        # Чат, в который пользователь отправил сообщение
        chat_id = message.chat.id

        # ID сообщения в LEAKS_ID
        message_id = forwarded_message.message_id

        # Время отправки исходного сообщения
        timestamp = message.date

        # Записываем информацию в БД
        pool = dp["db_pool"]

        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO leaks (
                    message_id,
                    forward_user_id,
                    original_user_id,
                    chat_id,
                    timestamp
                )
                VALUES ($1, $2, $3, $4, $5)
                """,
                message_id,
                forward_user_id,
                original_user_id,
                chat_id,
                timestamp
            )

    except Exception as e:
        log_error("url", e)
