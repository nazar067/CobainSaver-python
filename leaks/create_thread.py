import logging
from typing import Optional
import asyncpg
from aiogram import Bot
from aiogram.types import Message
from config import THREAD_GROUP_ID

async def save_thread(pool: asyncpg.Pool, chat_id: int, topic_id: int):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO threads (chat_id, topic_id) 
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
            """,
            chat_id, topic_id
        )
        
async def is_thread_exists(pool: asyncpg.Pool, chat_id: int) -> Optional[int]:
    async with pool.acquire() as conn:
        topic_id = await conn.fetchval(
            "SELECT topic_id FROM threads WHERE chat_id = $1", chat_id
        )
    return topic_id



async def get_forum_thread(bot: Bot, dp, message: Message):
    try:
        pool = dp["db_pool"]
        thread_group_id = int(THREAD_GROUP_ID)
        chat_id = message.chat.id
        thread_name = message.chat.full_name
        
        if chat_id == thread_group_id:
            return

        topic_id = await is_thread_exists(pool, chat_id)

        if topic_id:
            return topic_id

        topic = await bot.create_forum_topic(chat_id=thread_group_id, name=thread_name)

        await save_thread(pool, chat_id, topic.message_thread_id)

        return topic.message_thread_id

    except Exception as e:
        logging.error(f"Ошибка при создании темы: {e}")
        return None