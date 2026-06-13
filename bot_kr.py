#!/usr/bin/python3
from mastodon import Mastodon
from mastodon.streaming import StreamListener
from google.oauth2.service_account import Credentials
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import os
import re
import random
import gspread

'''
mastodon API LIMIT = 300/5m
gspread API LIMIT = 300/1m
'''

def load_env_file(file_path=None):
    env_path = Path(file_path) if file_path else Path(__file__).with_name(".env")
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")

        if key.startswith("export "):
            key = key.removeprefix("export ").strip()

        os.environ.setdefault(key, value)


load_env_file()

# 구글 클라이언트 ID, 마스토돈 토큰 등등 환경설정 필요
mastodon = Mastodon(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        access_token=os.getenv("ACCESS_TOKEN"),
        api_base_url=os.getenv("API_BASE_URL")
        )

# 구글 스프레드시트 세팅
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         ]

# 구글 인증 키
credential_json = os.getenv("CREDENTIAL_JSON") or os.getenv("CRENDENTIAL_JSON")
credentials = Credentials.from_service_account_file(credential_json, scopes=scope)

gc = gspread.authorize(credentials)
sh = gc.open_by_url(os.getenv("GOOGLE_SHEET_URL"))

DISALLOWED_COMMAND_CHARS = re.compile(r'[^\w\s\[\]/]')

def sanitize_command_text(raw_text: str) -> str:
    soup = BeautifulSoup(raw_text, 'html.parser')
    parsed_text = soup.get_text(strip=True)
    sanitized_text = re.sub(DISALLOWED_COMMAND_CHARS, '', parsed_text)
    return sanitized_text

def parse_number(raw_value: Optional[str]) -> Optional[int]:
    try:
        return int(raw_value.strip())
    except ValueError:
        return None

# 다이스, nDm을 굴림
def dice(n: int, m: int) -> str:
    if n < 1 or m < 1:
        return "다이스는 1 이상의 숫자로 굴려주세요."
    if n > MAX_DICE_COUNT or m > MAX_DICE_SIDES:
        return f"다이스는 최대 {MAX_DICE_COUNT}d{MAX_DICE_SIDES}까지 굴릴 수 있어요."

    random_number = sum(random.randint(1, m) for _ in range(n))
    return str(random_number)

# 참 거짓
def true_or_false() -> str:
    return random.choice(["거짓", "참"])


# 키워드로만 이루어지는 조사
# @param    keyword:string
# @return   string
# API Request   1회 Google Spreadsheet API 2회
def investigate(keyword: str) -> str:
    finder = search.find(keyword, in_column=SEARCH_KEYWORD, case_sensitive=True)
    if finder:
        keyword_row = finder.row
    else:
        return "존재하지 않는 조사 키워드입니다."

    result = f"[{keyword}] " + search.cell(keyword_row, SEARCH_DESCRIPTION).value

    return result


# 상점구입
# @param    account:string
# @param    item:string
# @return   string
# API Request   1회 Google Spreadsheet API 6회
def buy_something(account: Optional[str], item: Optional[str]) -> str:
    store_finder = store.find(item, in_column=STORE_ITEM, case_sensitive=True)
    if store_finder:
        item_row = store_finder.row
    else:
        return '존재하지 않는 아이템이에요!'

    character_finder = character.find(account, in_column=CHARACTER_ACCOUNT, case_sensitive=True)
    if character_finder:
        account_row = character_finder.row
    else:
        return '존재하지 않는 유저입니다.'

    if item_row:
        price = int(store.cell(item_row, STORE_PRICE).value)
        money = int(character.cell(account_row, CHARACTER_MONEY).value)
        if is_affordable(price, money):
            budget = money - price
            character.update_cell(account_row, CHARACTER_MONEY, budget)
            user_name = character.cell(account_row, CHARACTER_NAME).value
            return f'{user_name}님, 성공적으로 {item}을 구매했어요! (잔액: {budget})'
        else:
            return '재화가 부족합니다.'
    return '함수에 오류가 있는 것 같으니 제보 바랍니다.'



# 상점구입 헬퍼함수
# @param    price:number
# @param    money:number
# @return   boolean
def is_affordable(price: int, money: int) -> bool:
    return money >= price


# 이벤트 리스너
class Listener(StreamListener):
    def on_notification(self, notification):
        if notification['type'] == "mention":
            status = notification['status']

            try:
                self.handle_mention(notification)
            except Exception as error:
                print(f"멘션 처리 중 오류: {error}")
                mastodon.status_reply(status, "처리 중 오류가 발생했어요. 관리자에게 제보해주세요.", visibility='unlisted')

    def handle_mention(self, notification):
        status = notification['status']
        print("내용은 다음과 같습니다 == " + status['content'])

        user_text = sanitize_command_text(status['content'])

        print("user_text는 다음과 같습니다 == " + user_text)

        if '[' in user_text and ']' in user_text:
            cmd_start = user_text.find("[") + 1
            cmd_end = user_text.find("]")

            user_text = user_text[cmd_start:cmd_end]


            # 조사
            # 키워드 형식: [조사/키워드]
            if "조사" in user_text and '/' in user_text:
                keyword_start = user_text.find("/") + 1
                keyword = user_text[keyword_start:]
                result = investigate(keyword)
                mastodon.status_reply(status, result, visibility='unlisted')


            # 가챠 (확률 가챠)
            # 키워드 형식: [가챠/n]
            elif user_text.startswith("가챠/"):
                round_start = user_text.find("/") + 1
                rounds = parse_number(user_text[round_start:])
                result = "가챠 횟수는 숫자로 입력해주세요." if rounds is None else gatcha_with_prob(rounds)
                mastodon.status_reply(status, result, visibility='unlisted')

            elif "가챠" in user_text:
                result = gatcha_with_description()
                mastodon.status_reply(status, result, visibility='unlisted')

            # 구매
            # 키워드 형식: [구매]
            elif "구매" in user_text and '/' in user_text:
                user_account = status['account']["username"]
                item_start = user_text.find("/") + 1
                item = user_text[item_start:]
                result = buy_something(user_account, item)
                mastodon.status_reply(status, result, visibility='unlisted')


            # 다이스
            # 키워드 형식: [ndm] 혹은 [nDm]
            elif "D" in user_text or "d" in user_text:

                if "D" in user_text:
                    user_text = user_text.lower()

                std = user_text.find("d")

                n = parse_number(user_text[:std])
                m = parse_number(user_text[std + 1:])

                result = "다이스 형식은 [nDm]으로 입력해주세요." if n is None or m is None else dice(n, m)
                mastodon.status_reply(status, result, visibility='unlisted')


            # 참/거짓
            # 키워드 형식: [T/F]
            elif "T" in user_text and "F" in user_text and '/' in user_text:
                result = true_or_false()
                mastodon.status_reply(status, result, visibility='unlisted')

        else:
            mastodon.status_reply(status, "키워드 형식이 올바르지 않은 것 같아요.", visibility='unlisted')
            print("형식이 올바르지 아니함")


    def handle_heartbeat(self):
        return super().handle_heartbeat()


# 메인함수
def main():
    mastodon.stream_user(Listener())


# 실행
if __name__ == '__main__':
    main()
