import threading
from datetime import datetime, timezone
from typing import Callable, Optional

from commands.actions.general import choose_draw_item
from commands.parser import ITEM_COUNT_PATTERN
import sheets.repository as sheet_repository

BALANCE_LOCK = threading.Lock()
DEFAULT_DRAW_COST_ITEM = "뽑기코인"


def buy_something(
    repository: sheet_repository.SheetRepository,
    status_id: str,
    account: str,
    item: str,
) -> str:
    status_id = str(status_id)
    item = item.strip()
    if not item:
        return "구매할 아이템을 입력해주세요."

    previous_result = _find_transaction_result(
        repository,
        status_id,
        account,
    )
    if previous_result is not None:
        return previous_result

    store_finder = repository.store.find(
        item,
        in_column=sheet_repository.STORE_ITEM,
        case_sensitive=True,
    )
    if not store_finder:
        return "존재하지 않는 아이템입니다."

    price = int(
        repository.store.cell(
            store_finder.row,
            sheet_repository.STORE_PRICE,
        ).value
    )
    if price < 1:
        raise ValueError("아이템 가격은 1 이상이어야 합니다.")

    return _apply_purchase(
        repository=repository,
        status_id=status_id,
        account=account,
        item=item,
        price=price,
    )


def add_money(
    repository: sheet_repository.SheetRepository,
    status_id: str,
    accounts: tuple[str, ...],
    amount: int,
) -> str:
    status_id = str(status_id)
    accounts = tuple(
        dict.fromkeys(
            account.strip()
            for account in accounts
            if account.strip()
        )
    )
    if not accounts:
        return "소지금을 추가할 아이디를 입력해주세요."
    if amount < 1:
        return "추가할 금액은 1 이상이어야 합니다."

    results = [
        (
            account,
            _apply_balance_change(
                repository=repository,
                status_id=status_id,
                account=account,
                transaction_type="지급",
                target="소지금추가",
                amount=amount,
                result_builder=lambda user_name, balance_after: (
                    f"{user_name}님에게 {amount} 재화를 추가했습니다. "
                    f"(잔액: {balance_after})"
                ),
            ),
        )
        for account in accounts
    ]

    if len(results) == 1:
        return results[0][1]
    return "\n".join(
        f"{account}: {result}"
        for account, result in results
    )


def draw_with_item(
    repository: sheet_repository.SheetRepository,
    status_id: str,
    account: str,
    cost_item: str = DEFAULT_DRAW_COST_ITEM,
) -> str:
    status_id = str(status_id)
    account = account.strip()
    cost_item = cost_item.strip()
    if not account:
        return "뽑기를 진행할 아이디가 없습니다."
    if not cost_item:
        return "소모할 아이템을 입력해주세요."

    with BALANCE_LOCK:
        previous_result = _find_transaction_result(
            repository,
            status_id,
            account,
        )
        if previous_result is not None:
            return previous_result

        character = repository.character.find(
            account,
            in_column=sheet_repository.CHARACTER_ACCOUNT,
            case_sensitive=True,
        )
        if not character:
            return "존재하지 않는 유저입니다."

        inventory = _parse_inventory(
            repository.character.cell(
                character.row,
                sheet_repository.CHARACTER_ITEMS,
            ).value
        )
        if inventory.get(cost_item, 0) < 1:
            return f"{cost_item} 아이템이 없습니다."

        draw_item = choose_draw_item(repository)
        if draw_item is None:
            return "뽑을 수 있는 아이템이 없습니다."

        item_name, description = draw_item
        inventory[cost_item] -= 1
        if inventory[cost_item] == 0:
            del inventory[cost_item]
        inventory_after = _format_inventory(inventory)

        balance = int(
            repository.character.cell(
                character.row,
                sheet_repository.CHARACTER_MONEY,
            ).value
        )
        result = f"{item_name}을 뽑았다. {description}"
        transaction_values = [
            status_id,
            account,
            "아이템뽑기",
            cost_item,
            -1,
            balance,
            balance,
            result,
            datetime.now(timezone.utc).isoformat(),
        ]

        try:
            repository.record_inventory_transaction(
                character.row,
                inventory_after,
                transaction_values,
            )
        except Exception:
            previous_result = _find_transaction_result(
                repository,
                status_id,
                account,
            )
            if previous_result is not None:
                return previous_result
            raise

        return result


