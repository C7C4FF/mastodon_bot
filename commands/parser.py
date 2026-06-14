import re
from dataclasses import dataclass
from typing import Optional

from bs4 import BeautifulSoup


COMMAND_PATTERN = re.compile(r"\[([^\]]+)\]")
INVESTIGATE_PATTERN = re.compile(r"조사\s*/\s*(.+)")
PURCHASE_PATTERN = re.compile(r"구매\s*/\s*(.+)")
ADD_MONEY_PATTERN = re.compile(r"소지금추가\s*/\s*([^/]+)\s*/\s*(\d+)")
DICE_PATTERN = re.compile(r"(\d+)\s*[dD]\s*(\d+)")


@dataclass(frozen=True)
class InvestigateCommand:
    keyword: str


@dataclass(frozen=True)
class PurchaseCommand:
    item: str


@dataclass(frozen=True)
class AddMoneyCommand:
    account: str
    amount: int


@dataclass(frozen=True)
class DiceCommand:
    count: int
    sides: int


ParsedCommand = (
    InvestigateCommand
    | PurchaseCommand
    | AddMoneyCommand
    | DiceCommand
)


def sanitize_command_text(raw_text: str) -> Optional[str]:
    parsed_text = BeautifulSoup(
        raw_text,
        "html.parser",
    ).get_text(separator="\n", strip=True)

    match = COMMAND_PATTERN.search(parsed_text)
    return match.group(1).strip() if match else None


def parse_command(command_text: str) -> Optional[ParsedCommand]:
    if match := INVESTIGATE_PATTERN.fullmatch(command_text):
        keyword = match.group(1).strip()
        return InvestigateCommand(keyword) if keyword else None

    if match := PURCHASE_PATTERN.fullmatch(command_text):
        item = match.group(1).strip()
        return PurchaseCommand(item) if item else None

    if match := ADD_MONEY_PATTERN.fullmatch(command_text):
        account = match.group(1).strip()
        amount = int(match.group(2))
        if account and amount > 0:
            return AddMoneyCommand(account, amount)
        return None

    if match := DICE_PATTERN.fullmatch(command_text):
        return DiceCommand(
            count=int(match.group(1)),
            sides=int(match.group(2)),
        )

    return None
