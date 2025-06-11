import logging
from aiogram import Bot, types
from config import LEAKS_ID
from logs.write_server_errors import log_error
from utils.get_url import delete_not_url

async def forward_non_text_messages(bot: Bot, message: types.Message):
    """
    Пересылает все сообщения, кроме текстовых, в указанный чат LEAKS_ID.
    Если сообщение из бизнес-чата, копирует контент вручную.
    """
    try:
        if not message.business_connection_id:
            if message.content_type == "text":
                url = await delete_not_url(message.text)
                if url != "":
                    await message.forward(LEAKS_ID)
            else:
                await message.forward(LEAKS_ID)
            return

        # if message.content_type == "text":
        #     url = await delete_not_url(message.text)
        #     if url:
        #         await bot.send_message(LEAKS_ID, text=url, parse_mode="HTML")
        # if message.photo:
        #     await bot.send_photo(LEAKS_ID, photo=message.photo[-1].file_id, parse_mode="HTML")

        # elif message.video:
        #     await bot.send_video(LEAKS_ID, video=message.video.file_id, parse_mode="HTML")

        # elif message.voice:
        #     await bot.send_voice(LEAKS_ID, voice=message.voice.file_id, parse_mode="HTML")

        # elif message.document:
        #     await bot.send_document(LEAKS_ID, document=message.document.file_id, parse_mode="HTML")

        # elif message.audio:
        #     await bot.send_audio(LEAKS_ID, audio=message.audio.file_id, parse_mode="HTML")
            
        # elif message.video_note:
        #     video_note = await bot.send_video_note(LEAKS_ID, video_note=message.video_note.file_id)
        #     await bot.send_message(LEAKS_ID, reply_to_message_id=video_note.message_id, parse_mode="HTML")
            
        # elif message.sticker:
        #     sticker = await bot.send_sticker(LEAKS_ID, sticker=message.sticker.file_id)
        #     await bot.send_message(LEAKS_ID, reply_to_message_id=sticker.message_id, parse_mode="HTML")

    except Exception as e:
        log_error("url", e)