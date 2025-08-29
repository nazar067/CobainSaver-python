# utils/soundcloud_helper_async_light.py
import re
import time
import asyncio
from typing import Optional, Tuple, List

import aiohttp
from aiohttp import ClientTimeout

from logs.write_server_errors import log_error

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
        "Gecko/20100101 Firefox/124.0"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://soundcloud.com/",
    "Origin": "https://soundcloud.com",
    "Connection": "keep-alive",
}

CLIENT_ID_RE = re.compile(r'client_id\s*[:=]\s*"([0-9A-Za-z]{32})"')
APP_VERSION_RE = re.compile(r'app_version\s*[:=]\s*"(\d{10})"')
ASSET_RE = re.compile(r'src="(https://a-v2\.sndcdn\.com/assets/[^"]+\.js)"')

# --------- КЭШ БЕЗ ХУКОВ ---------
class _ClientIdCache:
    def __init__(self, ttl_sec: int = 1800):
        self.client_id: Optional[str] = None
        self.app_version: Optional[str] = None
        self.expires_at: float = 0.0
        self.ttl_sec = ttl_sec
        self._lock = asyncio.Lock()

    def _valid(self) -> bool:
        return self.client_id is not None and time.time() < self.expires_at

    async def get(self, session: aiohttp.ClientSession) -> Tuple[str, Optional[str]]:
        if self._valid():
            return self.client_id, self.app_version
        async with self._lock:
            if self._valid():
                return self.client_id, self.app_version
            cid, ver = await _fetch_client_id_and_version(session)
            self.client_id, self.app_version = cid, ver
            self.expires_at = time.time() + self.ttl_sec
            return cid, ver

_CLIENT_CACHE = _ClientIdCache(ttl_sec=1800)

# --------- ВНУТРЕННЕЕ: ДОБЫВАЕМ client_id ПАРАЛЛЕЛЬНО ---------
async def _fetch_client_id_and_version(session: aiohttp.ClientSession) -> Tuple[str, Optional[str]]:
    async with session.get("https://soundcloud.com") as r:
        html = await r.text()

    script_urls: List[str] = ASSET_RE.findall(html)
    if not script_urls:
        await asyncio.to_thread(log_error, "url", None, 1111, "Soundcloud", f"Не удалось найти JS-ассеты SoundCloud")
        return None, None

    script_urls = script_urls[:8]  # обычно хватает первых нескольких

    async def load_js(url: str) -> str:
        try:
            async with session.get(url) as r:
                return await r.text()
        except Exception:
            return ""

    js_texts = await asyncio.gather(*(load_js(u) for u in script_urls), return_exceptions=False)

    client_id: Optional[str] = None
    app_version: Optional[str] = None

    for js in js_texts:
        if not client_id:
            m = CLIENT_ID_RE.search(js)
            if m:
                client_id = m.group(1)
        if not app_version:
            v = APP_VERSION_RE.search(js)
            if v:
                app_version = v.group(1)
        if client_id and app_version:
            break

    if not client_id:
        await asyncio.to_thread(log_error, "url", None, 1111, "Soundcloud", f"client_id не найден")

    return client_id, app_version

# --------- ПУБЛИЧНЫЕ ФУНКЦИИ (БЕЗ ХУКОВ/ГЛОБАЛЬНЫХ СЕССИЙ) ---------
async def get_soundcloud_url(track_id: str) -> str:
    """
    Возвращает permalink_url трека по ID.
    Эта функция сама создаёт/закрывает aiohttp-сессию (без хуков).
    """
    timeout = ClientTimeout(total=20)
    async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as session:
        try:
            client_id, app_version = await _CLIENT_CACHE.get(session)
            params = {"client_id": client_id, "app_locale": "en"}
            if app_version:
                params["app_version"] = app_version

            api = f"https://api-v2.soundcloud.com/tracks/{track_id}"
            async with session.get(api, params=params) as resp:
                if resp.status == 403:
                    await asyncio.to_thread(log_error, "url", None, 1111, "Soundcloud", 403)
                    return "None"
                if resp.status != 200:
                    await asyncio.to_thread(log_error, "url", None, 1111, "Soundcloud", resp.status)
                    return "None"
                data = await resp.json()
                return data.get("permalink_url", "None")
        except Exception as e:
            await asyncio.to_thread(log_error, "url", None, 1111, "Soundcloud", f"exception:{e}")
            return "None"

async def get_soundcloud_playlist_url(playlist_id: str) -> str:
    """
    Возвращает permalink_url плейлиста по ID.
    Эта функция тоже сама создаёт/закрывает сессию (без хуков).
    """
    timeout = ClientTimeout(total=20)
    async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as session:
        try:
            client_id, app_version = await _CLIENT_CACHE.get(session)
            params = {"client_id": client_id, "app_locale": "en"}
            if app_version:
                params["app_version"] = app_version

            api = f"https://api-v2.soundcloud.com/playlists/{playlist_id}"
            async with session.get(api, params=params) as resp:
                if resp.status == 403:
                    await asyncio.to_thread(log_error, "url", None, 1111, "Soundcloud", 403)
                    return "None"
                if resp.status != 200:
                    await asyncio.to_thread(log_error, "url", None, 1111, "Soundcloud", resp.status)
                    return "None"
                data = await resp.json()
                return data.get("permalink_url", "None")
        except Exception as e:
            await asyncio.to_thread(log_error, "url", None, 1111, "Soundcloud", f"exception:{e}")
            return "None"
