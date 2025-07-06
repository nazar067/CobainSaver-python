import os
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from localisation.get_language import get_language
from user.get_user_path import get_user_path
from utils.get_name import get_clear_name, get_name_for_button_data, get_random_file_name
from utils.get_settings import get_settings
from localisation.translations.downloader import translations as downloader_translations
from localisation.translations.general import translations as general_translations

async def generate_playlist_keyboard(tracks, source, playlist_id, current_page, total_pages, content_type, dp, chat_id):
    """
    Создает inline-клавиатуру с треками и кнопками навигации.
    `source` - 'Y' (YouTube) или 'S' (Spotify).
    """
    pool = dp["db_pool"]
    builder = InlineKeyboardBuilder()
    chat_language = await get_language(pool, chat_id)
    # Добавляем кнопки треков
    for track in tracks:
        clear_tittle = await get_name_for_button_data(track["title"], 7)
        builder.button(
            text=track["title"],
            callback_data=f"{source} {track['id']} {playlist_id} {clear_tittle}"
        )

    builder.adjust(2)

    # Кнопки пагинации
    if total_pages > 1:
        navigation_buttons = []
        if current_page > 1:
            navigation_buttons.append(
                InlineKeyboardButton(text=downloader_translations["playlist_previous_btn"][chat_language], callback_data=f"P {source} {content_type} {playlist_id} {current_page - 1}")
            )
        if current_page < total_pages:
            navigation_buttons.append(
                InlineKeyboardButton(text=downloader_translations["playlist_next_btn"][chat_language], callback_data=f"P {source} {content_type} {playlist_id} {current_page + 1}")
            )

        if navigation_buttons:
            builder.row(*navigation_buttons)

    return builder.as_markup()

async def generate_settings_keyboard(chat_id: int, send_tiktok_music: bool, send_ads: bool, hd_size: bool, pool, business_connection_id=None):
    builder = InlineKeyboardBuilder()
    
    chat_language = await get_language(pool, chat_id)
    audio_text = general_translations["turn_on_audio_btn"][chat_language] if not send_tiktok_music else general_translations["turn_off_audio_btn"][chat_language]
    hd_size_text = general_translations["turn_on_hd_size"][chat_language] if not hd_size else general_translations["turn_off_hd_size"][chat_language]
    builder.button(
        text=audio_text,
        callback_data=f"toggle_audio {chat_id} {int(not send_tiktok_music)}"
    )
    
    settings = await get_settings(pool, chat_id)
    is_ads = settings["send_ads"]
    if is_ads:
        if business_connection_id == "" or business_connection_id == None:
            ads_text = general_translations["turn_on_ads_btn"][chat_language] if not send_ads else general_translations["turn_off_ads_btn"][chat_language]
            builder.button(
                text=ads_text,
                callback_data=f"pay:{25}"
            )
            
    builder.button(
        text=hd_size_text,
        callback_data=f"toggle_hd_size {chat_id} {int(not hd_size)}"
    )
    builder.adjust(1)

    return builder.as_markup()

def language_keyboard(message: Message) -> InlineKeyboardMarkup:
    """
    Создание клавиатуры для смены языка.
    """
    msg_id = message.message_id
    builder = InlineKeyboardBuilder()
    builder.button(text="English", callback_data=f"set_language:en {str(msg_id)}")
    builder.button(text="Русский", callback_data=f"set_language:ru {str(msg_id)}")
    builder.button(text="Українська", callback_data=f"set_language:uk {str(msg_id)}")
    builder.adjust(1)
    return builder.as_markup()

async def send_log_keyboard(bot_message, message_error, chat_language, chat_id) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    file_name = get_random_file_name("txt")
    user_path = await get_user_path(chat_id)
    os.makedirs(os.path.dirname(user_path), exist_ok=True)
    log_path = os.path.join(user_path, file_name)
    if not os.path.exists(log_path):
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(bot_message + "\n" + message_error + "\n" + chat_language)
    else:
        with open(log_path, 'r', encoding='utf-8') as f:
            old_data = f.read()

        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(bot_message + "\n" + message_error + "\n" + chat_language + "\n" + old_data)
            
    builder.button(text="Отправить📨", callback_data=f"error_file {log_path}")
    builder.adjust(1)
    return builder.as_markup()