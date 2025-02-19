from aiogram import Bot
from localisation.translations.bot import translations as bot_translation

async def set_bot_description(bot: Bot):
    """
    Устанавливает описание бота на нескольких языках.
    """
    await bot.set_my_description(
        description=bot_translation["description"]["en"],
        language_code="en"
    )
    await bot.set_my_description(
        description=bot_translation["description"]["uk"],
        language_code="uk"
    )
    await bot.set_my_description(
        description=bot_translation["description"]["ru"],
        language_code="ru"
    )