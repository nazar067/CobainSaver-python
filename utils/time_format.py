async def format_seconds(seconds: int) -> str:

    if seconds < 3600:
        minutes, secs = divmod(seconds, 60)
        return f"{minutes:02}:{secs:02}"
    else:
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{secs:02}"
