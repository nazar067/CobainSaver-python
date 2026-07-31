import asyncio
import html
import os
import shutil
import subprocess
from urllib.parse import urlparse

import requests
from aiogram import Bot, Dispatcher

from downloader.media import del_media_content, send_video
from localisation.get_language import get_language
from localisation.translations.downloader import translations
from user.get_user_path import get_user_path
from utils.fetch_data import download_file
from utils.get_name import get_random_file_name


UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
    "Gecko/20100101 Firefox/124.0"
)

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": UA,
        "Accept": "*/*",
        "Referer": "https://www.reddit.com/",
    }
)

MAX_DURATION_SECONDS = 20_000
MAX_FILE_SIZE_BYTES = 1_999 * 1024 * 1024


def _normalize_media_url(url: str | None) -> str | None:
    """
    Декодирует HTML-последовательности в URL Reddit.

    Например:
    &amp; -> &
    """
    if not url:
        return None

    normalized = html.unescape(url).strip()

    return normalized or None


def _extract_vreddit_id(url: str | None) -> str | None:
    """
    Извлекает ID видео из ссылки:

    https://v.redd.it/VIDEO_ID/...
    """
    if not url:
        return None

    parsed = urlparse(url)

    if parsed.netloc.lower() != "v.redd.it":
        return None

    path_parts = [
        part
        for part in parsed.path.split("/")
        if part
    ]

    if not path_parts:
        return None

    return path_parts[0]


def _extract_reddit_video(post: dict | None) -> dict | None:
    """
    Ищет reddit_video в:

    - secure_media;
    - media;
    - crosspost_parent_list;
    - preview.reddit_video_preview.
    """
    if not isinstance(post, dict):
        return None

    candidates = [post]

    crossposts = post.get("crosspost_parent_list")

    if isinstance(crossposts, list):
        candidates.extend(
            crosspost
            for crosspost in crossposts
            if isinstance(crosspost, dict)
        )

    for candidate in candidates:
        secure_media = candidate.get("secure_media") or {}
        media = candidate.get("media") or {}

        reddit_video = (
            secure_media.get("reddit_video")
            or media.get("reddit_video")
        )

        if isinstance(reddit_video, dict):
            return reddit_video

    preview = post.get("preview") or {}
    reddit_video_preview = preview.get(
        "reddit_video_preview"
    )

    if isinstance(reddit_video_preview, dict):
        return reddit_video_preview

    return None


def _safe_remove(path: str | None) -> None:
    if not path:
        return

    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def _download_file_sync(
    url: str,
    output_path: str,
) -> None:
    """
    Скачивает прямой MP4-файл.

    Используется для fallback_url, если DASH/HLS
    не удалось скачать через ffmpeg.
    """
    _safe_remove(output_path)

    with SESSION.get(
        url,
        stream=True,
        allow_redirects=True,
        timeout=(20, 180),
    ) as response:
        response.raise_for_status()

        with open(output_path, "wb") as output_file:
            for chunk in response.iter_content(
                chunk_size=128 * 1024
            ):
                if chunk:
                    output_file.write(chunk)

    if not os.path.exists(output_path):
        raise RuntimeError(
            "Файл Reddit-видео не был создан"
        )

    if os.path.getsize(output_path) == 0:
        _safe_remove(output_path)

        raise RuntimeError(
            "Reddit вернул пустой видеофайл"
        )


async def _download_file(
    url: str,
    output_path: str,
) -> None:
    await asyncio.to_thread(
        _download_file_sync,
        url,
        output_path,
    )


