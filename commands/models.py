from dataclasses import dataclass


@dataclass(frozen=True)
class InvestigateCommand:
    keyword: str


@dataclass(frozen=True)
class DrawCommand:
    pass


@dataclass(frozen=True)
class CoinCommand:
    pass


@dataclass(frozen=True)
class BalanceCommand:
    pass


@dataclass(frozen=True)
class InventoryCommand:
    pass


@dataclass(frozen=True)
class PurchaseCommand:
    item: str


@dataclass(frozen=True)
class AddMoneyCommand:
    accounts: tuple[str, ...]
    amount: int


@dataclass(frozen=True)
class TransferMoneyCommand:
    recipient_account: str
    amount: int


@dataclass(frozen=True)
class TransferItemCommand:
    recipient_account: str
    item: str
    count: int


@dataclass(frozen=True)
class DiceCommand:
    count: int
    sides: int


ParsedCommand = (
    InvestigateCommand
    | DrawCommand
    | CoinCommand
    | BalanceCommand
    | InventoryCommand
    | PurchaseCommand
    | AddMoneyCommand
    | TransferMoneyCommand
    | TransferItemCommand
    | DiceCommand
)
