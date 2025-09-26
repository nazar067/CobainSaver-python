import logging
from aiogram.types import PollAnswer
from datetime import datetime
from asyncpg import Pool

from logs.write_server_errors import log_error

async def handle_poll_answer(answer: PollAnswer, pool: Pool):
    try:
        user_id = answer.user.id
        selected_option_index = answer.option_ids[0]

        mark = 5 - selected_option_index
        today = datetime.utcnow().date()

        async with pool.acquire() as conn:
            exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1 FROM user_marks
                    WHERE chat_id = $1 AND DATE(timestamp) = $2
                )
                """,
                user_id, today
            )

            if not exists:
                await conn.execute(
                    """
                    INSERT INTO user_marks (chat_id, mark)
                    VALUES ($1, $2)
                    """,
                    user_id, mark
                )
            else:
                log_error("url", e, 1111, "save user marks")
    except Exception as e:
        log_error("url", e, 1111, "save user marks")
