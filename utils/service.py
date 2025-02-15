from urllib.parse import urlparse
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.enums.chat_action import ChatAction
from db.links import insert_link_into_db
from downloader.base_ytdlp_downloader import fetch_base_video
from downloader.instagram.fetch_data import fetch_instagram_content
from downloader.pinterest.fetch_data import fetch_pinterest_content
from downloader.spotify import process_spotify_track
from downloader.tiktok.process_tiktok import fetch_tiktok_video
from downloader.x.fetch_data import fetch_twitter_content
from downloader.youtube.youtube import process_youtube_video
from downloader.youtube.youtube_music import process_youtube_music
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
    if message.text.startswith("/"):
        return await choose_command(bot, message, dp)
    url = await delete_not_url(message.text)
    if url is not "":
        service = await identify_service(url)
        chat_id = message.chat.id
        user_id = message.from_user.id
        msg_id = message.message_id
        await send_bot_action(bot, chat_id, business_connection_id, "text")

        await insert_link_into_db(dp, chat_id, user_id, url, msg_id)
        
        if service is "YouTube":
            return await process_youtube_video(bot, url, chat_id, dp, business_connection_id, msg_id)
        elif service is "YouTubeMusic":
            return await process_youtube_music(bot, url, chat_id, dp, business_connection_id, msg_id)
        elif service is "Spotify":
            return await process_spotify_track(bot, url, chat_id, dp, business_connection_id, msg_id)
        elif service is "TikTok":
            return await fetch_tiktok_video(bot, url, chat_id, dp, business_connection_id, msg_id)
        elif service is "Twitter/X":
            return await fetch_twitter_content(bot, url, chat_id, dp, business_connection_id, msg_id)
        elif service is "Instagram":
            return await fetch_instagram_content(bot, url, chat_id, dp, business_connection_id, msg_id)
        elif service is "Pinterest":
            return await fetch_pinterest_content(bot, url, chat_id, dp, business_connection_id, msg_id)
        elif service is "PornHub":
            return await fetch_base_video(bot, url, chat_id, dp, business_connection_id, msg_id)
        elif service is "Twitch":
            return await fetch_base_video(bot, url, chat_id, dp, business_connection_id, msg_id)
        elif service is "Another":
            return await fetch_base_video(bot, url, chat_id, dp, business_connection_id, msg_id)