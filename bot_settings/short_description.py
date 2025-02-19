from aiogram import Bot
from localisation.translations.bot import translations as bot_translation

async def set_bot_short_description(bot: Bot):
    """
    Устанавливает краткое описание бота (Info) на нескольких языках.
    """
    await bot.set_my_short_description(
        short_description=bot_translation["short_description"]["en"],
        language_code="en"
    )
    await bot.set_my_short_description(
        short_description=bot_translation["short_description"]["uk"],
        language_code="uk"
    )
    await bot.set_my_short_description(
        short_description=bot_translation["short_description"]["ru"],
        language_code="ru"
    )