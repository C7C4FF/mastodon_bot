import random

import sheets.repository as sheet_repository

MAX_DICE_COUNT = 100
MAX_DICE_SIDES = 1000


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


def draw(repository: sheet_repository.SheetRepository) -> str:
    items = [
        (
            row[sheet_repository.DRAW_ITEM - 1].strip(),
            (
                row[sheet_repository.DRAW_DESCRIPTION - 1].strip()
                if len(row) >= sheet_repository.DRAW_DESCRIPTION
                else ""
            ),
        )
        for row in repository.draw.get_all_values()[1:]
        if len(row) >= sheet_repository.DRAW_ITEM
        and row[sheet_repository.DRAW_ITEM - 1].strip()
    ]
    if not items:
        return "뽑을 수 있는 아이템이 없습니다."

    item_name, description = random.choice(items)
    return f"{item_name}을 뽑았다. {description}"


def show_balance(
    repository: sheet_repository.SheetRepository,
    account: str,
) -> str:
    character = repository.character.find(
        account,
        in_column=sheet_repository.CHARACTER_ACCOUNT,
        case_sensitive=True,
    )
    if not character:
        return "존재하지 않는 유저입니다."

    user_name = repository.character.cell(
        character.row,
        sheet_repository.CHARACTER_NAME,
    ).value
    balance = repository.character.cell(
        character.row,
        sheet_repository.CHARACTER_MONEY,
    ).value
    return f"{user_name}님의 현재 소지금: {balance}"


def show_inventory(
    repository: sheet_repository.SheetRepository,
    account: str,
) -> str:
    character = repository.character.find(
        account,
        in_column=sheet_repository.CHARACTER_ACCOUNT,
        case_sensitive=True,
    )
    if not character:
        return "존재하지 않는 유저입니다."

    user_name = repository.character.cell(
        character.row,
        sheet_repository.CHARACTER_NAME,
    ).value
    inventory = repository.character.cell(
        character.row,
        sheet_repository.CHARACTER_ITEMS,
    ).value.strip()
    if not inventory:
        return f"{user_name}님의 가방이 비어 있습니다."
    return f"{user_name}님의 가방: {inventory}"
