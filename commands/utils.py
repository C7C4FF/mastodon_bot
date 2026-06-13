from bs4 import BeautifulSoup
from typing import Optional
import re


COMMAND_PATTERN = re.compile(r"\[([^\]]+)\]")


def sanitize_command_text(raw_text: str) -> Optional[str]:
    parsed_text = BeautifulSoup(
        raw_text,
        "html.parser",
    ).get_text(separator="\n", strip=True)

    match = COMMAND_PATTERN.search(parsed_text)
    return match.group(1).strip() if match else None


def parse_number(raw_value: Optional[str]) -> Optional[int]:
    if raw_value is None:
        return None

    try:
        return int(raw_value.strip())
    except ValueError:
        return None
