import re
import re
import html
from urllib.parse import urlparse, urlunparse, urljoin, parse_qsl, urlencode
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
      "Gecko/20100101 Firefox/124.0")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})

# --- Вспомогательные парсеры для HTML-редиректов (когда нет 30x) ---
_meta_refresh_re = re.compile(
    r'<meta[^>]+http-equiv=["\']?refresh["\']?[^>]+content=["\']?\s*\d+\s*;\s*url=([^"\'>\s]+)',
    re.IGNORECASE
)
_href_re = re.compile(r'<a[^>]+href=["\']([^"\']+)["\']', re.IGNORECASE)
_og_url_re = re.compile(
    r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE
)


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
        if time_value.endswith("s"):
            time_value = time_value[:-1]
        time_code = time_value

    query_params.pop("t", None)

    new_query = urlencode(query_params, doseq=True)
    url_without_time_code = urlunparse(parsed._replace(query=new_query))

    return {
        "url": url_without_time_code,
        "time_code": time_code
    }

async def _extract_redirect_from_html(html_text: str, base_url: str) -> str | None:
    # 1) meta refresh
    m = _meta_refresh_re.search(html_text)
    if m:
        return urljoin(base_url, html.unescape(m.group(1)))
    # 2) og:url (часто у reddit.app.link)
    m = _og_url_re.search(html_text)
    if m:
        return urljoin(base_url, html.unescape(m.group(1)))
    # 3) первая явная ссылка
    m = _href_re.search(html_text)
    if m:
        return urljoin(base_url, html.unescape(m.group(1)))
    return None

async def _strip_tracking(u: str) -> str:
    p = urlparse(u)
    # Уберём UTM и прочий мусор
    qs = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
          if not k.lower().startswith(("utm_", "ref", "mweb_"))]
    return urlunparse((p.scheme or "https", p.netloc, p.path, p.params,
                       urlencode(qs, doseq=True), ""))

async def _canonicalize_post_url(u: str) -> str:
    """
    Приводим к «старому» домену old.reddit.com для более стабильного JSON,
    и гарантируем, что это ссылка на пост (comments/<id>/...).
    """
    p = urlparse(u)
    netloc = p.netloc.lower()
    path = p.path

    # Короткие виды типа https://redd.it/<id> → comments/<id>
    if netloc == "redd.it":
        post_id = path.strip("/").split("/")[0]
        if post_id:
            return f"https://old.reddit.com/comments/{post_id}/"

    # Если уже comments-путь — норм
    if "/comments/" in path:
        return urlunparse(("https", "old.reddit.com", path if path.endswith("/") else path + "/", "", "", ""))

    # Иногда редирект ведёт на вид /r/sub/comments/id/slug
    # Или на https://www.reddit.com/r/... — просто заменим домен на old.
    return urlunparse(("https", "old.reddit.com", path if path.endswith("/") else path + "/", "", "", ""))

async def resolve_reddit_url(url: str) -> tuple[str, str]:
    """
    Принимает ЛЮБУЮ reddit-ссылку (мобильную/короткую/десктопную)
    → возвращает (canonical_post_url, post_json_url).

    canonical_post_url — нормальная ссылка на пост.
    post_json_url — та же ссылка, но с .json?raw_json=1
    """
    # 1) Сразу уберём трекинг
    url = await _strip_tracking(url)

    # 2) Прямые носители i.redd.it / v.redd.it возвращаем как есть (не пост)
    host = urlparse(url).netloc.lower()
    if host in {"i.redd.it", "preview.redd.it", "v.redd.it"}:
        # Для таких ссылок JSON поста не строим — это медиа, не страница поста.
        return url, ""

    # 3) Попробуем стандартные редиректы
    try:
        # Сначала HEAD — быстрее (если сервер корректен)
        r = SESSION.head(url, allow_redirects=True, timeout=15)
        final_url = r.url
    except requests.RequestException:
        final_url = url  # продолжим fallback'ами

    # Иногда сайт даёт 200 с HTML-страницей, где JS/meta редирект.
    # Тогда делаем GET и вынимаем целевой URL вручную.
    try:
        rget = SESSION.get(final_url, allow_redirects=True, timeout=20)
        # Если после GET урл снова изменился — используем его
        final_url = rget.url
        if rget.headers.get("Content-Type", "").lower().startswith("text/html"):
            maybe = await _extract_redirect_from_html(rget.text, final_url)
            if maybe:
                final_url = maybe
    except requests.RequestException:
        pass

    final_url = await _strip_tracking(final_url)

    # 4) Нормализуем к канонической ссылке на пост (old.reddit.com/...)
    canonical = await _canonicalize_post_url(final_url)

    # 5) Построим JSON-URL
    # Не лепим .json к медиа/профилям — только к comments/...
    if "/comments/" in canonical:
        json_url = canonical.rstrip("/") + "/.json?raw_json=1"
    else:
        json_url = ""

    return canonical, json_url
