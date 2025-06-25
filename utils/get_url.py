import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


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

async def split_time_code_and_video(url: str):
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    time_code = "0"
    if "t" in query_params:
        time_value = query_params["t"][0]
        time_code = time_value

    query_params.pop("t", None)

    new_query = urlencode(query_params, doseq=True)
    url_without_time_code = urlunparse(parsed._replace(query=new_query))

    return {
        "url": url_without_time_code,
        "time_code": time_code
    }