import asyncpg

async def get_db_pool(database_url):
    """
    Создание пула соединений с базой данных
    """
    return await asyncpg.create_pool(database_url)

async def init_db(pool):
    """
    Инициализация базы данных: создание таблиц
    """
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_languages (
                chat_id BIGINT PRIMARY KEY,
                language_code TEXT NOT NULL
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                user_id INT NOT NULL,
                link TEXT NOT NULL,
                msg_id INT NOT NULL,
                timestamp TIMESTAMP DEFAULT NOW(),
                success_send BOOLEAN DEFAULT FALSE
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                send_tiktok_music BOOLEAN DEFAULT TRUE,
                auto_pick_yt_quality BOOLEAN DEFAULT TRUE,
                send_ads BOOLEAN DEFAULT TRUE,
                time_start_off_ads TIMESTAMP DEFAULT NULL
            )
        """)