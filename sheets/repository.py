from google.oauth2.service_account import Credentials
import gspread
from gspread.utils import absolute_range_name, rowcol_to_a1

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
PURCHASE_BALANCE_BEFORE = 5
PURCHASE_BALANCE_AFTER = 6
PURCHASE_RESULT = 7
PURCHASE_PROCESSED_AT = 8


class SheetRepository:
    def __init__(self, credential_json: str, sheet_url: str):
        credentials = Credentials.from_service_account_file(
            credential_json,
            scopes=SCOPE,
        )
        client = gspread.authorize(credentials)
        self.spreadsheet = client.open_by_url(sheet_url)

        self.search = self.spreadsheet.worksheet("조사")
        self.store = self.spreadsheet.worksheet("상점")
        self.character = self.spreadsheet.worksheet("캐릭터")
        self.purchase_log = self.spreadsheet.worksheet("구매내역")

    def record_purchase(
        self,
        character_row: int,
        balance_after: int,
        purchase_values: list[str | int],
    ) -> None:
        if len(purchase_values) != PURCHASE_PROCESSED_AT:
            raise ValueError("구매 원장 값의 개수가 올바르지 않습니다.")

        purchase_row = len(
            self.purchase_log.col_values(PURCHASE_STATUS_ID)
        ) + 1
        character_cell = rowcol_to_a1(
            character_row,
            CHARACTER_MONEY,
        )
        purchase_range = f"A{purchase_row}:H{purchase_row}"

        self.spreadsheet.values_batch_update(
            {
                "valueInputOption": "RAW",
                "data": [
                    {
                        "range": absolute_range_name(
                            self.character.title,
                            character_cell,
                        ),
                        "values": [[balance_after]],
                    },
                    {
                        "range": absolute_range_name(
                            self.purchase_log.title,
                            purchase_range,
                        ),
                        "values": [purchase_values],
                    },
                ],
            }
        )
