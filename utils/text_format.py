import re

async def remove_special_chars(text: str) -> str:
    return text.replace('<', ' ').replace('>', ' ').replace('/', ' ')


async def format_as_expandable_quote(text: str) -> str:
    text = await remove_special_chars(text)
    lines = text.strip().splitlines()
    quoted_lines = [f"<blockquote expandable> {line}" for line in lines if line.strip()]
    quoted_text = "\n".join(quoted_lines)
    return f"{quoted_text}</blockquote>"
