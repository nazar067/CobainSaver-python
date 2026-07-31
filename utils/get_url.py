import asyncio
import html
import re
from urllib.parse import (
    parse_qs,
    parse_qsl,
    urlencode,
    urljoin,
    urlparse,
    urlunparse,
)

import requests


UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
    "Gecko/20100101 Firefox/124.0"
)

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": UA,
        "Accept": (
            "text/html,application/xhtml+xml,application/json;"
            "q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
)


# Reddit-ссылка с обычным comments-путём:
# /r/subreddit/comments/POST_ID/title/
# /comments/POST_ID/
_REDDIT_POST_ID_RE = re.compile(
    r"/comments/([a-zA-Z0-9]+)(?:/|$|\.json)",
    re.IGNORECASE,
)

# Canonical URL внутри HTML
_CANONICAL_URL_RE = re.compile(
    r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

# Альтернативный порядок атрибутов canonical
_CANONICAL_URL_RE_REVERSED = re.compile(
    r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']',
    re.IGNORECASE,
)

# og:url внутри HTML
_OG_URL_RE = re.compile(
    r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)

# Альтернативный порядок атрибутов og:url
_OG_URL_RE_REVERSED = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:url["\']',
    re.IGNORECASE,
)

# HTML meta refresh
_META_REFRESH_RE = re.compile(
    r'<meta[^>]+http-equiv=["\']?refresh["\']?[^>]+'
    r'content=["\']?\s*\d+\s*;\s*url=([^"\'>\s]+)',
    re.IGNORECASE,
)

# Любая Reddit-ссылка на comments внутри HTML
_COMMENTS_URL_IN_HTML_RE = re.compile(
    r'https?://(?:www\.|old\.|new\.)?reddit\.com/'
    r'[^"\'>\s]*comments/[a-zA-Z0-9]+[^"\'>\s]*',
    re.IGNORECASE,
)


async def delete_not_url(message: str) -> str:
    """
    Извлекает URL из сообщения.
    """
    regex_url = re.compile(r"\bhttps?://[^\s<>]+", re.IGNORECASE)
    regex_short_url = re.compile(r"\byoutu\.be/[^\s<>]+", re.IGNORECASE)

    match_url = regex_url.search(message)
    if match_url:
        return match_url.group(0).rstrip(".,;!?)\"'")

    match_short_url = regex_short_url.search(message)
    if match_short_url:
        return (
            "https://"
            + match_short_url.group(0).rstrip(".,;!?)\"'")
        )

    return ""


async def split_time_code_and_video(url: str):
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    def _parse_time_to_seconds(t: str) -> int:
        if not t:
            return 0

        t = t.strip().lower()

        if t.isdigit():
            return int(t)

        match = re.fullmatch(
            r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?",
            t,
        )

        if match and any(group is not None for group in match.groups()):
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)

            return hours * 3600 + minutes * 60 + seconds

        total = 0

        for value, unit in re.findall(r"(\d+)\s*([hms])", t):
            number = int(value)

            if unit == "h":
                total += number * 3600
            elif unit == "m":
                total += number * 60
            else:
                total += number

        return total

    time_code = "0"

    if "t" in query_params and query_params["t"]:
        raw_time = query_params["t"][0]
        time_code = str(_parse_time_to_seconds(raw_time))

    query_params.pop("t", None)

    new_query = urlencode(query_params, doseq=True)
    url_without_time_code = urlunparse(
        parsed._replace(query=new_query)
    )

    return {
        "url": url_without_time_code,
        "time_code": time_code,
    }


def _normalize_url(url: str) -> str:
    """
    Добавляет схему и удаляет пробелы.
    """
    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url


async def _strip_tracking(url: str) -> str:
    """
    Удаляет UTM и другие необязательные параметры отслеживания.
    """
    url = _normalize_url(url)
    parsed = urlparse(url)

    filtered_query = []

    for key, value in parse_qsl(
        parsed.query,
        keep_blank_values=True,
    ):
        lower_key = key.lower()

        if lower_key.startswith("utm_"):
            continue

        if lower_key in {
            "ref",
            "ref_source",
            "mweb_nav",
            "share_id",
            "context",
        }:
            continue

        filtered_query.append((key, value))

    return urlunparse(
        (
            parsed.scheme or "https",
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(filtered_query, doseq=True),
            "",
        )
    )


