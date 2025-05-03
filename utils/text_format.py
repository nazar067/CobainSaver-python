import re

def escape_markdown(text: str) -> str:
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', text)

def format_as_expandable_quote(text: str) -> str:
    escaped = escape_markdown(text)
    lines = escaped.strip().splitlines()
    quoted_lines = [f"**> {line}" for line in lines if line.strip()]
    quoted_text = "\n".join(quoted_lines)
    return f"{quoted_text}||"
