from datetime import datetime, timedelta
from asyncpg import Pool

async def get_active_chats_last_month(pool: Pool) -> list[int]:
    one_month_ago = datetime.utcnow() - timedelta(days=30)

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT chat_id
            FROM links
            WHERE timestamp >= $1
            GROUP BY chat_id
            HAVING COUNT(*) > 10
        """, one_month_ago)

    return [row['chat_id'] for row in rows]
