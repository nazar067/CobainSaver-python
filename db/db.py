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
                chat_id INT NOT NULL,
                user_id INT NOT NULL,
                link TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT NOW()
            )
        """)