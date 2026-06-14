import re
from typing import Optional

from bs4 import BeautifulSoup


COMMAND_PATTERN = re.compile(r"\[([^\]]+)\]")


def extract_command_text(raw_text: str) -> Optional[str]:
    parsed_text = BeautifulSoup(
        raw_text,
        "html.parser",
    ).get_text(separator="\n", strip=True)

    match = COMMAND_PATTERN.search(parsed_text)
    return match.group(1).strip() if match else None
