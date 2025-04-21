import asyncio
from datetime import datetime, timedelta
import logging
from aiogram import Bot, Dispatcher
from asyncpg import Pool

from utils.user_rate import get_active_chats_last_month

async def send_feedback_polls(bot: Bot, pool: Pool):
    try:
        chat_ids = await get_active_chats_last_month(pool)
        print("chats", chat_ids)

        for chat_id in chat_ids:
            try:
                await bot.send_poll(
                    chat_id=chat_id,
                    question="📝 На какую оценку бот сработал за последний месяц?",
                    options=["5 - Отлично", "4 - Хорошо", "3 - Нормально", "2 - Плохо", "1 - Ужасно"],
                    is_anonymous=False,
                    allows_multiple_answers=False
                )
            except Exception as e:
                logging.error(f"Ошибка при отправке опроса пользователю {chat_id}: {e}", exc_info=True)

    except Exception as e:
        logging.error(f"Ошибка при извлечении списка активных пользователей: {e}", exc_info=True)


async def daily_feedback_task(bot: Bot, dp: Dispatcher):
    while True:
        now = datetime.now()
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        wait_seconds = (next_midnight - now).total_seconds()
        
        await asyncio.sleep(wait_seconds)

        try:
            today = datetime.now()
            if today.day == 22:
                pool = dp["db_pool"]
                print("📊 Сегодня первое число. Отправка опросов...")
                await send_feedback_polls(bot, pool)
            else:
                print("Не первое число. Опрос не отправляется.")
        except Exception as e:
            logging.error(f"Ошибка в daily_feedback_task: {e}", exc_info=True)