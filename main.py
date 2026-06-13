#!/usr/bin/python3
from mastodon import Mastodon
from mastodon.streaming import StreamListener

import config.settings as settings
from commands.actions import (
    buy_something,
    dice,
    investigate,
)
from commands.parser import parse_number, sanitize_command_text


"""
mastodon API LIMIT = 300/5m
gspread API LIMIT = 300/1m
"""


mastodon = Mastodon(
    client_id=settings.CLIENT_ID,
    client_secret=settings.CLIENT_SECRET,
    access_token=settings.ACCESS_TOKEN,
    api_base_url=settings.API_BASE_URL,
)


class Listener(StreamListener):
    def on_notification(self, notification):
        if notification["type"] == "mention":
            status = notification["status"]

            try:
                self.handle_mention(notification)
            except Exception as error:
                print(f"멘션 처리 중 오류: {error}")
                mastodon.status_reply(status, "처리 중 오류가 발생했어요. 관리자에게 제보해주세요.", visibility="unlisted")

    def handle_mention(self, notification):
        status = notification["status"]

        # 멘션한 유저와 멘션한 텍스트를 받아옴
        user_text = sanitize_command_text(status["content"])
        user_account = status["account"]["acct"]

        if user_text is None:
            mastodon.status_reply(status, "키워드 형식이 올바르지 않은 것 같아요.", visibility="unlisted")
            print("형식이 올바르지 아니함")
            return

        if "조사" in user_text and "/" in user_text:
            keyword_start = user_text.find("/") + 1
            keyword = user_text[keyword_start:]
            result = investigate(keyword)
            mastodon.status_reply(status, result, visibility="unlisted")

        elif "구매" in user_text and "/" in user_text:
            item_start = user_text.find("/") + 1
            item = user_text[item_start:]
            result = buy_something(str(status["id"]), user_account, item)
            mastodon.status_reply(status, result, visibility="unlisted")

        elif "D" in user_text or "d" in user_text:
            if "D" in user_text:
                user_text = user_text.lower()

            std = user_text.find("d")

            n = parse_number(user_text[:std])
            m = parse_number(user_text[std + 1:])

            result = "다이스 형식은 [nDm]으로 입력해주세요." if n is None or m is None else dice(n, m)
            mastodon.status_reply(status, result, visibility="unlisted")

    def handle_heartbeat(self):
        return super().handle_heartbeat()


def main():
    mastodon.stream_user(Listener())


if __name__ == "__main__":
    main()
