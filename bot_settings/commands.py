from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeAllGroupChats
from localisation.translations.bot import translations as bot_translation

async def set_bot_commands(bot: Bot):
    """
    Устанавливает список команд бота с описаниями.
    """
    private_commands_en = [
        BotCommand(command="start", description=bot_translation["start_command_desc"]["en"]),
        BotCommand(command="changelang", description=bot_translation["changelang_command_desc"]["en"]),
        BotCommand(command="settings", description=bot_translation["settings_command_desc"]["en"]),
    ]
    private_commands_uk = [
        BotCommand(command="start", description=bot_translation["start_command_desc"]["uk"]),
        BotCommand(command="changelang", description=bot_translation["changelang_command_desc"]["uk"]),
        BotCommand(command="settings", description=bot_translation["settings_command_desc"]["uk"]),
    ]
    private_commands_ru = [
        BotCommand(command="start", description=bot_translation["start_command_desc"]["ru"]),
        BotCommand(command="changelang", description=bot_translation["changelang_command_desc"]["ru"]),
        BotCommand(command="settings", description=bot_translation["settings_command_desc"]["ru"]),
    ]

    await bot.set_my_commands(commands=private_commands_en, scope=BotCommandScopeDefault(), language_code="en")
    await bot.set_my_commands(commands=private_commands_uk, scope=BotCommandScopeDefault(), language_code="uk")
    await bot.set_my_commands(commands=private_commands_ru, scope=BotCommandScopeDefault(), language_code="ru")