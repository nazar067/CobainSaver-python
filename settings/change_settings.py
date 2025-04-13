from datetime import datetime

from datetime import datetime

async def upsert_settings(pool, chat_id, send_tiktok_music: bool = None, auto_pick_yt_quality: bool = None, send_ads: bool = None, hd_size: bool = None):
    async with pool.acquire() as conn:
        existing_row = await conn.fetchrow("SELECT * FROM settings WHERE chat_id = $1", chat_id)
        
        if existing_row:
            update_query = "UPDATE settings SET "
            update_params = []
            param_count = 1

            if send_tiktok_music is not None:
                update_query += f"send_tiktok_music = ${param_count}, "
                update_params.append(send_tiktok_music)
                param_count += 1

            if auto_pick_yt_quality is not None:
                update_query += f"auto_pick_yt_quality = ${param_count}, "
                update_params.append(auto_pick_yt_quality)
                param_count += 1

            if send_ads is not None:
                update_query += f"send_ads = ${param_count}, "
                update_params.append(send_ads)
                param_count += 1
                
                if send_ads is False:
                    update_query += f"time_start_off_ads = ${param_count}, "
                    update_params.append(datetime.utcnow())
                    param_count += 1
                elif send_ads is True:
                    update_query += f"time_start_off_ads = NULL, "

            if hd_size is not None:
                update_query += f"hd_size = ${param_count}, "
                update_params.append(hd_size)
                param_count += 1

            update_query = update_query.rstrip(", ")
            update_query += f" WHERE chat_id = ${param_count}"
            update_params.append(chat_id)

            await conn.execute(update_query, *update_params)

        else:
            await conn.execute("""
                INSERT INTO settings (chat_id, send_tiktok_music, auto_pick_yt_quality, send_ads, hd_size, time_start_off_ads)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, chat_id,
                send_tiktok_music if send_tiktok_music is not None else True,
                auto_pick_yt_quality if auto_pick_yt_quality is not None else True,
                send_ads if send_ads is not None else True,
                hd_size if hd_size is not None else False,
                datetime.utcnow() if send_ads is False else None
            )
