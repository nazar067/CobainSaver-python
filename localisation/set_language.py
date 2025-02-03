async def set_language(pool, chat_id, language_code):
    """
    Определение языка пользователя и запись в таблицу languages
    """
    async with pool.acquire() as connection:
        await connection.execute("""
            INSERT INTO chat_languages (chat_id, language_code)
            VALUES ($1, $2)
            ON CONFLICT (chat_id) DO UPDATE SET language_code = EXCLUDED.language_code
        """, chat_id, language_code)