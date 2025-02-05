from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def generate_playlist_keyboard(tracks, chat_id, source, playlist_id, current_page, total_pages, msg_id, content_type):
    """
    Создает inline-клавиатуру с треками и кнопками навигации.
    `source` - 'Y' (YouTube) или 'S' (Spotify).
    """
    buttons_list = [
        [InlineKeyboardButton(
            text=track["title"], 
            callback_data=f"{source} {track['id']} {chat_id} {playlist_id} {msg_id}"
        )]
        for track in tracks
    ]

    # Кнопки пагинации
    navigation_buttons = []
    if total_pages > 1:
        if current_page > 1:
            navigation_buttons.append(
                InlineKeyboardButton(text="◀️ Назад", callback_data=f"P {source} {content_type} {chat_id} {playlist_id} {current_page - 1} {msg_id}")
            )
        if current_page < total_pages:
            navigation_buttons.append(
                InlineKeyboardButton(text="Вперед ▶️", callback_data=f"N {source} {content_type} {chat_id} {playlist_id} {current_page + 1} {msg_id}")
            )
    
    if navigation_buttons:
        buttons_list.append(navigation_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons_list)