
import os
from urllib.parse import urlparse

from downloader.send_album import send_social_media_album
from utils.fetch_data import download_file
from utils.get_name import get_random_file_name


async def best_image_url(entry: dict) -> str:
    # в media_metadata для галерей: берём 's' (source) или наибольший 'p'
    if "s" in entry and "u" in entry["s"]:
        return entry["s"]["u"].replace("&amp;", "&")
    if "p" in entry and entry["p"]:
        return entry["p"][-1]["u"].replace("&amp;", "&")
    # fallback на id -> i.redd.it/id.jpg
    if "id" in entry:
        return f"https://i.redd.it/{entry['id']}.jpg"
    raise ValueError("No image url in media_metadata entry")

async def download_gallery(bot, chat_id, chat_language, business_connection_id, msg_id, pool, post: dict, dest_dir: str) -> list[str]:
    out = []
    order = [i["media_id"] for i in post.get("gallery_data", {}).get("items", [])]
    meta = post.get("media_metadata", {}) or {}
    title = post.get("title", "")
    for mid in order:
        entry = meta.get(mid)
        if not entry:
            continue
        url = await best_image_url(entry)
        ext = os.path.splitext(urlparse(url).path)[1] or ".jpg"
        random_name = await get_random_file_name("")
        path = os.path.join(dest_dir, f"{random_name}{ext}")
        await download_file(url, path)
        out.append(path)
    return await send_social_media_album(bot, chat_id, chat_language, business_connection_id, out, title, msg_id, False, pool=pool)