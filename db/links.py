import asyncpg

async def insert_link_into_db(dp, chat_id: int, user_id: int, link: str, msg_id):
    pool = dp["db_pool"]
    query = """
    INSERT INTO links (chat_id, user_id, link, msg_id, success_send)
    VALUES ($1, $2, $3, $4, $5)
    RETURNING id;
    """
    async with pool.acquire() as connection:
        if link.startswith("https://music.youtube.com/playlist?") or link.startswith("https://open.spotify.com/album")or link.startswith("https://open.spotify.com/playlist"):
            return await connection.fetchval(query, chat_id, user_id, link, msg_id, None)
        return await connection.fetchval(query, chat_id, user_id, link, msg_id, False)

async def update_link_status(dp, chat_id: int, msg_id: int, success_send: bool):
    """
    Обновляет значение success_send в таблице links по chat_id и msg_id.
    
    :param pool: asyncpg.Pool - пул соединений с базой данных
    :param chat_id: int - идентификатор чата
    :param msg_id: int - идентификатор сообщения
    :param success_send: bool - новое значение success_send
    """
    pool = dp["db_pool"]
    async with pool.acquire() as connection:
        await connection.execute(
            """
            UPDATE links
            SET success_send = $1
            WHERE chat_id = $2 AND msg_id = $3
            """,
            success_send, chat_id, msg_id
        )