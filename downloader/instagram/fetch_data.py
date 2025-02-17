import os
import instaloader
from aiogram import Bot, Dispatcher

from downloader.send_album import send_social_media_album
from localisation.get_language import get_language
from user.get_user_path import get_user_path
from utils.get_name import get_random_file_name
from localisation.translations.downloader import translations

async def fetch_instagram_content(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id, msg_id):
    pool = dp["db_pool"]
    chat_language = await get_language(pool, chat_id)
    random_name = get_random_file_name("") + "insta"
    directory = await get_user_path(chat_id)
    
    loader = instaloader.Instaloader(
        dirname_pattern=directory,
        filename_pattern=random_name,
        download_comments=False,
        download_geotags=False,
        download_pictures=True,
        download_video_thumbnails=False,
        save_metadata=False
    )

    shortcode = url.split('/')[-2]

    post = instaloader.Post.from_shortcode(loader.context, shortcode)
    loader.download_post(post, target=shortcode)
    
    matching_files = [
        os.path.join(directory, file) for file in os.listdir(directory) if random_name in file
    ]

    caption = ""
    txt_file_path = next((os.path.join(directory, file) for file in os.listdir(directory) if random_name in file and file.endswith(".txt")), None)
    
    if txt_file_path:
        try:
            with open(txt_file_path, "r", encoding="utf-8") as f:
                caption = f.read().strip()
        except Exception as e:
            print(e)
    if matching_files:
        return await send_social_media_album(bot, chat_id, chat_language, business_connection_id, matching_files, caption, msg_id, pool=pool)
    else:
        await bot.send_message(chat_id, text=translations["unavaliable_content"][chat_language], reply_to_message_id=msg_id)
