import re
from typing import Optional

from commands.models import (
    AddMoneyCommand,
    DiceCommand,
    DrawCommand,
    InvestigateCommand,
    ParsedCommand,
    PurchaseCommand,
    TransferItemCommand,
    TransferMoneyCommand,
)

INVESTIGATE_PATTERN = re.compile(r"조사\s*/\s*(.+)")
DRAW_PATTERN = re.compile(r"뽑기")
PURCHASE_PATTERN = re.compile(r"구매\s*/\s*(.+)")
ADD_MONEY_PATTERN = re.compile(r"소지금\s*추가\s*/\s*([^/]+)\s*/\s*(\d+)")
TRANSFER_MONEY_PATTERN = re.compile(
    r"소지금\s*양도\s*/\s*([^/]+)\s*/\s*(\d+)"
)
TRANSFER_ITEM_PATTERN = re.compile(
    r"아이템\s*양도\s*/\s*([^/]+)\s*/\s*([^/]+)"
    r"(?:\s*/\s*(\d+))?"
)
DICE_PATTERN = re.compile(r"(\d+)\s*[dD]\s*(\d+)")
ITEM_COUNT_PATTERN = re.compile(r"^(.*?)\s*\*\s*(\d+)$")


def parse_command(command_text: str) -> Optional[ParsedCommand]:
    if DRAW_PATTERN.fullmatch(command_text):
        return DrawCommand()

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

    if match := TRANSFER_MONEY_PATTERN.fullmatch(command_text):
        recipient_account = match.group(1).strip()
        amount = int(match.group(2))
        if recipient_account and amount > 0:
            return TransferMoneyCommand(recipient_account, amount)
        return None

    if match := TRANSFER_ITEM_PATTERN.fullmatch(command_text):
        recipient_account = match.group(1).strip()
        item = match.group(2).strip()
        count = int(match.group(3)) if match.group(3) else 1
        if match.group(3) is None:
            item_count = ITEM_COUNT_PATTERN.fullmatch(item)
            if item_count:
                item = item_count.group(1).strip()
                count = int(item_count.group(2))
        if recipient_account and item and count > 0:
            return TransferItemCommand(recipient_account, item, count)
        return None

    if match := DICE_PATTERN.fullmatch(command_text):
        return DiceCommand(
            count=int(match.group(1)),
            sides=int(match.group(2)),
        )

    return None
