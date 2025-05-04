import re

def format_as_expandable_quote(text: str) -> str:
    lines = text.strip().splitlines()
    quoted_lines = [f"<blockquote expandable> {line}" for line in lines if line.strip()]
    quoted_text = "\n".join(quoted_lines)
    return f"{quoted_text}</blockquote>"
