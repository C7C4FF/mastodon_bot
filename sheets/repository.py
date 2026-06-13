from google.oauth2.service_account import Credentials
import gspread

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
]

SEARCH_KEYWORD = 1
SEARCH_DESCRIPTION = 2

STORE_ITEM = 1
STORE_PRICE = 2

CHARACTER_ACCOUNT = 1
CHARACTER_NAME = 2
CHARACTER_MONEY = 3

PURCHASE_STATUS_ID = 1
PURCHASE_ACCOUNT = 2
PURCHASE_ITEM = 3
PURCHASE_PRICE = 4
PURCHASE_BALANCE = 5
PURCHASE_RESULT = 6
PURCHASE_PROCESSED_AT = 7


class SheetRepository:
    def __init__(self, credential_json: str, sheet_url: str):
        credentials = Credentials.from_service_account_file(
            credential_json,
            scopes=SCOPE,
        )
        client = gspread.authorize(credentials)
        spreadsheet = client.open_by_url(sheet_url)

        self.search = spreadsheet.worksheet("조사")
        self.store = spreadsheet.worksheet("상점")
        self.character = spreadsheet.worksheet("캐릭터")
        self.purchase_log = spreadsheet.worksheet("구매내역")
