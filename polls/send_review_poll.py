import asyncio
from datetime import datetime, timedelta
import logging
from aiogram import Bot, Dispatcher
from asyncpg import Pool

from localisation.get_language import get_language
from utils.user_rate import get_active_chats_last_month
from localisation.translations.polls import translations

async def send_feedback_polls(bot: Bot, pool: Pool):
    try:
        chat_ids = await get_active_chats_last_month(pool)
        
        print("chats", chat_ids)

        for chat_id in chat_ids:
            chat_language = await get_language(pool, chat_id)
            options = translations["rate"][chat_language].splitlines()
            try:
                await bot.send_poll(
                    chat_id=chat_id,
                    question=translations["send_review_poll"][chat_language],
                    options=options,
                    is_anonymous=False,
                    allows_multiple_answers=False,
                    question_parse_mode="HTML",
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
        except Exception as e:
            logging.error(f"Ошибка в daily_feedback_task: {e}", exc_info=True)