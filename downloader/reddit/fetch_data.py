import os
import re
import json
import shutil
import subprocess
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs
from aiogram import Bot, Dispatcher
import requests

from downloader.media import send_gif, send_video
from downloader.reddit.photo_download import download_gallery
from downloader.reddit.video_download import download_video_content
from downloader.send_album import send_social_media_album
from keyboard import send_log_keyboard
from localisation.get_language import get_language
from logs.write_server_errors import log_error
from user.get_user_path import get_user_path
from utils.fetch_data import download_file
from utils.get_name import get_random_file_name
from localisation.translations.downloader import translations
from utils.get_url import resolve_reddit_url

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
      "Gecko/20100101 Firefox/124.0")
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})

def _ensure_dir(d: str):
    os.makedirs(d, exist_ok=True)

async def _get_json_for_post(url: str) -> dict | None:
    """
    Возвращает JSON (первый элемент ленты поста) для ссылок вида reddit.com/... .
    """
    # Нормализация: уберём хвосты типа ?utm_source=...
    p = urlparse(url)
    if not p.netloc:
        return None
    # если это уже .json — используем как есть
    if p.path.endswith(".json"):
        json_url = urlunparse((p.scheme or "https", p.netloc, p.path, "", "raw_json=1", ""))
    else:
        # добавим .json к пути поста
        path = p.path
        if not path.endswith("/"):
            path += "/"
        path += ".json"
        json_url = urlunparse((p.scheme or "https", p.netloc, path, "", "raw_json=1", ""))

    r = SESSION.get(json_url, timeout=20)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list) and data:
        # первый элемент — список постов, берём первый пост
        post = data[0]["data"]["children"][0]["data"]
        return post
    return None

async def _download(url: str, out_path: str):
    with SESSION.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(1 << 14):
                if chunk:
                    f.write(chunk)

def _ffmpeg_exists() -> bool:
    return shutil.which("ffmpeg") is not None

async def _merge_av(video_path: str, audio_path: str, out_path: str):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c", "copy",
        out_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

async def _guess_audio_from_fallback(fallback_url: str) -> str | None:
    """
    Для v.redd.it часто есть аудио по шаблону .../DASH_audio.mp4.
    Пробуем заменить DASH_1080.mp4 -> DASH_audio.mp4 и скачать.
    """
    m = re.search(r"(https://v\.redd\.it/[^/]+)/DASH_[^/?#]+\.mp4", fallback_url)
    if not m:
        return None
    base = m.group(1)
    return base + "/DASH_audio.mp4"

async def _download_reddit_video(bot, chat_id, msg_id, chat_language, business_connection_id, post: dict, dest_dir: str, random_name: str):
    """
    Качает видео с v.redd.it. Если есть аудио — пытается склеить (нужен ffmpeg).
    """
    rv = (post.get("secure_media") or post.get("media") or {}).get("reddit_video") \
         or post.get("preview", {}).get("reddit_video_preview")
    if not rv:
        # иногда «fallback_url» лежит глубже или отсутствует
        raise ValueError("No reddit_video in post")

    video_title = post.get("title", "")
    fallback = rv.get("fallback_url")
    dash_url = rv.get("dash_url")
    if not fallback and dash_url:
        # некоторые посты имеют только dash_url — возьмём 720p трек как fallback
        # но чаще fallback присутствует. Если нет — можно скачать dash через ffmpeg/yt-dlp.
        fallback = dash_url

    if not fallback:
        raise ValueError("No fallback_url/dash_url for reddit video")

    # Скачаем видео-трек
    v_ext = ".mp4" if ".mp4" in fallback else ".mp4"
    v_path = os.path.join(dest_dir, f"{random_name}_video{v_ext}")
    await _download(fallback, v_path)

    # Попробуем достать аудио
    merged = []
    #a_url = await _guess_audio_from_fallback(fallback)
    # if a_url:
    #     try:
    #         a_path = os.path.join(dest_dir, f"{random_name}_audio.mp4")
    #         await _download(a_url, a_path)
    #         if _ffmpeg_exists():
    #             out_path = os.path.join(dest_dir, f"{random_name}.mp4")
    #             await _merge_av(v_path, a_path, out_path)
    #             merged.append(out_path)
    #             # можно оставить исходники, но чаще их удаляют:
    #             # os.remove(v_path); os.remove(a_path)
    #             return merged
    #         else:
    #             # ffmpeg нет — вернём раздельные дорожки
    #             return [v_path, a_path]
    #     except requests.HTTPError:
    #         print("No audio track found")
    #         # аудио может отсутствовать (немые клипы)
    #         pass

    # вернём хотя бы «тихий» mp4
    return await send_video(bot, chat_id, msg_id, chat_language, business_connection_id, v_path, video_title, None, 0, parse_mode="HTML")

