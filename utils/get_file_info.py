import os
import re
import subprocess
from typing import Optional, Tuple, Union, List
from aiogram.types import InputMediaPhoto, InputMediaVideo, FSInputFile

async def get_music_size(bit_rate_kbps: int, duration_seconds: int) -> float:
    size_mb = (bit_rate_kbps * duration_seconds) / (8 * 1024)
    return size_mb
    
async def get_video_width_height(
    media: Optional[Union[str, FSInputFile, List[Union[InputMediaPhoto, InputMediaVideo]]]]
) -> Optional[Tuple[int, int]]:
    if media is None:
        return None

    path = None

    # list
    if isinstance(media, list) and media:
        first = media[0]
        if isinstance(first, InputMediaVideo):
            if isinstance(first.media, str) and os.path.exists(first.media):
                path = first.media
        elif isinstance(first, InputMediaPhoto):
            return None

    # str
    if isinstance(media, str) and os.path.exists(media):
        path = media

    if isinstance(media, FSInputFile) and os.path.exists(media.path):
        path = media.path

    if not path:
        return None

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0",
                path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        out = (result.stdout or "").strip()
        if not out:
            return None

        first_line = out.splitlines()[0].strip()
        m = re.search(r"(\d+)\s*x\s*(\d+)", first_line)
        if not m:
            return None

        w, h = int(m.group(1)), int(m.group(2))
        return w, h

    except Exception as ex:
        print(ex)
        return 180, 320
    
def extract_index(path):
    name = os.path.basename(path)
    m = re.match(r"(\d+)", name)
    return int(m.group(1)) if m else 0 