import os
import asyncio
from typing import List, Optional

from aiogram import Bot, Dispatcher

from downloader.send_album import send_social_media_album
from keyboard import send_log_keyboard
from localisation.get_language import get_language
from logs.write_server_errors import log_error
from user.get_user_path import get_user_path
from utils.get_name import get_random_file_name
from utils.service_identifier import identify_service
from localisation.translations.downloader import translations

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")

async def download_photo_content(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id, msg_id) -> List[str]:
    try:
        pool = dp["db_pool"]
        chat_language = await get_language(pool, chat_id)
        save_dir = await get_user_path(chat_id)
        uniq_id = await get_random_file_name("")
        os.makedirs(save_dir, exist_ok=True)

        before = set(os.listdir(save_dir))
        
        cmd = [
            "gallery-dl",
            "-d", save_dir,
            "--filter", "extension in ('jpg','jpeg','png','webp')",
            "-o", "directory=",
            "-o", f"filename={uniq_id}_{{num}}.{{extension}}",
            url,
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError(f"gallery-dl timeout after {600}s")

        if proc.returncode != 0:
            raise RuntimeError(
                f"gallery-dl failed (code {proc.returncode}).\n"
                f"STDOUT:\n{stdout.decode(errors='ignore')}\n"
                f"STDERR:\n{stderr.decode(errors='ignore')}"
            )

        after = set(os.listdir(save_dir))
        new_names = sorted(after - before)

        new_paths = [os.path.join(save_dir, name) for name in new_names]
        new_paths = [p for p in new_paths if p.lower().endswith(IMAGE_EXTS)]

        new_paths.sort()
        new_paths.sort(key=lambda p: os.path.getmtime(p))

        return await send_social_media_album(bot, chat_id, chat_language, business_connection_id, new_paths, "test", msg_id, False, pool=pool)
    except Exception as e:
        await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["unavaliable_content"][chat_language], reply_to_message_id=msg_id, reply_markup=await send_log_keyboard(translations["unavaliable_content"][chat_language], e, chat_language, chat_id, url))
        log_error(url, e, chat_id, await identify_service(url))
        return False