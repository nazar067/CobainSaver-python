import re


async def delete_not_url(message: str) -> str:
    """
    Фильтрует URL-адрес из сообщения.
    """
    regex_url = re.compile(r"\bhttps://\S+\b")

    regex_short_url = re.compile(r"youtu.be/\w+")

    match_url = regex_url.search(message)

    match_short_url = regex_short_url.search(message)

    if match_url:
        return match_url.group(0)

    if match_short_url:
        return "https://" + match_short_url.group(0)

    return ""