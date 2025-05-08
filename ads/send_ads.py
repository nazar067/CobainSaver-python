from localisation.get_language import get_language
from logs.write_server_errors import log_error
from utils.get_settings import get_settings
from localisation.translations.ads import translations


async def send_ad(dp, chat_id, bot, business_connection_id):
    try:
        if business_connection_id == "":
            pool = dp["db_pool"]
            chat_language = await get_language(pool, chat_id)
            settings = await get_settings(pool, chat_id)
            is_ads = settings["send_ads"]
            if is_ads:
                await bot.send_message(chat_id=chat_id, text=translations["cobain_news"][chat_language] + "\n\n" + translations["dice"][chat_language]+ "\n\n" + translations["disable_ads"][chat_language], parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        log_error("url", e, chat_id)