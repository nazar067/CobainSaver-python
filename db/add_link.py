import asyncpg

async def insert_link_into_db(dp, chat_id: int, user_id: int, link: str):
    pool = dp["db_pool"]
    query = """
    INSERT INTO links (chat_id, user_id, link)
    VALUES ($1, $2, $3)
    RETURNING id;
    """
    async with pool.acquire() as connection:
        return await connection.fetchval(query, chat_id, user_id, link)