def _download_manifest_sync(
    manifest_url: str,
    output_path: str,
) -> None:
    """
    Скачивает DASH или HLS manifest через ffmpeg.

    DASH Reddit часто содержит отдельно:
    - видеодорожку;
    - аудиодорожку.

    ffmpeg автоматически скачивает и объединяет их.
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg не установлен или недоступен в PATH"
        )

    _safe_remove(output_path)

    request_headers = (
        f"User-Agent: {UA}\r\n"
        "Referer: https://www.reddit.com/\r\n"
        "Accept: */*\r\n"
    )

    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",

        # Тайм-аут сетевых операций в микросекундах.
        "-rw_timeout",
        "60000000",

        "-headers",
        request_headers,

        "-i",
        manifest_url,

        # Первая видеодорожка обязательна.
        "-map",
        "0:v:0",

        # Аудиодорожка необязательна.
        # Некоторые Reddit GIF не имеют звука.
        "-map",
        "0:a:0?",

        # Не перекодируем видео.
        "-c:v",
        "copy",

        # Для совместимости с Telegram.
        "-c:a",
        "aac",

        "-movflags",
        "+faststart",

        output_path,
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        _safe_remove(output_path)

        error_text = result.stderr.strip()

        if len(error_text) > 2000:
            error_text = error_text[-2000:]

        raise RuntimeError(
            "ffmpeg не смог скачать Reddit-видео. "
            f"Manifest={manifest_url}; "
            f"Error={error_text}"
        )

    if not os.path.exists(output_path):
        raise RuntimeError(
            "ffmpeg завершился без ошибки, "
            "но не создал видеофайл"
        )

    if os.path.getsize(output_path) == 0:
        _safe_remove(output_path)

        raise RuntimeError(
            "ffmpeg создал пустой видеофайл"
        )


async def _download_manifest(
    manifest_url: str,
    output_path: str,
) -> None:
    await asyncio.to_thread(
        _download_manifest_sync,
        manifest_url,
        output_path,
    )


def _get_video_duration(
    reddit_video: dict | None,
) -> int:
    if not reddit_video:
        return 0

    try:
        return int(
            float(reddit_video.get("duration") or 0)
        )
    except (TypeError, ValueError):
        return 0


def _get_thumbnail_url(
    post: dict | None,
) -> str | None:
    if not isinstance(post, dict):
        return None

    thumbnail = post.get("thumbnail")

    if (
        isinstance(thumbnail, str)
        and thumbnail.startswith(("http://", "https://"))
    ):
        return _normalize_media_url(thumbnail)

    preview = post.get("preview") or {}
    images = preview.get("images") or []

    if not isinstance(images, list) or not images:
        return None

    source = images[0].get("source") or {}
    preview_url = source.get("url")

    if isinstance(preview_url, str):
        return _normalize_media_url(preview_url)

    return None


async def _download_thumbnail(
    post: dict | None,
    save_folder: str,
    random_name: str,
) -> str | None:
    thumbnail_url = _get_thumbnail_url(post)

    if not thumbnail_url:
        return None

    thumbnail_path = os.path.join(
        save_folder,
        f"{random_name}_thumbnail.jpg",
    )

    try:
        await download_file(
            thumbnail_url,
            thumbnail_path,
        )

        if (
            os.path.exists(thumbnail_path)
            and os.path.getsize(thumbnail_path) > 0
        ):
            return thumbnail_path

    except Exception:
        _safe_remove(thumbnail_path)

    return None


async def _send_downloaded_video(
    bot: Bot,
    chat_id: int,
    msg_id: int,
    chat_language: str,
    business_connection_id,
    video_path: str,
    title: str,
    duration: int,
    post: dict | None,
    save_folder: str,
    random_name: str,
):
    if not os.path.exists(video_path):
        raise RuntimeError(
            "Скачанный Reddit-видеофайл не найден"
        )

    file_size = os.path.getsize(video_path)

    if file_size == 0:
        _safe_remove(video_path)

        raise RuntimeError(
            "Скачанный Reddit-видеофайл пустой"
        )

    if file_size >= MAX_FILE_SIZE_BYTES:
        await del_media_content(video_path)

        return await bot.send_message(
            chat_id=chat_id,
            business_connection_id=business_connection_id,
            text=translations["large_content"][
                chat_language
            ],
            reply_to_message_id=msg_id,
        )

    thumbnail_path = await _download_thumbnail(
        post,
        save_folder,
        random_name,
    )

    return await send_video(
        bot,
        chat_id,
        msg_id,
        chat_language,
        business_connection_id,
        video_path,
        title,
        thumbnail_path,
        duration,
        parse_mode="HTML",
    )


async def download_video_content(
    bot: Bot,
    url: str,
    chat_id: int,
    dp: Dispatcher,
    business_connection_id,
    msg_id: int,
    post: dict | None = None,
):
    """
    Скачивает Reddit-видео без yt-dlp.

    Для ссылки на пост передавайте OAuth-данные поста через post.

    Для прямой ссылки v.redd.it достаточно передать url.

    Порядок загрузки:
    1. DASH manifest.
    2. HLS manifest.
    3. fallback_url.
    """
    pool = dp["db_pool"]

    chat_language = await get_language(
        pool,
        chat_id,
    )

    save_folder = await get_user_path(chat_id)
    os.makedirs(save_folder, exist_ok=True)

    random_name = await get_random_file_name("")

    reddit_video = _extract_reddit_video(post)

    fallback_url: str | None = None
    dash_url: str | None = None
    hls_url: str | None = None

    if reddit_video:
        fallback_url = _normalize_media_url(
            reddit_video.get("fallback_url")
        )

        dash_url = _normalize_media_url(
            reddit_video.get("dash_url")
        )

        hls_url = _normalize_media_url(
            reddit_video.get("hls_url")
        )

    video_id = _extract_vreddit_id(url)

    if not video_id:
        video_id = _extract_vreddit_id(fallback_url)

    if not video_id:
        video_id = _extract_vreddit_id(dash_url)

    if not video_id:
        video_id = _extract_vreddit_id(hls_url)

    # Для прямых v.redd.it ссылок metadata поста может отсутствовать.
    # Тогда строим стандартные manifest URL по ID.
    if video_id:
        base_url = f"https://v.redd.it/{video_id}"

        if not dash_url:
            dash_url = (
                f"{base_url}/DASHPlaylist.mpd"
            )

        if not hls_url:
            hls_url = (
                f"{base_url}/HLSPlaylist.m3u8"
            )

    if not any(
        (
            dash_url,
            hls_url,
            fallback_url,
        )
    ):
        raise ValueError(
            "В Reddit-посте не найдено видео"
        )

    duration = _get_video_duration(reddit_video)

    if duration > MAX_DURATION_SECONDS:
        return await bot.send_message(
            chat_id=chat_id,
            business_connection_id=business_connection_id,
            text=translations["large_content"][
                chat_language
            ],
            reply_to_message_id=msg_id,
        )

    title = ""

    if isinstance(post, dict):
        title = post.get("title") or ""

    output_path = os.path.join(
        save_folder,
        f"{random_name}.mp4",
    )

    errors: list[str] = []

    # DASH обычно является лучшим вариантом,
    # потому что содержит видео и аудио.
    if shutil.which("ffmpeg"):
        manifests: list[tuple[str, str]] = []

        if dash_url:
            manifests.append(
                ("DASH", dash_url)
            )

        if hls_url and hls_url != dash_url:
            manifests.append(
                ("HLS", hls_url)
            )

        for manifest_type, manifest_url in manifests:
            try:
                await _download_manifest(
                    manifest_url,
                    output_path,
                )

                return await _send_downloaded_video(
                    bot=bot,
                    chat_id=chat_id,
                    msg_id=msg_id,
                    chat_language=chat_language,
                    business_connection_id=business_connection_id,
                    video_path=output_path,
                    title=title,
                    duration=duration,
                    post=post,
                    save_folder=save_folder,
                    random_name=random_name,
                )

            except Exception as error:
                errors.append(
                    f"{manifest_type}: {error}"
                )

                _safe_remove(output_path)

    else:
        errors.append(
            "ffmpeg не установлен"
        )

    # fallback_url обычно содержит только видеодорожку,
    # поэтому используется после DASH/HLS.
    if fallback_url:
        try:
            await _download_file(
                fallback_url,
                output_path,
            )

            return await _send_downloaded_video(
                bot=bot,
                chat_id=chat_id,
                msg_id=msg_id,
                chat_language=chat_language,
                business_connection_id=business_connection_id,
                video_path=output_path,
                title=title,
                duration=duration,
                post=post,
                save_folder=save_folder,
                random_name=random_name,
            )

        except Exception as error:
            errors.append(
                f"fallback: {error}"
            )

            _safe_remove(output_path)

    raise RuntimeError(
        "Не удалось скачать Reddit-видео. "
        + " | ".join(errors)
    )