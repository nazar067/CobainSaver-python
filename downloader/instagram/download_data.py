import os
import asyncio
import re
import time
from aiogram import Dispatcher
import instaloader
from typing import Dict, Any, Optional
from pathlib import Path

class InstagramRateLimited(Exception):
    pass

_SHORTCODE_RE = re.compile(
    r"(?:https?://)?(?:www\.)?instagram\.com/(?:(?:p|reel|tv)/([A-Za-z0-9_-]+))",
    re.IGNORECASE,
)

def _extract_shortcode(url: str) -> str:
    url = url.strip()
    m = _SHORTCODE_RE.search(url)
    if m:
        return m.group(1)
    parts = url.rstrip("/").split("/")
    if len(parts) >= 2:
        return parts[-2]
    raise ValueError(f"Cannot extract shortcode from URL: {url}")

_IG_MIN_INTERVAL_SEC_DEFAULT = 8.0 
_IG_SEMAPHORE_DEFAULT = asyncio.Semaphore(1)

def _get_dp_sem_and_throttle(dp: Dispatcher):
    sem = dp.get("ig_semaphore") or _IG_SEMAPHORE_DEFAULT
    dp["ig_semaphore"] = sem
    min_interval = dp.get("ig_min_interval") or _IG_MIN_INTERVAL_SEC_DEFAULT
    dp["ig_min_interval"] = min_interval
    return sem, float(min_interval)

def _enforce_min_interval(dp: Dispatcher):
    now = time.time()
    last = dp.get("ig_last_call_ts")
    min_interval = float(dp.get("ig_min_interval") or _IG_MIN_INTERVAL_SEC_DEFAULT)
    if last is not None:
        delta = now - float(last)
        wait = min_interval - delta
        if wait > 0:
            time.sleep(wait)
    dp["ig_last_call_ts"] = time.time()

# -------- sync worker --------
def _download_inst_post_sync(
    url: str,
    base_dir: str,
    filename_pattern: str,
    login: Optional[str] = None,
    password: Optional[str] = None,
    sessionfile: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> Dict[str, Any]:
    from instaloader.exceptions import (
        LoginRequiredException,
        BadCredentialsException,
        TwoFactorAuthRequiredException,
        ConnectionException,
        QueryReturnedNotFoundException,
        InvalidArgumentException,
    )

    os.makedirs(base_dir, exist_ok=True)

    loader = instaloader.Instaloader(
        dirname_pattern=base_dir,
        filename_pattern=filename_pattern,
        download_comments=False,
        download_geotags=False,
        download_pictures=True,
        download_video_thumbnails=False,
        save_metadata=False,
        max_connection_attempts=1,  # меньше агрессии к IG (NEW)
        request_timeout=30.0,       # (NEW)
        compress_json=False,        # (NEW) иногда снижает «подозрительность»
    )

    def _load_session_or_login():
        """Сначала пробуем сессию; если нет — один логин. При 401 НЕ логинимся заново."""
        if sessionfile and os.path.exists(sessionfile):
            try:
                loader.load_session_from_file(login, sessionfile)
                return
            except Exception:
                pass
        if login and password:
            loader.login(login, password)
            try:
                if sessionfile:
                    loader.save_session_to_file(sessionfile)
            except Exception:
                pass

    _load_session_or_login()

    shortcode = _extract_shortcode(url)

    # Экспоненциальный backoff
    attempt = 0
    delay = retry_delay
    post = None
    last_err = None

    while attempt < max_retries:
        attempt += 1
        try:
            post = instaloader.Post.from_shortcode(loader.context, shortcode)
            break
        except LoginRequiredException as e:
            # Это может быть «сессия протухла», но частый релогин = быстрое 401.
            # Дадим одну попытку принудительного логина только ЕСЛИ ещё не логинились в этом ранe.
            last_err = e
            if login and password and not (sessionfile and os.path.exists(sessionfile)):
                # первый запуск без сессии -> пробовали логин; сюда попадём редко
                try:
                    loader.login(login, password)
                    if sessionfile:
                        try:
                            loader.save_session_to_file(sessionfile)
                        except Exception:
                            pass
                    continue
                except Exception as le:
                    last_err = le
            # иначе просто backoff
            time.sleep(delay)
            delay *= 2
        except ConnectionException as e:
            last_err = e
            msg = str(e).lower()
            if "please wait a few minutes" in msg or "429" in msg or "401" in msg:
                # Явная блокировка rate limit -> бросаем спец-исключение
                raise InstagramRateLimited(str(e))
            time.sleep(delay)
            delay *= 2
        except QueryReturnedNotFoundException as e:
            last_err = e
            # Иногда IG маскирует throttling как 404 -> backoff
            time.sleep(delay)
            delay *= 2
        except (InvalidArgumentException, BadCredentialsException, TwoFactorAuthRequiredException) as e:
            raise e
        except Exception as e:
            last_err = e
            time.sleep(delay)
            delay *= 2

    if post is None:
        raise last_err or RuntimeError("Failed to fetch post metadata")

    loader.download_post(post, target=shortcode)
    target_dir = os.path.join(base_dir, shortcode)

    media_exts = {".jpg", ".jpeg", ".png", ".mp4", ".webp"}
    files = []
    if os.path.isdir(target_dir):
        for f in os.listdir(target_dir):
            p = os.path.join(target_dir, f)
            if os.path.isfile(p) and os.path.splitext(f)[1].lower() in media_exts:
                files.append(p)

    return {
        "shortcode": shortcode,
        "target_dir": target_dir,
        "files": sorted(files),
        "is_video": post.is_video,
        "caption": (post.caption or "").strip(),
    }

async def download_inst_post(
    url: str,
    base_dir: str,
    filename_pattern: str,
    login: Optional[str] = None,
    password: Optional[str] = None,
    sessionfile: Optional[str] = None,
) -> Dict[str, Any]:
    return await asyncio.to_thread(
        _download_inst_post_sync,
        url,
        base_dir,
        filename_pattern,
        login,
        password,
        sessionfile,
    )
