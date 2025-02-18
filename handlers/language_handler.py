from aiogram.types import CallbackQuery

from localisation.get_language import get_language
from localisation.set_language import set_language
from localisation.translations.general import translations

async def set_language_handler(callback: CallbackQuery, pool):
    """
    Обработка нажатия кнопки для смены языка.
    """
    chat_id = callback.message.chat.id
    language_code = callback.data.split(":")[1].split(" ")[0]
    user_msg_id = callback.data.split(" ")[1]

    print(language_code)
    
    await set_language(pool, chat_id, language_code)
    chat_language = await get_language(pool, chat_id)
    
    await callback.bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.bot.delete_message(callback.message.chat.id, int(user_msg_id))

    await callback.answer(translations["success_lang"][chat_language], show_alert=True)
