from aiogram import Bot

from config import ADMIN_ID
from localisation.get_language import get_language
from logs.write_server_errors import log_error
from localisation.translations.general import translations

async def send_premium(bot: Bot, dp, user_id, months, star):
    try:
        pool = dp["db_pool"]
        chat_language = await get_language(pool, int(user_id))
        is_success = await bot.gift_premium_subscription(user_id=user_id, month_count=months, star_count=star, text=translations["congratulations_premium"][chat_language], text_parse_mode="HTML")
        await bot.send_message(ADMIN_ID, is_success)
        if is_success:
            await bot.send_message(user_id, text=translations["add_bot_to_private_chats"][chat_language], parse_mode="HTML")
            await bot.send_message(ADMIN_ID, "all done")
    except Exception as e:
        log_error("url", e, user_id, "send gift premium")