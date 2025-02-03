async def get_language(pool, chat_id):
    """
    Проверка языка пользователя. Если язык не русский или украинский, возвращается английский.
    """
    async with pool.acquire() as connection:
        language_code = await connection.fetchval("""
            SELECT language_code FROM chat_languages WHERE chat_id = $1
        """, chat_id)

    if language_code not in ["ru", "uk"]:
        return "en"
    return language_code