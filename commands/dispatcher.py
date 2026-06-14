from functools import singledispatchmethod

from commands.actions import (
    add_money,
    buy_something,
    dice,
    draw,
    investigate,
    show_balance,
    show_inventory,
    transfer_item,
    transfer_money,
)
from commands.context import CommandContext
from commands.models import (
    AddMoneyCommand,
    BalanceCommand,
    DiceCommand,
    DrawCommand,
    InvestigateCommand,
    InventoryCommand,
    ParsedCommand,
    PurchaseCommand,
    TransferItemCommand,
    TransferMoneyCommand,
)
from sheets.repository import SheetRepository


class CommandDispatcher:
    def __init__(self, repository: SheetRepository):
        self.repository = repository

    @singledispatchmethod
    def dispatch(
        self,
        command: ParsedCommand,
        context: CommandContext,
    ) -> str:
        raise ValueError("지원하지 않는 명령어입니다.")

    @dispatch.register
    def _(
        self,
        command: InvestigateCommand,
        context: CommandContext,
    ) -> str:
        return investigate(self.repository, command.keyword)

    @dispatch.register
    def _(
        self,
        command: DrawCommand,
        context: CommandContext,
    ) -> str:
        return draw(self.repository)

    @dispatch.register
    def _(
        self,
        command: BalanceCommand,
        context: CommandContext,
    ) -> str:
        return show_balance(self.repository, context.user_account)

    @dispatch.register
    def _(
        self,
        command: InventoryCommand,
        context: CommandContext,
    ) -> str:
        return show_inventory(self.repository, context.user_account)

    @dispatch.register
    def _(
        self,
        command: PurchaseCommand,
        context: CommandContext,
    ) -> str:
        return buy_something(
            self.repository,
            context.status_id,
            context.user_account,
            command.item,
        )

    @dispatch.register
    def _(
        self,
        command: AddMoneyCommand,
        context: CommandContext,
    ) -> str:
        return add_money(
            self.repository,
            context.status_id,
            command.accounts,
            command.amount,
        )

    @dispatch.register
    def _(
        self,
        command: TransferMoneyCommand,
        context: CommandContext,
    ) -> str:
        return transfer_money(
            self.repository,
            context.status_id,
            context.user_account,
            command.recipient_account,
            command.amount,
        )

    @dispatch.register
    def _(
        self,
        command: TransferItemCommand,
        context: CommandContext,
    ) -> str:
        return transfer_item(
            self.repository,
            context.status_id,
            context.user_account,
            command.recipient_account,
            command.item,
            command.count,
        )

    @dispatch.register
    def _(
        self,
        command: DiceCommand,
        context: CommandContext,
    ) -> str:
        return dice(command.count, command.sides)
