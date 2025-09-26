import logging
from typing import Optional
import asyncpg
from aiogram import Bot
from aiogram.types import Message
from config import THREAD_GROUP_ID
from logs.write_server_errors import log_error

async def save_thread(pool: asyncpg.Pool, adder_user_id: int, second_user_id: int, business_connection_id: str, topic_id: int):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO threads (adder_user_id, second_user_id, business_connection_id, topic_id) 
            VALUES ($1, $2, $3, $4)
            ON CONFLICT DO NOTHING
            """,
            adder_user_id, second_user_id, business_connection_id, topic_id
        )
        
async def is_thread_exists(pool: asyncpg.Pool, business_connection_id: str, adder_user_id: int, second_user_id: int) -> Optional[int]:
    async with pool.acquire() as conn:
        topic_id = await conn.fetchval(
            "SELECT topic_id FROM threads WHERE business_connection_id = $1 AND ( (adder_user_id = $2 AND second_user_id = $3) OR (adder_user_id = $3 AND second_user_id = $2) ) LIMIT 1", 
            business_connection_id, adder_user_id, second_user_id
        )
    return topic_id

async def get_adder_user_id(pool: asyncpg.Pool, business_connection_id: str) -> Optional[int]:
    async with pool.acquire() as conn:
        adder_user_id = await conn.fetchval(
            "SELECT adder_user_id FROM threads WHERE business_connection_id = $1", business_connection_id
        )
    return adder_user_id

async def get_second_user_id(pool: asyncpg.Pool, business_connection_id: str, second_user_id) -> Optional[int]:
    async with pool.acquire() as conn:
        second_user_id = await conn.fetchval(
            "SELECT second_user_id FROM threads WHERE business_connection_id = $1 AND second_user_id = $2", business_connection_id, second_user_id
        )
    return second_user_id


async def get_forum_thread(bot: Bot, dp, message: Message):
    try:
        pool = dp["db_pool"]
        thread_group_id = int(THREAD_GROUP_ID)
        business_connection_id = message.business_connection_id
        chat_id = message.chat.id
        thread_name = message.chat.full_name
        bc = await bot.get_business_connection(business_connection_id)
        adder_user_id = bc.user.id
        
        if chat_id == thread_group_id:
            return

        topic_id = await is_thread_exists(pool, business_connection_id, adder_user_id, chat_id)

        if topic_id:
            return topic_id

        topic = await bot.create_forum_topic(chat_id=thread_group_id, name=thread_name)

        await save_thread(pool, adder_user_id, chat_id ,business_connection_id, topic.message_thread_id)

        return topic.message_thread_id

    except Exception as e:
        log_error("url", e, chat_id, "get forum thread")
        return None