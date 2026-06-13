from bs4 import BeautifulSoup
from typing import Optional
import re


DISALLOWED_COMMAND_CHARS = re.compile(r'[^\w\s\[\]/]')


def sanitize_command_text(raw_text: str) -> str:
    soup = BeautifulSoup(raw_text, "html.parser")
    parsed_text = soup.get_text(strip=True)
    sanitized_text = re.sub(DISALLOWED_COMMAND_CHARS, "", parsed_text)
    return sanitized_text


def parse_number(raw_value: Optional[str]) -> Optional[int]:
    if raw_value is None:
        return None

    try:
        return int(raw_value.strip())
    except ValueError:
        return None

