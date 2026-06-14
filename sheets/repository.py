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

TRANSACTION_STATUS_ID = 1
TRANSACTION_ACCOUNT = 2
TRANSACTION_TYPE = 3
TRANSACTION_TARGET = 4
TRANSACTION_AMOUNT = 5
TRANSACTION_BALANCE_BEFORE = 6
TRANSACTION_BALANCE_AFTER = 7
TRANSACTION_RESULT = 8
TRANSACTION_PROCESSED_AT = 9


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
        self.transaction_log = self.spreadsheet.worksheet("재화내역")

    def record_transaction(
        self,
        character_row: int,
        balance_after: int,
        transaction_values: list[str | int],
    ) -> None:
        if len(transaction_values) != TRANSACTION_PROCESSED_AT:
            raise ValueError("재화 원장 값의 개수가 올바르지 않습니다.")

        transaction_row = len(
            self.transaction_log.col_values(TRANSACTION_STATUS_ID)
        ) + 1
        character_cell = rowcol_to_a1(
            character_row,
            CHARACTER_MONEY,
        )
        transaction_range = f"A{transaction_row}:I{transaction_row}"

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
                            self.transaction_log.title,
                            transaction_range,
                        ),
                        "values": [transaction_values],
                    },
                ],
            }
        )