async def download_reddit_media(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id, msg_id) -> list[str]:
    try:
        """
        Принимает ссылку на пост Reddit ИЛИ прямую ссылку на i.redd.it/v.redd.it,
        скачивает фото/видео. Возвращает список путей к сохранённым файлам.
        """
        pool = dp["db_pool"]
        chat_language = await get_language(pool, chat_id)
        dest_dir = await get_user_path(chat_id)
        _ensure_dir(dest_dir)

        # --- Новая часть: нормализуем ссылку ---
        canonical, json_url = await resolve_reddit_url(url)
        p = urlparse(canonical)

        # 1) Прямые ссылки на i.redd.it (картинка)
        if p.netloc in {"i.redd.it", "preview.redd.it"}:
            name = await get_random_file_name("")
            if not os.path.splitext(name)[1]:
                name += ".jpg"
            out = os.path.join(dest_dir, name)
            await download_file(canonical, out)
            return [out]

        # 2) Прямые ссылки на v.redd.it (видео)
        if p.netloc == "v.redd.it":
            return await download_video_content(bot, canonical, chat_id, dp, business_connection_id, msg_id)

        # 3) Ссылка на пост reddit.com/... — берём JSON
        if json_url:
            resp = SESSION.get(json_url, timeout=20)
            ctype = resp.headers.get("Content-Type", "")
            if "application/json" not in ctype:
                raise ValueError(f"Not a JSON response (Content-Type={ctype})")

            data = resp.json()
            post = data[0]["data"]["children"][0]["data"]
            if not post:
                raise ValueError("Не удалось получить JSON поста")

            random_name = await get_random_file_name("")

            # Галерея
            if post.get("is_gallery") and post.get("media_metadata"):
                return await download_gallery(bot, chat_id, chat_language, business_connection_id, msg_id, pool, post, dest_dir)

            # Одиночная картинка
            media_url = post.get("url_overridden_by_dest") or post.get("url")
            if media_url and urlparse(media_url).netloc in {"i.redd.it", "preview.redd.it"}:
                ext = os.path.splitext(urlparse(media_url).path)[1] or ".jpg"
                out_path = os.path.join(dest_dir, f"{random_name}{ext}")
                await download_file(media_url, out_path)
                if ext.lower() in {".gif", ".gifv"}:
                    return await send_gif(bot, chat_id, msg_id, chat_language, business_connection_id,
                                          out_path, post.get("title", ""), None, "HTML")
                else:
                    await send_social_media_album(bot, chat_id, chat_language, business_connection_id,
                                                  out_path, post.get("title", ""), msg_id, False, pool=pool)

            # GIF через reddit_video_preview (будет mp4)
            if post.get("preview", {}).get("reddit_video_preview"):
                return await _download_reddit_video(bot, chat_id, msg_id, chat_language,
                                                    business_connection_id, post, dest_dir, random_name)

            # Видео reddit
            if (post.get("secure_media") or post.get("media")) and (
                (post.get("secure_media") or {}).get("reddit_video") or
                (post.get("media") or {}).get("reddit_video")
            ):
                return await download_video_content(bot, canonical, chat_id, dp, business_connection_id, msg_id)

    except Exception as e:
        log_error(url, e, chat_id, "Reddit")
        return await bot.send_message(
            chat_id=chat_id,
            business_connection_id=business_connection_id,
            text=translations["unavaliable_content"][chat_language],
            reply_to_message_id=msg_id,
            reply_markup=await send_log_keyboard(
                translations["unavaliable_content"][chat_language],
                str(e),
                chat_language,
                chat_id,
                url
            )
        )
