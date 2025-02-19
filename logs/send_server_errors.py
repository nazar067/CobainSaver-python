import os
from aiogram.types import Message
from aiogram.types.input_file import FSInputFile
from aiogram.exceptions import TelegramBadRequest
from localisation.get_language import get_language
from localisation.translations.server import translations as server_translation

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