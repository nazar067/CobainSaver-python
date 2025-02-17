import asyncio
from datetime import datetime, timedelta

async def check_and_update_ads(pool):

    while True:
        async with pool.acquire() as conn:
            records = await conn.fetch(
                """
                SELECT chat_id, time_start_off_ads FROM settings 
                WHERE send_ads = FALSE AND time_start_off_ads IS NOT NULL
                """
            )

            now = datetime.utcnow()

            for record in records:
                chat_id = record["chat_id"]
                time_start_off_ads = record["time_start_off_ads"]

                if time_start_off_ads and now >= time_start_off_ads + timedelta(days=30):
                    await conn.execute(
                        """
                        UPDATE settings 
                        SET send_ads = TRUE, time_start_off_ads = NULL
                        WHERE chat_id = $1
                        """,
                        chat_id
                    )

        await asyncio.sleep(60)
