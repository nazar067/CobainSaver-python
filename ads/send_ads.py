from localisation.get_language import get_language
from logs.write_server_errors import log_error
from utils.get_settings import get_settings
from localisation.translations.ads import translations

VIDEO_AD_CHAT_ID = -1002445866808
VIDEO_AD_URL = "https://bandura.monster/tiltovik.mp4"


async def send_ad(dp, chat_id, bot, business_connection_id):
    try:
        if business_connection_id:
            return
        pool = dp["db_pool"]
        chat_language = await get_language(pool, chat_id)
        settings = await get_settings(pool, chat_id)
        is_ads = settings["send_ads"]
        if not is_ads:
            return
        text = translations["cobain_news"][chat_language] + "\n\n" + translations["dice"][chat_language]+ "\n\n" + translations["disable_ads"][chat_language]
        if str(chat_id) == str(VIDEO_AD_CHAT_ID):
            await bot.send_video(chat_id=chat_id, video=VIDEO_AD_URL, caption=text, parse_mode="HTML", supports_streaming=True, request_timeout=1800)
            return
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        log_error("url", e, chat_id, "send ads")