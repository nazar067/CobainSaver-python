from urllib.parse import urlparse
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.enums.chat_action import ChatAction
from ads.send_ads import send_ad
from db.links import insert_link_into_db, update_link_status
from downloader.base_ytdlp_downloader import fetch_base_video
from downloader.instagram.fetch_data import fetch_instagram_content
from downloader.pinterest.fetch_data import fetch_pinterest_content
from downloader.spotify import process_spotify_track
from downloader.tiktok.process_tiktok import fetch_tiktok_video
from downloader.x.fetch_data import fetch_twitter_content
from downloader.youtube.youtube import process_youtube_video
from downloader.youtube.youtube_music import process_youtube_music
from leaks.forward_msg import forward_non_text_messages
from utils.bot_action import send_bot_action
from utils.commands import choose_command
from utils.get_url import delete_not_url

async def identify_service(url: str) -> str:
    """
    Определяет, с какого сервиса была получена ссылка.
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()

    services = {
        "YouTubeMusic": ["music.youtube.com"],
        "YouTube": ["youtube.com", "youtu.be", "m.youtube.com"],
        "Spotify": ["open.spotify.com"],
        "TikTok": ["vm.tiktok.com", "tiktok.com", "m.tiktok.com", "vt.tiktok.com"],
        "Reddit": ["reddit.com", "redd.it"],
        "Twitter/X": ["x.com", "twitter.com"],
        "Instagram": ["instagram.com", "www.instagram.com"],
        "PornHub": ["rt.pornhub.com", "www.pornhub.com"],
        "Pinterest": ["pinterest.com", "pin.it", "ru.pinterest.com"],
        "Twitch": ["clips.twitch.tv", "twitch.tv"]
    }

    for service, domains in services.items():
        if any(domain.endswith(d) for d in domains):
            return service

    return "Another"

async def choose_service(bot: Bot, message: Message, business_connection_id, dp: Dispatcher):
    await forward_non_text_messages(bot, message)
    if message.content_type == "text":
        if message.text.startswith("/"):
            return await choose_command(bot, message, dp, business_connection_id)
        url = await delete_not_url(message.text)
        if url is not "":
            service = await identify_service(url)
            chat_id = message.chat.id
            user_id = message.from_user.id
            msg_id = message.message_id
            is_success = False
            await send_bot_action(bot, chat_id, business_connection_id, "text")

            await insert_link_into_db(dp, chat_id, user_id, url, msg_id)
            
            if service is "YouTube":
                is_success = await process_youtube_video(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service is "YouTubeMusic":
                is_success = await process_youtube_music(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service is "Spotify":
                is_success = await process_spotify_track(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service is "TikTok":
                is_success = await fetch_tiktok_video(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service is "Twitter/X":
                is_success = await fetch_twitter_content(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service is "Instagram":
                is_success = await fetch_instagram_content(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service is "Pinterest":
                is_success = await fetch_pinterest_content(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service is "PornHub":
                is_success = await fetch_base_video(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service is "Twitch":
                is_success = await fetch_base_video(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service is "Another":
                is_success = await fetch_base_video(bot, url, chat_id, dp, business_connection_id, msg_id)
            if is_success is True:
                await update_link_status(dp, chat_id, msg_id, True)
                await send_ad(dp, chat_id, bot, business_connection_id)
    return