def transfer_money(
    repository: sheet_repository.SheetRepository,
    status_id: str,
    sender_account: str,
    recipient_account: str,
    amount: int,
) -> str:
    status_id = str(status_id)
    sender_account = sender_account.strip()
    recipient_account = recipient_account.strip()
    if not recipient_account:
        return "양도받을 아이디를 입력해주세요."
    if sender_account == recipient_account:
        return "자기 자신에게는 재화를 양도할 수 없습니다."
    if amount < 1:
        return "양도할 금액은 1 이상이어야 합니다."

    with BALANCE_LOCK:
        previous_result = _find_transaction_result(
            repository,
            status_id,
            sender_account,
        )
        if previous_result is not None:
            return previous_result

        sender = repository.character.find(
            sender_account,
            in_column=sheet_repository.CHARACTER_ACCOUNT,
            case_sensitive=True,
        )
        if not sender:
            return "보내는 유저가 존재하지 않습니다."

        recipient = repository.character.find(
            recipient_account,
            in_column=sheet_repository.CHARACTER_ACCOUNT,
            case_sensitive=True,
        )
        if not recipient:
            return "양도받을 유저가 존재하지 않습니다."

        sender_balance_before = int(
            repository.character.cell(
                sender.row,
                sheet_repository.CHARACTER_MONEY,
            ).value
        )
        if sender_balance_before < amount:
            return "재화가 부족합니다."

        recipient_balance_before = int(
            repository.character.cell(
                recipient.row,
                sheet_repository.CHARACTER_MONEY,
            ).value
        )
        sender_balance_after = sender_balance_before - amount
        recipient_balance_after = recipient_balance_before + amount
        sender_name = repository.character.cell(
            sender.row,
            sheet_repository.CHARACTER_NAME,
        ).value
        recipient_name = repository.character.cell(
            recipient.row,
            sheet_repository.CHARACTER_NAME,
        ).value
        result = (
            f"{sender_name}님이 {recipient_name}님에게 "
            f"{amount} 재화를 양도했습니다. "
            f"(잔액: {sender_balance_after})"
        )
        processed_at = datetime.now(timezone.utc).isoformat()
        transaction_values = [
            [
                status_id,
                sender_account,
                "소지금양도",
                recipient_account,
                -amount,
                sender_balance_before,
                sender_balance_after,
                result,
                processed_at,
            ],
            [
                status_id,
                recipient_account,
                "소지금수령",
                sender_account,
                amount,
                recipient_balance_before,
                recipient_balance_after,
                result,
                processed_at,
            ],
        ]

        try:
            repository.record_money_transfer(
                sender.row,
                sender_balance_after,
                recipient.row,
                recipient_balance_after,
                transaction_values,
            )
        except Exception:
            previous_result = _find_transaction_result(
                repository,
                status_id,
                sender_account,
            )
            if previous_result is not None:
                return previous_result
            raise

        return result


def transfer_item(
    repository: sheet_repository.SheetRepository,
    status_id: str,
    sender_account: str,
    recipient_account: str,
    item: str,
    count: int = 1,
) -> str:
    status_id = str(status_id)
    sender_account = sender_account.strip()
    recipient_account = recipient_account.strip()
    item = item.strip()
    if not recipient_account:
        return "양도받을 아이디를 입력해주세요."
    if not item:
        return "양도할 아이템을 입력해주세요."
    if sender_account == recipient_account:
        return "자기 자신에게는 아이템을 양도할 수 없습니다."
    if count < 1:
        return "양도할 수량은 1 이상이어야 합니다."

    with BALANCE_LOCK:
        previous_result = _find_transaction_result(
            repository,
            status_id,
            sender_account,
        )
        if previous_result is not None:
            return previous_result

        sender = repository.character.find(
            sender_account,
            in_column=sheet_repository.CHARACTER_ACCOUNT,
            case_sensitive=True,
        )
        if not sender:
            return "보내는 유저가 존재하지 않습니다."

        recipient = repository.character.find(
            recipient_account,
            in_column=sheet_repository.CHARACTER_ACCOUNT,
            case_sensitive=True,
        )
        if not recipient:
            return "양도받을 유저가 존재하지 않습니다."

        sender_inventory = _parse_inventory(
            repository.character.cell(
                sender.row,
                sheet_repository.CHARACTER_ITEMS,
            ).value
        )
        if sender_inventory.get(item, 0) < count:
            return "아이템 수량이 부족합니다."

        recipient_inventory = _parse_inventory(
            repository.character.cell(
                recipient.row,
                sheet_repository.CHARACTER_ITEMS,
            ).value
        )
        sender_inventory[item] -= count
        if sender_inventory[item] == 0:
            del sender_inventory[item]
        recipient_inventory[item] = recipient_inventory.get(item, 0) + count

        sender_inventory_after = _format_inventory(sender_inventory)
        recipient_inventory_after = _format_inventory(recipient_inventory)
        sender_name = repository.character.cell(
            sender.row,
            sheet_repository.CHARACTER_NAME,
        ).value
        recipient_name = repository.character.cell(
            recipient.row,
            sheet_repository.CHARACTER_NAME,
        ).value
        sender_balance = int(
            repository.character.cell(
                sender.row,
                sheet_repository.CHARACTER_MONEY,
            ).value
        )
        recipient_balance = int(
            repository.character.cell(
                recipient.row,
                sheet_repository.CHARACTER_MONEY,
            ).value
        )
        result = (
            f"{sender_name}님이 {recipient_name}님에게 "
            f"{item} {count}개를 양도했습니다."
        )
        processed_at = datetime.now(timezone.utc).isoformat()
        transaction_values = [
            [
                status_id,
                sender_account,
                "아이템양도",
                f"{recipient_account}/{item}",
                -count,
                sender_balance,
                sender_balance,
                result,
                processed_at,
            ],
            [
                status_id,
                recipient_account,
                "아이템수령",
                f"{sender_account}/{item}",
                count,
                recipient_balance,
                recipient_balance,
                result,
                processed_at,
            ],
        ]

        try:
            repository.record_item_transfer(
                sender.row,
                sender_inventory_after,
                recipient.row,
                recipient_inventory_after,
                transaction_values,
            )
        except Exception:
            previous_result = _find_transaction_result(
                repository,
                status_id,
                sender_account,
            )
            if previous_result is not None:
                return previous_result
            raise

        return result


