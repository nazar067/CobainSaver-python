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

async def generate_settings_keyboard(chat_id: int, send_tiktok_music: bool, send_ads: bool):
    builder = InlineKeyboardBuilder()

    audio_text = "✅ Включить аудио" if not send_tiktok_music else "❌ Выключить аудио"
    builder.button(
        text=audio_text,
        callback_data=f"toggle_audio {chat_id} {int(not send_tiktok_music)}"
    )

    ads_text = "✅ Включить рекламу" if not send_ads else "❌ Выключить рекламу"
    builder.button(
        text=ads_text,
        callback_data=f"toggle_ads {chat_id} {int(not send_ads)}"
    )
    builder.adjust(1)

    return builder.as_markup()