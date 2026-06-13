#!/usr/bin/python3
from mastodon import Mastodon
from mastodon.streaming import StreamListener

import config.settings as settings
from commands.actions import (
    buy_something,
    dice,
    investigate,
)
from commands.parser import (
    DiceCommand,
    InvestigateCommand,
    PurchaseCommand,
    parse_command,
    sanitize_command_text,
)
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

            try:
                self.handle_mention(notification)
            except Exception as error:
                print(f"멘션 처리 중 오류: {error}")
                self.mastodon.status_reply(
                    status,
                    "처리 중 오류가 발생했어요. 관리자에게 제보해주세요.",
                )

    def handle_mention(self, notification):
        status = notification["status"]

        # 멘션한 유저와 멘션한 텍스트를 받아옴
        user_text = sanitize_command_text(status["content"])
        user_account = status["account"]["acct"]

        command = parse_command(user_text) if user_text is not None else None
        if command is None:
            self.mastodon.status_reply(
                status,
                "명령어 형식이 올바르지 않은 것 같아요.",
            )
            print("형식이 올바르지 아니함")
            return

        if isinstance(command, InvestigateCommand):
            result = investigate(self.repository, command.keyword)
        elif isinstance(command, PurchaseCommand):
            result = buy_something(
                self.repository,
                str(status["id"]),
                user_account,
                command.item,
            )
        elif isinstance(command, DiceCommand):
            result = dice(command.count, command.sides)

        self.mastodon.status_reply(status, result)

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
    mastodon.stream_user(Listener(mastodon, repository))


if __name__ == "__main__":
    main()
