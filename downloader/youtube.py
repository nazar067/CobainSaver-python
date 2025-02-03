import yt_dlp
import os

from downloader.media import del_media_content, send_video
from user.get_user_path import get_user_path

MAX_SIZE_MB = 50 
MAX_RESOLUTION = "1080" 
QUALITIES = ["1080", "720", "480", "360", "240", "144"] 

async def download_youtube_video(bot, url: str, chat_id: int) -> str:
    """
    Скачивает видео с YouTube и сохраняет его в папку пользователя.
    """
    user_folder = await get_user_path(chat_id)

    for quality in QUALITIES:
        ydl_opts = {
            'format': f"bestvideo[height<={quality}]+bestaudio/best",
            'outtmpl': f'{user_folder}/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'quiet': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info_dict)

                if os.path.exists(file_path):
                    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    if file_size_mb <= MAX_SIZE_MB:
                        return await send_video(bot, chat_id, file_path)

                    await del_media_content(file_path)

        except Exception as e:
            return f"Ошибка при скачивании: {str(e)}"

    return "Ошибка: даже в минимальном качестве видео превышает 50MB."
