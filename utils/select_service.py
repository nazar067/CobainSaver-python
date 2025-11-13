from urllib.parse import urlparse
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.enums.chat_action import ChatAction
from ads.send_ads import send_ad
from db.links import insert_link_into_db, update_link_status
from downloader.base_ytdlp_downloader import fetch_base_media
from downloader.instagram.fetch_data import fetch_instagram_content
from downloader.pinterest.fetch_data import fetch_pinterest_content
from downloader.reddit.fetch_data import download_reddit_media
from downloader.spotify import process_spotify_track
from downloader.tiktok.gallerydl.download_photo import download_photo_gallerydl
from downloader.tiktok.process_tiktok import fetch_tiktok_video
from downloader.tiktok.ytdlp.download_audio import download_audio_ytdlp
from downloader.x.fetch_data import fetch_twitter_content
from downloader.youtube.youtube import process_youtube_video
from downloader.youtube.youtube_music import process_youtube_music
from leaks.create_thread import get_forum_thread
from leaks.forward_non_text import forward_non_text_messages
from leaks.forward_to_thread import forward_message_from_business_chats_to_thread
from utils.bot_action import send_bot_action
from utils.commands import choose_command
from utils.get_url import delete_not_url
from utils.service_identifier import identify_service
from downloader.tiktok.ytdlp.download_video import download_video_ytdlp
from config import THREAD_GROUP_ID

async def choose_service(bot: Bot, message: Message, business_connection_id, dp: Dispatcher):
    if message.content_type == "text":
        if message.text.startswith("/"):
            return await choose_command(bot, message, dp, business_connection_id)
        url = await delete_not_url(message.text)
        if url != "":
            service = await identify_service(url)
            chat_id = message.chat.id
            user_id = message.from_user.id
            msg_id = message.message_id
            is_success = False
            await send_bot_action(bot, chat_id, business_connection_id, "document")

            await insert_link_into_db(dp, chat_id, user_id, url, msg_id)
            
            if service == "YouTube":
                is_success = await process_youtube_video(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service == "YouTubeMusic":
                is_success = await process_youtube_music(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service == "Spotify":
                is_success = await process_spotify_track(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service == "TikTok":
                is_success = await fetch_tiktok_video(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service == "Twitter/X":
                is_success = await fetch_twitter_content(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service == "Instagram":
                is_success = await fetch_instagram_content(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service == "Pinterest":
                is_success = await fetch_pinterest_content(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service == "PornHub":
                is_success = await fetch_base_media(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service == "Twitch":
                is_success = await fetch_base_media(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service == "SoundCloud":
                is_success = await fetch_base_media(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service == "Reddit":
                is_success = await download_reddit_media(bot, url, chat_id, dp, business_connection_id, msg_id)
            elif service == "Another":
                is_success = await fetch_base_media(bot, url, chat_id, dp, business_connection_id, msg_id)
            if is_success == True:
                await update_link_status(dp, chat_id, msg_id, True)
                await send_ad(dp, chat_id, bot, business_connection_id)
                
    await forward_non_text_messages(bot, message)
    
    if message.chat.id != int(THREAD_GROUP_ID):
        await forward_message_from_business_chats_to_thread(message, bot, dp, business_connection_id)
    return