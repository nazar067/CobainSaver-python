import os
from urllib.parse import urlparse

from aiogram import Bot, Dispatcher

from downloader.media import send_gif
from downloader.reddit.photo_download import download_gallery
from downloader.reddit.video_download import download_video_content
from downloader.send_album import send_social_media_album
from keyboard import send_log_keyboard
from localisation.get_language import get_language
from localisation.translations.downloader import translations
from logs.write_server_errors import log_error
from user.get_user_path import get_user_path
from utils.fetch_data import download_file
from utils.get_name import get_random_file_name
from utils.get_url import resolve_reddit_url
from utils.reddit_api import reddit_oauth_get


def _ensure_dir(directory: str) -> None:
    os.makedirs(directory, exist_ok=True)


async def download_reddit_media(
    bot: Bot,
    url: str,
    chat_id: int,
    dp: Dispatcher,
    business_connection_id,
    msg_id: int,
):
    chat_language = "en"

    try:
        pool = dp["db_pool"]

        chat_language = await get_language(
            pool,
            chat_id,
        )

        dest_dir = await get_user_path(chat_id)
        _ensure_dir(dest_dir)

        canonical, json_url = await resolve_reddit_url(
            url
        )

        parsed_canonical = urlparse(canonical)
        canonical_host = parsed_canonical.netloc.lower()

        # 1. Прямая ссылка на Reddit-картинку
        if canonical_host in {
            "i.redd.it",
            "preview.redd.it",
            "external-preview.redd.it",
        }:
            random_name = await get_random_file_name("")

            extension = os.path.splitext(
                parsed_canonical.path
            )[1]

            if not extension:
                extension = ".jpg"

            output_path = os.path.join(
                dest_dir,
                f"{random_name}{extension}",
            )

            await download_file(
                canonical,
                output_path,
            )

            return [output_path]

        # 2. Прямая ссылка на v.redd.it
        if canonical_host == "v.redd.it":
            return await download_video_content(
                bot=bot,
                url=canonical,
                chat_id=chat_id,
                dp=dp,
                business_connection_id=business_connection_id,
                msg_id=msg_id,
            )

        # Остальные Reddit-ссылки должны вести на пост.
        if not json_url:
            raise ValueError(
                "Не удалось сформировать Reddit OAuth URL"
            )

        data = await reddit_oauth_get(json_url)

        if not isinstance(data, list) or not data:
            raise ValueError(
                "Reddit API вернул пустой "
                "или неожиданный ответ"
            )

        try:
            children = data[0]["data"]["children"]

            if not children:
                raise ValueError(
                    "В ответе Reddit отсутствует пост"
                )

            post = children[0]["data"]

        except (
            KeyError,
            IndexError,
            TypeError,
        ) as error:
            raise ValueError(
                "Не удалось извлечь данные поста "
                "из ответа Reddit API"
            ) from error

        if not isinstance(post, dict) or not post:
            raise ValueError(
                "Reddit API не вернул данные поста"
            )

        random_name = await get_random_file_name("")

        # 3. Галерея
        if (
            post.get("is_gallery")
            and post.get("media_metadata")
        ):
            return await download_gallery(
                bot,
                chat_id,
                chat_language,
                business_connection_id,
                msg_id,
                pool,
                post,
                dest_dir,
            )

        # 4. Одиночная картинка
        media_url = (
            post.get("url_overridden_by_dest")
            or post.get("url")
        )

        if media_url:
            parsed_media = urlparse(media_url)
            media_host = parsed_media.netloc.lower()

            if media_host in {
                "i.redd.it",
                "preview.redd.it",
                "external-preview.redd.it",
            }:
                extension = os.path.splitext(
                    parsed_media.path
                )[1]

                if not extension:
                    extension = ".jpg"

                output_path = os.path.join(
                    dest_dir,
                    f"{random_name}{extension}",
                )

                await download_file(
                    media_url,
                    output_path,
                )

                if extension.lower() in {
                    ".gif",
                    ".gifv",
                }:
                    return await send_gif(
                        bot,
                        chat_id,
                        msg_id,
                        chat_language,
                        business_connection_id,
                        output_path,
                        post.get("title", ""),
                        None,
                        "HTML",
                    )

                return await send_social_media_album(
                    bot,
                    chat_id,
                    chat_language,
                    business_connection_id,
                    [output_path],
                    post.get("title", ""),
                    msg_id,
                    False,
                    pool=pool,
                )

        # 5. Видео, Reddit GIF или видео внутри crosspost.
        # video_download.py сам найдёт нужные metadata.
        return await download_video_content(
            bot=bot,
            url=canonical,
            chat_id=chat_id,
            dp=dp,
            business_connection_id=business_connection_id,
            msg_id=msg_id,
            post=post,
        )

    except Exception as error:
        log_error(
            url,
            error,
            chat_id,
            "Reddit",
        )

        return await bot.send_message(
            chat_id=chat_id,
            business_connection_id=business_connection_id,
            text=translations[
                "unavaliable_content"
            ][chat_language],
            reply_to_message_id=msg_id,
            reply_markup=await send_log_keyboard(
                translations[
                    "unavaliable_content"
                ][chat_language],
                str(error),
                chat_language,
                chat_id,
                url,
            ),
        )