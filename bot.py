import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart
from config import API_TOKEN
from downloader.utils import choose_service, delete_not_url, identify_service

TOKEN = API_TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Привет! Отправь мне любое сообщение, и я отвечу!")

@dp.message()
async def echo_handler(message: Message):
    await choose_service(bot, message)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
