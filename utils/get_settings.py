async def get_settings(pool, chat_id):
    """
    Получает все настройки пользователя.

    Args:
        pool: Пул подключений к БД.
        chat_id (int): ID чата.

    Returns:
        dict: Словарь с настройками пользователя.
    """
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT send_tiktok_music, auto_pick_yt_quality, send_ads, hd_size, time_start_off_ads FROM settings WHERE chat_id = $1",
            chat_id
        )

        if result:
            return {
                "send_tiktok_music": result["send_tiktok_music"],
                "auto_pick_yt_quality": result["auto_pick_yt_quality"],
                "send_ads": result["send_ads"],
                "hd_size": result["hd_size"],
                "time_start_off_ads": result["time_start_off_ads"]
            }
        else:
            return {
                "send_tiktok_music": True,
                "auto_pick_yt_quality": True,
                "send_ads": True,
                "hd_size": False,
                "time_start_off_ads": None
            }
