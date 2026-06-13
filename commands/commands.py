import random
import threading
from datetime import datetime, timezone

import sheets.sheets as sheet_data

MAX_DICE_COUNT = 100
MAX_DICE_SIDES = 1000
PURCHASE_LOCK = threading.Lock()


def dice(n: int, m: int) -> str:
    if n < 1 or m < 1:
        return "다이스는 1 이상의 숫자로 굴려주세요."
    if n > MAX_DICE_COUNT or m > MAX_DICE_SIDES:
        return f"다이스는 최대 {MAX_DICE_COUNT}d{MAX_DICE_SIDES}까지 굴릴 수 있어요."

    random_number = sum(random.randint(1, m) for _ in range(n))
    return str(random_number)


def investigate(keyword: str) -> str:
    finder = sheet_data.search.find(
        keyword,
        in_column=sheet_data.SEARCH_KEYWORD,
        case_sensitive=True,
    )
    if not finder:
        return "존재하지 않는 조사 키워드입니다."

    result = f"[{keyword}] " + sheet_data.search.cell(
        finder.row,
        sheet_data.SEARCH_DESCRIPTION,
    ).value
    return result


def buy_something(status_id: str, account: str, item: str) -> str:
    status_id = str(status_id)
    item = item.strip()
    if not item:
        return "구매할 아이템을 입력해주세요."

    with PURCHASE_LOCK:
        previous_purchase = sheet_data.purchase_log.find(
            status_id,
            in_column=sheet_data.PURCHASE_STATUS_ID,
            case_sensitive=True,
        )
        if previous_purchase:
            return sheet_data.purchase_log.cell(
                previous_purchase.row,
                sheet_data.PURCHASE_RESULT,
            ).value

        store_finder = sheet_data.store.find(
            item,
            in_column=sheet_data.STORE_ITEM,
            case_sensitive=True,
        )
        if not store_finder:
            return "존재하지 않는 아이템입니다."

        character_finder = sheet_data.character.find(
            account,
            in_column=sheet_data.CHARACTER_ACCOUNT,
            case_sensitive=True,
        )
        if not character_finder:
            return "존재하지 않는 유저입니다."

        price = int(
            sheet_data.store.cell(
                store_finder.row,
                sheet_data.STORE_PRICE,
            ).value
        )
        if price < 1:
            raise ValueError("아이템 가격은 1 이상이어야 합니다.")

        base_money = int(
            sheet_data.character.cell(
                character_finder.row,
                sheet_data.CHARACTER_MONEY,
            ).value
        )
        money = base_money - get_total_purchase_amount(account)
        if not is_affordable(price, money):
            return "재화가 부족합니다."

        budget = money - price
        user_name = sheet_data.character.cell(
            character_finder.row,
            sheet_data.CHARACTER_NAME,
        ).value
        result = f"{user_name}님, {item}을 구매했습니다. (잔액: {budget})"

        sheet_data.purchase_log.append_row(
            [
                status_id,
                account,
                item,
                price,
                budget,
                result,
                datetime.now(timezone.utc).isoformat(),
            ]
        )
        return result


def get_total_purchase_amount(account: str) -> int:
    total = 0

    for row in sheet_data.purchase_log.get_all_values():
        if len(row) < sheet_data.PURCHASE_PRICE:
            continue
        if row[sheet_data.PURCHASE_ACCOUNT - 1] != account:
            continue

        price = int(row[sheet_data.PURCHASE_PRICE - 1])
        if price < 1:
            raise ValueError("구매 원장의 가격은 1 이상이어야 합니다.")
        total += price

    return total


def is_affordable(price: int, money: int) -> bool:
    return money >= price
