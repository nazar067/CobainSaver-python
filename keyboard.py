from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def generate_playlist_keyboard(tracks, source, playlist_id, current_page, total_pages, content_type):
    """
    Создает inline-клавиатуру с треками и кнопками навигации.
    `source` - 'Y' (YouTube) или 'S' (Spotify).
    """
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки треков
    for track in tracks:
        builder.button(
            text=track["title"],
            callback_data=f"{source} {track['id']} {playlist_id}"
        )

    builder.adjust(2)

    # Кнопки пагинации
    if total_pages > 1:
        navigation_buttons = []
        if current_page > 1:
            navigation_buttons.append(
                InlineKeyboardButton(text="◀️ Назад", callback_data=f"P {source} {content_type} {playlist_id} {current_page - 1}")
            )
        if current_page < total_pages:
            navigation_buttons.append(
                InlineKeyboardButton(text="Вперед ▶️", callback_data=f"P {source} {content_type} {playlist_id} {current_page + 1}")
            )

        if navigation_buttons:
            builder.row(*navigation_buttons)

    return builder.as_markup()
