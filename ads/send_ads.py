from utils.get_settings import get_settings


async def send_ad(dp, chat_id, bot, business_connection_id):
    if business_connection_id is "":
        pool = dp["db_pool"]
        settings = await get_settings(pool, chat_id)
        is_ads = settings["send_ads"]
        if is_ads:
            await bot.send_message(chat_id=chat_id, text="ads")