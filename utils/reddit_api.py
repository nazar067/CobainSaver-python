import asyncio
import os
import threading
import time
from typing import Any
from urllib.parse import urlparse, urlunparse

import requests
from requests.auth import HTTPBasicAuth

from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT


REDDIT_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_OAUTH_BASE_URL = "https://oauth.reddit.com"


class RedditApiError(Exception):
    pass


class RedditApiCredentialsError(RedditApiError):
    pass


class RedditApiAccessError(RedditApiError):
    pass


_SESSION = requests.Session()

_ACCESS_TOKEN: str | None = None
_ACCESS_TOKEN_EXPIRES_AT = 0.0

_TOKEN_LOCK = threading.Lock()


def _check_credentials() -> None:
    missing = []

    if not REDDIT_CLIENT_ID:
        missing.append("REDDIT_CLIENT_ID")

    if not REDDIT_CLIENT_SECRET:
        missing.append("REDDIT_CLIENT_SECRET")

    if missing:
        raise RedditApiCredentialsError(
            "Не указаны переменные окружения Reddit API: "
            + ", ".join(missing)
        )


def _safe_response_text(response: requests.Response) -> str:
    try:
        text = response.text.strip()
    except Exception:
        return ""

    if len(text) > 500:
        return text[:500] + "..."

    return text


def _request_access_token_sync() -> str:
    global _ACCESS_TOKEN
    global _ACCESS_TOKEN_EXPIRES_AT

    _check_credentials()

    response = _SESSION.post(
        REDDIT_TOKEN_URL,
        auth=HTTPBasicAuth(
            REDDIT_CLIENT_ID,
            REDDIT_CLIENT_SECRET,
        ),
        data={
            "grant_type": "client_credentials",
        },
        headers={
            "User-Agent": REDDIT_USER_AGENT,
            "Accept": "application/json",
        },
        timeout=20,
    )

    if response.status_code != 200:
        response_body = _safe_response_text(response)

        raise RedditApiAccessError(
            "Не удалось получить Reddit OAuth token. "
            f"Status={response.status_code}; "
            f"Response={response_body}"
        )

    try:
        data = response.json()
    except ValueError as error:
        raise RedditApiAccessError(
            "Reddit вернул невалидный JSON при получении OAuth token. "
            f"Content-Type={response.headers.get('Content-Type', '')}"
        ) from error

    access_token = data.get("access_token")

    if not access_token:
        raise RedditApiAccessError(
            "Reddit не вернул access_token. "
            f"Response={data}"
        )

    expires_in = int(data.get("expires_in") or 3600)

    _ACCESS_TOKEN = access_token

    # Обновляем токен немного раньше его фактического истечения.
    _ACCESS_TOKEN_EXPIRES_AT = (
        time.monotonic()
        + max(expires_in - 60, 60)
    )

    return access_token


def _get_access_token_sync(
    force_refresh: bool = False,
) -> str:
    global _ACCESS_TOKEN
    global _ACCESS_TOKEN_EXPIRES_AT

    current_time = time.monotonic()

    if (
        not force_refresh
        and _ACCESS_TOKEN
        and current_time < _ACCESS_TOKEN_EXPIRES_AT
    ):
        return _ACCESS_TOKEN

    with _TOKEN_LOCK:
        current_time = time.monotonic()

        if (
            not force_refresh
            and _ACCESS_TOKEN
            and current_time < _ACCESS_TOKEN_EXPIRES_AT
        ):
            return _ACCESS_TOKEN

        return _request_access_token_sync()


def _convert_to_oauth_url(url: str) -> str:
    parsed = urlparse(url)

    return urlunparse(
        (
            "https",
            "oauth.reddit.com",
            parsed.path,
            parsed.params,
            parsed.query,
            "",
        )
    )


def _oauth_get_sync(
    url: str,
    retry_after_unauthorized: bool = True,
) -> Any:
    token = _get_access_token_sync()
    oauth_url = _convert_to_oauth_url(url)

    response = _SESSION.get(
        oauth_url,
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": REDDIT_USER_AGENT,
            "Accept": "application/json",
        },
        timeout=20,
        allow_redirects=False,
    )

    # Токен мог истечь или быть отозван.
    if (
        response.status_code == 401
        and retry_after_unauthorized
    ):
        token = _get_access_token_sync(force_refresh=True)

        response = _SESSION.get(
            oauth_url,
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": REDDIT_USER_AGENT,
                "Accept": "application/json",
            },
            timeout=20,
            allow_redirects=False,
        )

    if response.status_code == 403:
        response_body = _safe_response_text(response)

        raise RedditApiAccessError(
            "Reddit API вернул 403 Forbidden. "
            "Проверьте, что приложение существует, credentials правильные "
            "и доступ к Reddit Data API одобрен. "
            f"URL={oauth_url}; "
            f"Response={response_body}"
        )

    if response.status_code == 429:
        reset = response.headers.get("X-Ratelimit-Reset")
        remaining = response.headers.get("X-Ratelimit-Remaining")

        raise RedditApiAccessError(
            "Превышен лимит Reddit API. "
            f"Remaining={remaining}; Reset={reset}"
        )

    if response.status_code >= 400:
        response_body = _safe_response_text(response)

        raise RedditApiAccessError(
            "Ошибка Reddit API. "
            f"Status={response.status_code}; "
            f"URL={oauth_url}; "
            f"Response={response_body}"
        )

    content_type = response.headers.get(
        "Content-Type",
        "",
    ).lower()

    if "application/json" not in content_type:
        raise RedditApiAccessError(
            "Reddit OAuth API вернул не JSON. "
            f"Status={response.status_code}; "
            f"Content-Type={content_type}; "
            f"URL={oauth_url}"
        )

    try:
        return response.json()
    except ValueError as error:
        raise RedditApiAccessError(
            "Не удалось разобрать JSON Reddit API. "
            f"URL={oauth_url}"
        ) from error


async def reddit_oauth_get(url: str) -> Any:
    return await asyncio.to_thread(
        _oauth_get_sync,
        url,
    )


async def get_reddit_post(post_id: str) -> dict:
    post_id = post_id.strip()

    if not post_id:
        raise RedditApiError("Пустой Reddit post ID")

    url = (
        f"{REDDIT_OAUTH_BASE_URL}/comments/{post_id}"
        "?raw_json=1&limit=1"
    )

    data = await reddit_oauth_get(url)

    if not isinstance(data, list) or not data:
        raise RedditApiError(
            "Reddit API вернул неожиданный формат поста"
        )

    try:
        children = data[0]["data"]["children"]

        if not children:
            raise RedditApiError(
                "Reddit API не вернул данные поста"
            )

        post = children[0]["data"]
    except (
        KeyError,
        IndexError,
        TypeError,
    ) as error:
        raise RedditApiError(
            "Не удалось получить пост из ответа Reddit API"
        ) from error

    if not isinstance(post, dict):
        raise RedditApiError(
            "Reddit API вернул некорректные данные поста"
        )

    return post