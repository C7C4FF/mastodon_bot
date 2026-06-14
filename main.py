#!/usr/bin/python3
import time

from mastodon import Mastodon
from mastodon.streaming import StreamListener

import config.settings as settings
from commands.actions import (
    add_money,
    buy_something,
    dice,
    draw,
    investigate,
    transfer_item,
    transfer_money,
)
from commands.extractor import extract_command_text
from commands.models import (
    AddMoneyCommand,
    DiceCommand,
    DrawCommand,
    InvestigateCommand,
    PurchaseCommand,
    TransferItemCommand,
    TransferMoneyCommand,
)
from commands.parser import parse_command
from sheets.repository import SheetRepository


"""
mastodon API LIMIT = 300/5m
gspread API LIMIT = 300/1m
"""


class Listener(StreamListener):
    def __init__(self, mastodon: Mastodon, repository: SheetRepository):
        self.mastodon = mastodon
        self.repository = repository

    def on_notification(self, notification):
        if notification["type"] == "mention":
            status = notification["status"]
            status_id = str(status["id"])

            try:
                result = self.handle_mention(notification)
            except Exception as error:
                print(f"멘션 처리 중 오류 (status_id={status_id}): {error}")
                self.send_reply(
                    status,
                    "처리 중 오류가 발생했어요. 관리자에게 제보해주세요.",
                    idempotency_key=f"mention-error:{status_id}",
                )
                return

            self.send_reply(
                status,
                result,
                idempotency_key=f"mention-reply:{status_id}",
            )

    def send_reply(self, status, result: str, idempotency_key: str) -> None:
        for attempt in range(2):
            try:
                self.mastodon.status_reply(
                    status,
                    result,
                    idempotency_key=idempotency_key,
                )
                return
            except Exception as error:
                if attempt == 1:
                    print(
                        "답글 전송 중 오류 "
                        f"(status_id={status['id']}): {error}"
                    )

    def handle_mention(self, notification) -> str:
        status = notification["status"]

        # 멘션한 유저와 멘션한 텍스트를 받아옴
        user_text = extract_command_text(status["content"])
        user_account = status["account"]["acct"]

        command = parse_command(user_text) if user_text is not None else None
        if command is None:
            return "명령어 형식이 올바르지 않은 것 같아요."

        if isinstance(command, InvestigateCommand):
            return investigate(self.repository, command.keyword)
        if isinstance(command, DrawCommand):
            return draw(self.repository)
        if isinstance(command, PurchaseCommand):
            return buy_something(
                self.repository,
                str(status["id"]),
                user_account,
                command.item,
            )
        if isinstance(command, AddMoneyCommand):
            return add_money(
                self.repository,
                str(status["id"]),
                command.accounts,
                command.amount,
            )
        if isinstance(command, TransferMoneyCommand):
            return transfer_money(
                self.repository,
                str(status["id"]),
                user_account,
                command.recipient_account,
                command.amount,
            )
        if isinstance(command, TransferItemCommand):
            return transfer_item(
                self.repository,
                str(status["id"]),
                user_account,
                command.recipient_account,
                command.item,
                command.count,
            )
        if isinstance(command, DiceCommand):
            return dice(command.count, command.sides)

        raise ValueError("지원하지 않는 명령어입니다.")

    def handle_heartbeat(self):
        return super().handle_heartbeat()


def main():
    mastodon = Mastodon(
        client_id=settings.CLIENT_ID,
        client_secret=settings.CLIENT_SECRET,
        access_token=settings.ACCESS_TOKEN,
        api_base_url=settings.API_BASE_URL,
    )

    repository = SheetRepository(
        settings.CREDENTIAL_JSON,
        settings.GOOGLE_SHEET_URL,
    )

    stream = mastodon.stream_user(
        Listener(mastodon, repository),
        run_async=True,
        reconnect_async=True,
        reconnect_async_wait_sec=10,
    )

    try:
        while stream.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        return
    finally:
        stream.close()

    raise RuntimeError("Mastodon 스트림이 예기치 않게 종료되었습니다.")


if __name__ == "__main__":
    main()
