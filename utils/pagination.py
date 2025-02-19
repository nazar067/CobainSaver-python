from aiogram.types import CallbackQuery
from downloader.playlist import process_music_playlist


async def playlist_pagination(callback: CallbackQuery, dp):
    _, source, content_type, playlist_id, new_page = callback.data.split()
    chat_id = callback.message.chat.id
    msg_id = callback.message.message_id
    business_connection_id = callback.message.business_connection_id
    print(source)
    print(content_type)
    if source == "Y":
        await process_music_playlist(callback.bot, dp, business_connection_id, int(chat_id), f"https://music.youtube.com/playlist?list={playlist_id}", int(new_page), int(msg_id))
    elif source == "S":
        if content_type is "a":
            await process_music_playlist(callback.bot, dp, business_connection_id, int(chat_id), f"https://open.spotify.com/album/{playlist_id}", int(new_page), int(msg_id))
        elif content_type is "p":
            print("pagination")
            await process_music_playlist(callback.bot, dp, business_connection_id, int(chat_id), f"https://open.spotify.com/playlist/{playlist_id}", int(new_page), int(msg_id))
    await callback.answer()