def _apply_purchase(
    repository: sheet_repository.SheetRepository,
    status_id: str,
    account: str,
    item: str,
    price: int,
) -> str:
    with BALANCE_LOCK:
        previous_result = _find_transaction_result(
            repository,
            status_id,
            account,
        )
        if previous_result is not None:
            return previous_result

        character_finder = repository.character.find(
            account,
            in_column=sheet_repository.CHARACTER_ACCOUNT,
            case_sensitive=True,
        )
        if not character_finder:
            return "존재하지 않는 유저입니다."

        balance_before = int(
            repository.character.cell(
                character_finder.row,
                sheet_repository.CHARACTER_MONEY,
            ).value
        )
        balance_after = balance_before - price
        if balance_after < 0:
            return "재화가 부족합니다."

        user_name = repository.character.cell(
            character_finder.row,
            sheet_repository.CHARACTER_NAME,
        ).value

        inventory_text = repository.character.cell(
            character_finder.row,
            sheet_repository.CHARACTER_ITEMS,
        ).value

        inventory_after = _add_inventory_item(
            inventory_text,
            item,
        )

        result = (
            f"{user_name}님, {item}을 구매했습니다. "
            f"(잔액: {balance_after})"
        )

        transaction_values = [
            status_id,
            account,
            "구매",
            item,
            -price,
            balance_before,
            balance_after,
            result,
            datetime.now(timezone.utc).isoformat(),
        ]

        try:
            repository.record_purchase(
                character_finder.row,
                balance_after,
                inventory_after,
                transaction_values,
            )
        except Exception:
            previous_result = _find_transaction_result(
                repository,
                status_id,
                account,
            )
            if previous_result is not None:
                return previous_result
            raise

        return result


def _apply_balance_change(
    repository: sheet_repository.SheetRepository,
    status_id: str,
    account: str,
    transaction_type: str,
    target: str,
    amount: int,
    result_builder: Callable[[str, int], str],
) -> str:
    with BALANCE_LOCK:
        previous_result = _find_transaction_result(
            repository,
            status_id,
            account,
        )
        if previous_result is not None:
            return previous_result

        character_finder = repository.character.find(
            account,
            in_column=sheet_repository.CHARACTER_ACCOUNT,
            case_sensitive=True,
        )
        if not character_finder:
            return "존재하지 않는 유저입니다."

        balance_before = int(
            repository.character.cell(
                character_finder.row,
                sheet_repository.CHARACTER_MONEY,
            ).value
        )
        balance_after = balance_before + amount
        if balance_after < 0:
            return "재화가 부족합니다."

        user_name = repository.character.cell(
            character_finder.row,
            sheet_repository.CHARACTER_NAME,
        ).value
        result = result_builder(user_name, balance_after)
        transaction_values = [
            status_id,
            account,
            transaction_type,
            target,
            amount,
            balance_before,
            balance_after,
            result,
            datetime.now(timezone.utc).isoformat(),
        ]

        try:
            repository.record_transaction(
                character_finder.row,
                balance_after,
                transaction_values,
            )
        except Exception:
            previous_result = _find_transaction_result(
                repository,
                status_id,
                account,
            )
            if previous_result is not None:
                return previous_result
            raise

        return result


def _find_transaction_result(
    repository: sheet_repository.SheetRepository,
    status_id: str,
    account: str,
) -> Optional[str]:
    for row in repository.transaction_log.get_all_values():
        if len(row) < sheet_repository.TRANSACTION_RESULT:
            continue
        if (
            row[sheet_repository.TRANSACTION_STATUS_ID - 1] == status_id
            and row[sheet_repository.TRANSACTION_ACCOUNT - 1] == account
        ):
            return row[sheet_repository.TRANSACTION_RESULT - 1]
    return None


def _add_inventory_item(inventory_text: str, item: str) -> str:
    inventory = _parse_inventory(inventory_text)
    inventory[item] = inventory.get(item, 0) + 1
    return _format_inventory(inventory)


def _parse_inventory(inventory_text: str) -> dict[str, int]:
    inventory = {}

    for entry in (inventory_text or "").split(","):
        entry = entry.strip()
        if not entry:
            continue

        match = ITEM_COUNT_PATTERN.fullmatch(entry)
        if match:
            item_name = match.group(1).strip()
            count = int(match.group(2))
        else:
            item_name = entry
            count = 1

        if item_name and count > 0:
            inventory[item_name] = inventory.get(item_name, 0) + count

    return inventory


def _format_inventory(inventory: dict[str, int]) -> str:
    return ", ".join(
        item if count == 1 else f"{item} * {count}"
        for item, count in inventory.items()
    )
