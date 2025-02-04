from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def generate_playlist_keyboard(videos, chat_id, playlist_id, current_page, total_pages, msg_id):
    """
    Создает inline-клавиатуру с треками и кнопками навигации.
    """
    buttons_list = [
        [InlineKeyboardButton(text=track["title"], callback_data=f"L {track['id']} {chat_id} {playlist_id} {msg_id}")]
        for track in videos
    ]

    # Кнопки пагинации
    navigation_buttons = []
    if total_pages > 1:
        if current_page > 1:
            navigation_buttons.append(
                InlineKeyboardButton(text="◀️ Назад", callback_data=f"P {chat_id} {playlist_id} {current_page - 1} {msg_id}")
            )
        if current_page < total_pages:
            navigation_buttons.append(
                InlineKeyboardButton(text="Вперед ▶️", callback_data=f"N {chat_id} {playlist_id} {current_page + 1} {msg_id}")
            )
    if navigation_buttons:
        buttons_list.append(navigation_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons_list)