import random
import threading
from datetime import datetime, timezone
from typing import Callable, Optional

from commands.parser import ITEM_COUNT_PATTERN
import sheets.repository as sheet_repository

MAX_DICE_COUNT = 100
MAX_DICE_SIDES = 1000
BALANCE_LOCK = threading.Lock()


def dice(n: int, m: int) -> str:
    if n < 1 or m < 1:
        return "다이스는 1 이상의 숫자로 굴려주세요."
    if n > MAX_DICE_COUNT or m > MAX_DICE_SIDES:
        return f"다이스는 최대 {MAX_DICE_COUNT}d{MAX_DICE_SIDES}까지 굴릴 수 있어요."

    random_number = sum(random.randint(1, m) for _ in range(n))
    return str(random_number)


def investigate(repository: sheet_repository.SheetRepository, keyword: str) -> str:
    finders = repository.search.findall(
        keyword,
        in_column=sheet_repository.SEARCH_KEYWORD,
        case_sensitive=True,
    )
    if not finders:
        return "존재하지 않는 조사 키워드입니다."

    finder = random.choice(finders)
    result = f"[{keyword}] " + repository.search.cell(
        finder.row,
        sheet_repository.SEARCH_DESCRIPTION,
    ).value
    return result


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
