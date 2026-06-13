import random

import sheets


MAX_DICE_COUNT = 100
MAX_DICE_SIDES = 1000


def dice(n: int, m: int) -> str:
    if n < 1 or m < 1:
        return "다이스는 1 이상의 숫자로 굴려주세요."
    if n > MAX_DICE_COUNT or m > MAX_DICE_SIDES:
        return f"다이스는 최대 {MAX_DICE_COUNT}d{MAX_DICE_SIDES}까지 굴릴 수 있어요."

    random_number = sum(random.randint(1, m) for _ in range(n))
    return str(random_number)


def investigate(keyword: str) -> str:
    finder = sheets.search.find(keyword, in_column=sheets.SEARCH_KEYWORD, case_sensitive=True)
    if not finder:
        return "존재하지 않는 조사 키워드입니다."

    result = f"[{keyword}] " + sheets.search.cell(finder.row, sheets.SEARCH_DESCRIPTION).value
    return result


def buy_something(account: str, item: str) -> str:
    store_finder = sheets.store.find(item, in_column=sheets.STORE_ITEM, case_sensitive=True)
    if not store_finder:
        return "존재하지 않는 아이템입니다."

    character_finder = sheets.character.find(account, in_column=sheets.CHARACTER_ACCOUNT, case_sensitive=True)
    if not character_finder:
        return "존재하지 않는 유저입니다."

    price = int(sheets.store.cell(store_finder.row, sheets.STORE_PRICE).value)
    money = int(sheets.character.cell(character_finder.row, sheets.CHARACTER_MONEY).value)
    if not is_affordable(price, money):
        return "재화가 부족합니다."

    budget = money - price
    sheets.character.update_cell(character_finder.row, sheets.CHARACTER_MONEY, budget)
    user_name = sheets.character.cell(character_finder.row, sheets.CHARACTER_NAME).value
    return f"{user_name}님, {item}을 구매했습니다. (잔액: {budget})"


def is_affordable(price: int, money: int) -> bool:
    return money >= price
