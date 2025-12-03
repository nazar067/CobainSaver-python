import os
import asyncio

from aiogram import Bot, Dispatcher
from downloader.media import send_audio
from localisation.get_language import get_language
from keyboard import send_log_keyboard
from localisation.translations.downloader import translations
from logs.write_server_errors import log_error
from user.get_user_path import get_user_path
from utils.get_name import get_random_file_name
from utils.service_identifier import identify_service

async def download_audio_gallerydl(
    bot: Bot,
    url: str,
    chat_id: int,
    dp: Dispatcher,
    business_connection_id,
    msg_id,
    audio_format: str = "m4a"
) -> str:
    """
    Скачивает аудио с TikTok (включая фото/галереи) через gallery-dl.
    Возвращает путь к скачанному аудио-файлу.
    """
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
            "-o", "directory=",
            "-o", f"filename={uniq_id}.{{extension}}",
            "-o", "extractor.extract-audio=true",
            "-o", f"extractor.audio-format={audio_format}",
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
            raise RuntimeError(f"gallery-dl timeout after 600s")

        if proc.returncode != 0:
            raise RuntimeError(
                f"gallery-dl failed (code {proc.returncode}).\n"
                f"STDOUT:\n{stdout.decode(errors='ignore')}\n"
                f"STDERR:\n{stderr.decode(errors='ignore')}"
            )

        after = set(os.listdir(save_dir))
        new_names = sorted(after - before)
        await asyncio.sleep(2)
        
        audio_extensions = ["mp3", "wav", "m4a", "aac", "ogg", "flac", "opus"]

        matching_files = [
            os.path.normpath(os.path.join(save_dir, file))
            for file in os.listdir(save_dir)
            if uniq_id in file and file.split(".")[-1].lower() in audio_extensions
        ]

        matching_files = [os.path.normpath(p) for p in matching_files]
        audio_path = matching_files[0]

        return await send_audio(
            bot, chat_id, msg_id, chat_language,
            business_connection_id, audio_path, "tiktok music",
            None, 0, author="CobainSaver", disableNotification=True
        )

    except Exception as e:
        await bot.send_message(
            chat_id=chat_id,
            business_connection_id=business_connection_id,
            text=translations["unavaliable_content"][chat_language],
            reply_to_message_id=msg_id,
            reply_markup=await send_log_keyboard(
                translations["unavaliable_content"][chat_language],
                e,
                chat_language,
                chat_id,
                url
            )
        )
        log_error(url, e, chat_id, await identify_service(url))
        return None
