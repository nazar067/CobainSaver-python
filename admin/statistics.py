import asyncpg
from aiogram import Bot
from datetime import datetime
from utils.service_identifier import identify_service
from config import ADMIN_ID

async def get_statistics(pool, date=None):
    """
    Извлекает статистику за определенную дату (по умолчанию - сегодня).
    """
    if date is None:
        date = datetime.now().date()

    async with pool.acquire() as conn:
        # Уникальные пользователи за день
        unique_users = await conn.fetchval(
            "SELECT COUNT(DISTINCT user_id) FROM links WHERE DATE(timestamp) = $1", date
        )

        # Уникальные чаты за день
        unique_chats = await conn.fetchval(
            "SELECT COUNT(DISTINCT chat_id) FROM links WHERE DATE(timestamp) = $1", date
        )

        # Количество ссылок за день
        total_links_today = await conn.fetchval(
            "SELECT COUNT(link) FROM links WHERE DATE(timestamp) = $1", date
        )

        # Количество успешно обработанных ссылок за день
        success_links_today = await conn.fetchval(
            "SELECT COUNT(link) FROM links WHERE DATE(timestamp) = $1 AND success_send = TRUE", date
        )

        # Количество ссылок за все время
        total_links_all_time = await conn.fetchval("SELECT COUNT(link) FROM links")

        # Количество успешно обработанных ссылок за все время
        success_links_all_time = await conn.fetchval(
            "SELECT COUNT(link) FROM links WHERE success_send = TRUE"
        )

        # Получаем ссылки за день для анализа сервисов
        rows = await conn.fetch(
            "SELECT link, success_send FROM links WHERE DATE(timestamp) = $1", date
        )

    return {
        "date": date,
        "unique_users": unique_users or 0,
        "unique_chats": unique_chats or 0,
        "total_links_today": total_links_today or 0,
        "success_links_today": success_links_today or 0,
        "total_links_all_time": total_links_all_time or 0,
        "success_links_all_time": success_links_all_time or 0,
        "links": rows,
    }

async def analyze_services(links_data):
    """
    Анализирует количество ссылок по сервисам и количество успешно обработанных ссылок.
    """
    services = {
        "YouTube": [0, 0], "YouTubeMusic": [0, 0], "Spotify": [0, 0],
        "TikTok": [0, 0], "Twitter/X": [0, 0], "Instagram": [0, 0],
        "Pinterest": [0, 0], "PornHub": [0, 0], "Twitch": [0, 0], "Another": [0, 0]
    }

    for row in links_data:
        service = await identify_service(row["link"])
        if service in services:
            services[service][0] += 1  # Всего ссылок
            if row["success_send"]:
                services[service][1] += 1  # Успешно обработано

    return services

async def format_statistics(statistics, services):
    """
    Форматирует статистику в удобное сообщение.
    """
    stats_message = (
        f"📊 <b>Статистика за {statistics['date']}</b>\n\n"
        f"👤 Уникальные пользователи: <b>{statistics['unique_users']}</b>\n"
        f"💬 Уникальные чаты: <b>{statistics['unique_chats']}</b>\n"
        f"🔗 Ссылок за день: <b>{statistics['total_links_today']}</b>\n"
        f"✅ Успешных ссылок за день: <b>{statistics['success_links_today']}</b>\n\n"
        f"📌 <b>Общая статистика</b>:\n"
        f"🔗 Всего ссылок: <b>{statistics['total_links_all_time']}</b>\n"
        f"✅ Успешно обработано: <b>{statistics['success_links_all_time']}</b>\n\n"
        f"📊 <b>Статистика по сервисам</b>:\n"
    )

    for service, (total, success) in services.items():
        stats_message += f"🔹 {service}: <b>{total}</b> (✅ {success})\n"

    return stats_message

async def send_statistics(bot: Bot, pool, chat_id=ADMIN_ID, date=None):
    """
    Извлекает, анализирует и отправляет статистику в указанный чат.
    """
    statistics = await get_statistics(pool, date)
    services = await analyze_services(statistics["links"])
    stats_message = await format_statistics(statistics, services)

    await bot.send_message(chat_id=chat_id, text=stats_message, parse_mode="HTML")
