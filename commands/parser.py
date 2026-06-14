import re
from typing import Optional

from commands.models import (
    AddMoneyCommand,
    DiceCommand,
    InvestigateCommand,
    ParsedCommand,
    PurchaseCommand,
)

INVESTIGATE_PATTERN = re.compile(r"조사\s*/\s*(.+)")
PURCHASE_PATTERN = re.compile(r"구매\s*/\s*(.+)")
ADD_MONEY_PATTERN = re.compile(r"소지금\s*추가\s*/\s*([^/]+)\s*/\s*(\d+)")
DICE_PATTERN = re.compile(r"(\d+)\s*[dD]\s*(\d+)")
ITEM_COUNT_PATTERN = re.compile(r"^(.*?)\s*\*\s*(\d+)$")


def parse_command(command_text: str) -> Optional[ParsedCommand]:
    if match := INVESTIGATE_PATTERN.fullmatch(command_text):
        keyword = match.group(1).strip()
        return InvestigateCommand(keyword) if keyword else None

    if match := PURCHASE_PATTERN.fullmatch(command_text):
        item = match.group(1).strip()
        return PurchaseCommand(item) if item else None

    if match := ADD_MONEY_PATTERN.fullmatch(command_text):
        accounts = tuple(
            dict.fromkeys(
                account.strip()
                for account in match.group(1).split(",")
                if account.strip()
            )
        )
        amount = int(match.group(2))
        if accounts and amount > 0:
            return AddMoneyCommand(accounts, amount)
        return None

    if match := DICE_PATTERN.fullmatch(command_text):
        return DiceCommand(
            count=int(match.group(1)),
            sides=int(match.group(2)),
        )

    return None
