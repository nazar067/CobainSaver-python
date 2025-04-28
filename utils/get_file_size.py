async def get_music_size(bit_rate_kbps: int, duration_seconds: int) -> float:
    size_mb = (bit_rate_kbps * duration_seconds) / (8 * 1024)
    return size_mb
