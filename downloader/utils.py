import os
import re
from urllib.parse import urlparse
from aiogram.types import Message

from downloader.youtube import process_youtube_video

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
        "PornHub": ["rt.pornhub.com"],
        "Pinterest": ["pinterest.com", "pin.it", "ru.pinterest.com"],
        "Twitch": ["clips.twitch.tv", "twitch.tv"]
    }

    for service, domains in services.items():
        if any(domain.endswith(d) for d in domains):
            return service

    return "Another"

async def choose_service(bot, message: Message, business_connection_id):
    url = await delete_not_url(message.text)
    service = await identify_service(url)
    chat_id = message.chat.id
    if service is "YouTube":
        return await process_youtube_video(bot, url, chat_id, business_connection_id)

async def delete_not_url(message: str) -> str:
    """
    Фильтрует URL-адрес из сообщения.
    """
    regex_url = re.compile(r"\bhttps://\S+\b")

    regex_short_url = re.compile(r"youtu.be/\w+")

    match_url = regex_url.search(message)

    match_short_url = regex_short_url.search(message)

    if match_url:
        return match_url.group(0)

    if match_short_url:
        return "https://" + match_short_url.group(0)

    return ""