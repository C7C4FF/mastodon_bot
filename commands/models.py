from dataclasses import dataclass


@dataclass(frozen=True)
class InvestigateCommand:
    keyword: str


@dataclass(frozen=True)
class PurchaseCommand:
    item: str


@dataclass(frozen=True)
class AddMoneyCommand:
    accounts: tuple[str, ...]
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
