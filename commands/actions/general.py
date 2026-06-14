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