def _extract_post_id(url: str) -> str | None:
    """
    Извлекает ID Reddit-поста из обычной ссылки или redd.it.
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path

    match = _REDDIT_POST_ID_RE.search(path)
    if match:
        return match.group(1)

    if host in {"redd.it", "www.redd.it"}:
        parts = [
            part
            for part in path.split("/")
            if part
        ]

        if parts:
            return parts[0]

    return None


def _extract_url_from_html(
    html_text: str,
    base_url: str,
) -> str | None:
    """
    Пытается найти реальный URL поста внутри HTML.
    """
    patterns = (
        _CANONICAL_URL_RE,
        _CANONICAL_URL_RE_REVERSED,
        _OG_URL_RE,
        _OG_URL_RE_REVERSED,
    )

    for pattern in patterns:
        match = pattern.search(html_text)

        if match:
            candidate = html.unescape(match.group(1))
            candidate = urljoin(base_url, candidate)

            if _extract_post_id(candidate):
                return candidate

    match = _META_REFRESH_RE.search(html_text)

    if match:
        candidate = html.unescape(match.group(1))
        candidate = urljoin(base_url, candidate)

        if _extract_post_id(candidate):
            return candidate

    match = _COMMENTS_URL_IN_HTML_RE.search(html_text)

    if match:
        return html.unescape(match.group(0))

    return None


async def _extract_redirect_from_html(
    html_text: str,
    base_url: str,
) -> str | None:
    """
    Совместимая async-обёртка для старых вызовов функции.
    """
    return _extract_url_from_html(html_text, base_url)


async def _canonicalize_post_url(url: str) -> str:
    """
    Приводит Reddit-ссылку к стабильному canonical URL.
    """
    url = await _strip_tracking(url)
    post_id = _extract_post_id(url)

    if post_id:
        return f"https://www.reddit.com/comments/{post_id}/"

    parsed = urlparse(url)

    path = parsed.path
    if not path.endswith("/"):
        path += "/"

    return urlunparse(
        (
            "https",
            "www.reddit.com",
            path,
            "",
            "",
            "",
        )
    )


def _resolve_reddit_request(url: str) -> tuple[str, str]:
    """
    Синхронно раскрывает Reddit-ссылку.

    Возвращает:
    - финальный URL после HTTP-редиректов;
    - HTML ответа.
    """
    response = SESSION.get(
        url,
        allow_redirects=True,
        timeout=20,
    )

    response.raise_for_status()

    return response.url, response.text


async def resolve_reddit_url(url: str) -> tuple[str, str]:
    """
    Принимает Reddit-ссылку любого поддерживаемого вида:

    - reddit.com/r/.../comments/...
    - reddit.com/r/.../s/...
    - redd.it/POST_ID
    - old.reddit.com
    - new.reddit.com
    - i.redd.it
    - preview.redd.it
    - v.redd.it

    Возвращает:

    canonical_post_url:
        https://www.reddit.com/comments/POST_ID/

    post_json_url:
        https://www.reddit.com/comments/POST_ID.json?raw_json=1

    Для прямых медиа-ссылок JSON URL будет пустой строкой.
    """
    url = await _strip_tracking(url)
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    direct_media_hosts = {
        "i.redd.it",
        "preview.redd.it",
        "external-preview.redd.it",
        "v.redd.it",
    }

    if host in direct_media_hosts:
        return url, ""

    # Для обычных comments-ссылок и redd.it запрос не нужен.
    post_id = _extract_post_id(url)

    if post_id:
        canonical = f"https://www.reddit.com/comments/{post_id}/"
        json_url = (
            f"https://oauth.reddit.com/comments/"
            f"{post_id}?raw_json=1&limit=1"
        )

        return canonical, json_url

    # Ссылки вида /r/Subreddit/s/ABC нужно раскрыть через GET.
    try:
        final_url, response_html = await asyncio.to_thread(
            _resolve_reddit_request,
            url,
        )
    except requests.RequestException as error:
        raise ValueError(
            f"Не удалось раскрыть Reddit-ссылку: {url}. "
            f"Ошибка запроса: {error}"
        ) from error

    final_url = await _strip_tracking(final_url)

    # Сначала пробуем получить ID из URL после HTTP-редиректа.
    post_id = _extract_post_id(final_url)

    # Иногда Reddit возвращает HTML без нормального HTTP-редиректа.
    if not post_id:
        html_url = _extract_url_from_html(
            response_html,
            final_url,
        )

        if html_url:
            final_url = await _strip_tracking(html_url)
            post_id = _extract_post_id(final_url)

    if not post_id:
        raise ValueError(
            "Не удалось определить ID Reddit-поста. "
            f"Исходный URL: {url}; "
            f"финальный URL: {final_url}"
        )

    canonical = f"https://www.reddit.com/comments/{post_id}/"
    json_url = (
        f"https://oauth.reddit.com/comments/"
        f"{post_id}?raw_json=1&limit=1"
    )

    return canonical, json_url