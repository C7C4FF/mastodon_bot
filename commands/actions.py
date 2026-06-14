import random
import threading
from datetime import datetime, timezone

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
    finder = repository.search.find(
        keyword,
        in_column=sheet_repository.SEARCH_KEYWORD,
        case_sensitive=True,
    )
    if not finder:
        return "존재하지 않는 조사 키워드입니다."

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

    with BALANCE_LOCK:
        previous_purchase = repository.transaction_log.find(
            status_id,
            in_column=sheet_repository.TRANSACTION_STATUS_ID,
            case_sensitive=True,
        )
        if previous_purchase:
            return repository.transaction_log.cell(
                previous_purchase.row,
                sheet_repository.TRANSACTION_RESULT,
            ).value

        store_finder = repository.store.find(
            item,
            in_column=sheet_repository.STORE_ITEM,
            case_sensitive=True,
        )
        if not store_finder:
            return "존재하지 않는 아이템입니다."

        character_finder = repository.character.find(
            account,
            in_column=sheet_repository.CHARACTER_ACCOUNT,
            case_sensitive=True,
        )
        if not character_finder:
            return "존재하지 않는 유저입니다."

        price = int(
            repository.store.cell(
                store_finder.row,
                sheet_repository.STORE_PRICE,
            ).value
        )
        if price < 1:
            raise ValueError("아이템 가격은 1 이상이어야 합니다.")

        balance_before = int(
            repository.character.cell(
                character_finder.row,
                sheet_repository.CHARACTER_MONEY,
            ).value
        )
        if not is_affordable(price, balance_before):
            return "재화가 부족합니다."

        balance_after = balance_before - price
        user_name = repository.character.cell(
            character_finder.row,
            sheet_repository.CHARACTER_NAME,
        ).value
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
            repository.record_transaction(
                character_finder.row,
                balance_after,
                transaction_values,
            )
        except Exception:
            previous_purchase = repository.transaction_log.find(
                status_id,
                in_column=sheet_repository.TRANSACTION_STATUS_ID,
                case_sensitive=True,
            )
            if previous_purchase:
                return repository.transaction_log.cell(
                    previous_purchase.row,
                    sheet_repository.TRANSACTION_RESULT,
                ).value
            raise

        return result


def add_money(
    repository: sheet_repository.SheetRepository,
    status_id: str,
    account: str,
    amount: int,
) -> str:
    status_id = str(status_id)
    account = account.strip()
    if not account:
        return "소지금을 추가할 아이디를 입력해주세요."
    if amount < 1:
        return "추가할 금액은 1 이상이어야 합니다."

    with BALANCE_LOCK:
        previous_addition = repository.transaction_log.find(
            status_id,
            in_column=sheet_repository.TRANSACTION_STATUS_ID,
            case_sensitive=True,
        )
        if previous_addition:
            return repository.transaction_log.cell(
                previous_addition.row,
                sheet_repository.TRANSACTION_RESULT,
            ).value

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
        user_name = repository.character.cell(
            character_finder.row,
            sheet_repository.CHARACTER_NAME,
        ).value
        result = (
            f"{user_name}님에게 {amount} 재화를 추가했습니다. "
            f"(잔액: {balance_after})"
        )
        transaction_values = [
            status_id,
            account,
            "지급",
            "소지금추가",
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
            previous_addition = repository.transaction_log.find(
                status_id,
                in_column=sheet_repository.TRANSACTION_STATUS_ID,
                case_sensitive=True,
            )
            if previous_addition:
                return repository.transaction_log.cell(
                    previous_addition.row,
                    sheet_repository.TRANSACTION_RESULT,
                ).value
            raise

        return result


def is_affordable(price: int, balance: int) -> bool:
    return balance >= price
