from aiogram import Bot, Dispatcher

from downloader.tiktok.download_audio import download_and_send_tiktok_audio
from downloader.tiktok.download_video import download_and_send_tiktok_video
from downloader.tiktok.extract_tiktok_data import extract_tiktok_data
from downloader.tiktok.internet_video import send_tiktok_video
from localisation.get_language import get_language
from user.get_user_path import get_user_path

async def fetch_tiktok_video(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id) -> None:
    """
    Главная функция: извлекает данные, скачивает и отправляет TikTok-контент.
    """
    try:
        pool = dp["db_pool"]
        chat_language = await get_language(pool, chat_id)
        save_folder = await get_user_path(chat_id)

        # 📌 **Извлекаем данные**
        data = await extract_tiktok_data(url)
        if "error" in data:
            return await bot.send_message(chat_id, text=data["error"])

        # 📥 **Скачиваем и отправляем видео**
        await send_tiktok_video(bot, chat_id, chat_language, business_connection_id, data, save_folder)

        # 🎵 **Скачиваем и отправляем аудио**
        await download_and_send_tiktok_audio(bot, chat_id, chat_language, business_connection_id, data, save_folder)

    except Exception as e:
        print(f"❌ Ошибка обработки TikTok: {str(e)}")

