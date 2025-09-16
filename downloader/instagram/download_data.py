import os
import asyncio
import re
import time
import instaloader
from typing import Dict, Any, Optional
from pathlib import Path


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

def _download_inst_post_sync(
    url: str,
    base_dir: str,
    filename_pattern: str,
    login: Optional[str] = None,
    password: Optional[str] = None,
    sessionfile: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 1.5,
) -> Dict[str, Any]:
    os.makedirs(base_dir, exist_ok=True)

    loader = instaloader.Instaloader(
        dirname_pattern=base_dir,
        filename_pattern=filename_pattern,
        download_comments=False,
        download_geotags=False,
        download_pictures=True,
        download_video_thumbnails=False,
        save_metadata=False,
    )

    if sessionfile and os.path.exists(sessionfile):
        try:
            loader.load_session_from_file(login, sessionfile)
        except Exception:
            if login and password:
                loader.login(login, password)
                try:
                    loader.save_session_to_file(sessionfile)
                except Exception:
                    pass
    elif login and password:
        loader.login(login, password)
        try:
            if sessionfile:
                loader.save_session_to_file(sessionfile)
        except Exception:
            pass

    shortcode = _extract_shortcode(url)

    last_err = None
    post = None
    for _ in range(max_retries):
        try:
            post = instaloader.Post.from_shortcode(loader.context, shortcode)
            break
        except Exception as e:
            last_err = e
            time.sleep(retry_delay)
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