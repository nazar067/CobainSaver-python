import os
from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.types.input_file import FSInputFile
from aiogram.exceptions import TelegramBadRequest
from config import LOGS_ID
from downloader.media import del_media_content
from localisation.get_language import get_language
from localisation.translations.server import translations as server_translation
from localisation.translations.general import translations as general_translation
from localisation.translations.errors import translations as error_translation

from admin.check_is_admin import is_user_admin

async def send_server_logs(message: Message, dp):
    """
    Отправка файла serverLogs после проверки прав пользователя.
    """
    pool = dp["db_pool"]
    user_id = message.from_user.id
    user_language = await get_language(pool, message.chat.id)

    if not is_user_admin(user_id):
        return

    log_file = "serverLogs.txt"

    if not os.path.exists(log_file):
        await message.reply(server_translation["file_not_found"][user_language])
        return

    try:
        await message.answer_document(
            document=FSInputFile(log_file),
            caption=server_translation["logs"][user_language]
        )
    except TelegramBadRequest as e:
        await message.reply(server_translation["logs"][user_language].format(e=e))
        
async def send_log_from_users(bot: Bot, callback: CallbackQuery, dp):
    try:
        pool = dp["db_pool"]
        data = callback.data.split()
        file_path = data[1]
        chat_id = callback.message.chat.id
        business_connection_id = callback.message.business_connection_id
        chat_language = await get_language(pool, chat_id)
        
        if not os.path.exists(file_path):
            if callback.message.chat.type == "private":    
                await callback.answer(error_translation["old_error"][chat_language], show_alert=True)
            else: 
                await callback.bot.send_message(chat_id=chat_id, text=error_translation["old_error"][chat_language], business_connection_id=business_connection_id)
                
            await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=None,
                business_connection_id=business_connection_id
            )
            return
        
        await bot.send_document(
            chat_id=LOGS_ID,
            document=FSInputFile(file_path),
            caption=f"User ID: {callback.from_user.id}\nChat ID: {chat_id}"
        )
        
        await del_media_content(file_path)
        
        if callback.message.chat.type == "private":    
            await callback.answer(general_translation["success_send"][chat_language], show_alert=True)
        else: 
            await callback.bot.send_message(chat_id=chat_id, text=general_translation["success_send"][chat_language])
            
        await bot.edit_message_reply_markup(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=None,
            business_connection_id=business_connection_id
        )
    except Exception as e:
        print(e)