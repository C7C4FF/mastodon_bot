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

DRAW_ITEM = 1
DRAW_DESCRIPTION = 2

CHARACTER_ACCOUNT = 1
CHARACTER_NAME = 2
CHARACTER_MONEY = 3
CHARACTER_ITEMS = 4

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
        self.draw = self.spreadsheet.worksheet("뽑기")
        self.character = self.spreadsheet.worksheet("캐릭터")
        self.transaction_log = self.spreadsheet.worksheet("재화내역")

    def record_transaction(
        self,
        character_row: int,
        balance_after: int,
        transaction_values: list[str | int],
    ) -> None:
        self._record_transaction(
            character_row,
            balance_after,
            transaction_values,
        )

    def record_purchase(
        self,
        character_row: int,
        balance_after: int,
        inventory_after: str,
        transaction_values: list[str | int],
    ) -> None:
        self._record_transaction(
            character_row,
            balance_after,
            transaction_values,
            inventory_after=inventory_after,
        )

    def record_money_transfer(
        self,
        sender_row: int,
        sender_balance_after: int,
        recipient_row: int,
        recipient_balance_after: int,
        transaction_values: list[list[str | int]],
    ) -> None:
        self._record_transfer(
            [
                (sender_row, CHARACTER_MONEY, sender_balance_after),
                (recipient_row, CHARACTER_MONEY, recipient_balance_after),
            ],
            transaction_values,
        )

    def record_item_transfer(
        self,
        sender_row: int,
        sender_inventory_after: str,
        recipient_row: int,
        recipient_inventory_after: str,
        transaction_values: list[list[str | int]],
    ) -> None:
        self._record_transfer(
            [
                (sender_row, CHARACTER_ITEMS, sender_inventory_after),
                (recipient_row, CHARACTER_ITEMS, recipient_inventory_after),
            ],
            transaction_values,
        )

    def _record_transaction(
        self,
        character_row: int,
        balance_after: int,
        transaction_values: list[str | int],
        inventory_after: str | None = None,
    ) -> None:
        data = [
            self._character_cell_update(
                character_row,
                CHARACTER_MONEY,
                balance_after,
            )
        ]

        if inventory_after is not None:
            data.append(
                self._character_cell_update(
                    character_row,
                    CHARACTER_ITEMS,
                    inventory_after,
                )
            )

        data.append(self._transaction_update([transaction_values]))
        self.spreadsheet.values_batch_update(
            {
                "valueInputOption": "RAW",
                "data": data,
            }
        )

    def _record_transfer(
        self,
        character_updates: list[tuple[int, int, str | int]],
        transaction_values: list[list[str | int]],
    ) -> None:
        data = [
            self._character_cell_update(row, column, value)
            for row, column, value in character_updates
        ]
        data.append(self._transaction_update(transaction_values))
        self.spreadsheet.values_batch_update(
            {
                "valueInputOption": "RAW",
                "data": data,
            }
        )

    def _character_cell_update(
        self,
        row: int,
        column: int,
        value: str | int,
    ) -> dict:
        return {
            "range": absolute_range_name(
                self.character.title,
                rowcol_to_a1(row, column),
            ),
            "values": [[value]],
        }

    def _transaction_update(
        self,
        transaction_values: list[list[str | int]],
    ) -> dict:
        if not transaction_values or any(
            len(values) != TRANSACTION_PROCESSED_AT
            for values in transaction_values
        ):
            raise ValueError("재화 원장 값의 개수가 올바르지 않습니다.")

        first_row = len(
            self.transaction_log.col_values(TRANSACTION_STATUS_ID)
        ) + 1
        last_row = first_row + len(transaction_values) - 1
        transaction_range = f"A{first_row}:I{last_row}"
        return {
            "range": absolute_range_name(
                self.transaction_log.title,
                transaction_range,
            ),
            "values": transaction_values,
        }
