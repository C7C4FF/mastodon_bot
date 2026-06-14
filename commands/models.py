from dataclasses import dataclass


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
