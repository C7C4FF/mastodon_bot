from google.oauth2.service_account import Credentials
import gspread

import config

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
]

credentials = Credentials.from_service_account_file(config.CREDENTIAL_JSON, scopes=SCOPE)

gc = gspread.authorize(credentials)
spreadsheet = gc.open_by_url(config.GOOGLE_SHEET_URL)


# 이하는 커뮤 맞춤 설정

SEARCH_KEYWORD = 1
SEARCH_DESCRIPTION = 2

STORE_ITEM = 1
STORE_PRICE = 2

CHARACTER_ACCOUNT = 1
CHARACTER_NAME = 2
CHARACTER_MONEY = 3

search = spreadsheet.worksheet("조사")
store = spreadsheet.worksheet("상점")
character = spreadsheet.worksheet("캐릭터")
