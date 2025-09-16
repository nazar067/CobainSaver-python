import os
import asyncio
from pathlib import Path

from aiogram import Bot, Dispatcher

from config import INSTAGRAM_LOGIN, INSTAGRAM_PASSWORD
from constants.errors.telegram_errors import NOT_RIGHTS
from downloader.instagram.download_data import download_inst_post
from downloader.send_album import send_social_media_album
from keyboard import send_log_keyboard
from localisation.get_language import get_language
from logs.write_server_errors import log_error
from user.get_user_path import get_user_path
from utils.get_name import get_random_file_name
from localisation.translations.downloader import translations
from utils.service_identifier import identify_service

def _find_project_root(start: Path) -> Path:
    env_root = os.getenv("PROJECT_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        if p.exists():
            return p

    current = start.resolve()
    markers = {".git", "pyproject.toml", "requirements.txt"}
    for parent in [current, *current.parents]:
        try:
            listing = {p.name for p in parent.iterdir()}
        except Exception:
            listing = set()
        if markers & listing:
            return parent
    return current

_THIS_FILE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _find_project_root(_THIS_FILE_DIR)

async def fetch_instagram_content(
    bot: Bot,
    url: str,
    chat_id: int,
    dp: Dispatcher,
    business_connection_id,
    msg_id
):
    """Не блокирует event loop. Медиа — в get_user_path(chat_id), сессия — в корне проекта."""
    try:
        pool = dp["db_pool"]
        chat_language = await get_language(pool, chat_id)

        user_dir = await get_user_path(chat_id)
        os.makedirs(user_dir, exist_ok=True)

        session_path = str(_PROJECT_ROOT / "ig.session")

        random_name = (await get_random_file_name("")) + "insta"

        result = await download_inst_post(
            url=url,
            base_dir=user_dir,
            filename_pattern=random_name,
            login=INSTAGRAM_LOGIN,
            password=INSTAGRAM_PASSWORD,
            sessionfile=session_path,
        )

        matching_files = [
            os.path.join(user_dir, file) for file in os.listdir(user_dir) if random_name in file
        ]
        caption = result.get("caption", "") or ""

        if matching_files:
            return await send_social_media_album(
                bot,
                chat_id,
                chat_language,
                business_connection_id,
                matching_files,
                caption,
                msg_id,
                pool=pool
            )
        else:
            text = translations["unavaliable_content"][chat_language]
            kb = await send_log_keyboard(text, "Not found insta files", chat_language, chat_id, url)
            await bot.send_message(
                chat_id,
                text=text,
                reply_to_message_id=msg_id,
                business_connection_id=business_connection_id,
                reply_markup=kb
            )
            return False

    except Exception as e:
        try:
            svc = await identify_service(url)
        except Exception:
            svc = "instagram"

        await asyncio.to_thread(log_error, url, e, chat_id, svc)

        if NOT_RIGHTS in str(e):
            return False

        try:
            pool = dp["db_pool"]
            chat_language = await get_language(pool, chat_id)
        except Exception:
            chat_language = "en"

        text = translations["unavaliable_content"][chat_language]
        kb = await send_log_keyboard(text, str(e), chat_language, chat_id, url)
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_to_message_id=msg_id,
            business_connection_id=business_connection_id,
            reply_markup=kb
        )
        return False
