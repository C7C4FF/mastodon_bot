#!/usr/bin/python3
from mastodon import Mastodon
from mastodon.streaming import StreamListener

import config
from commands.commands import (
    buy_something,
    dice,
    investigate,
)
from commands.utils import parse_number, sanitize_command_text


"""
mastodon API LIMIT = 300/5m
gspread API LIMIT = 300/1m
"""


mastodon = Mastodon(
    client_id=config.CLIENT_ID,
    client_secret=config.CLIENT_SECRET,
    access_token=config.ACCESS_TOKEN,
    api_base_url=config.API_BASE_URL,
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
        print("내용은 다음과 같습니다 == " + status["content"])

        user_text = sanitize_command_text(status["content"])

        print("user_text는 다음과 같습니다 == " + user_text)

        if "[" not in user_text or "]" not in user_text:
            mastodon.status_reply(status, "키워드 형식이 올바르지 않은 것 같아요.", visibility="unlisted")
            print("형식이 올바르지 아니함")
            return

        cmd_start = user_text.find("[") + 1
        cmd_end = user_text.find("]")
        user_text = user_text[cmd_start:cmd_end]

        if "조사" in user_text and "/" in user_text:
            keyword_start = user_text.find("/") + 1
            keyword = user_text[keyword_start:]
            result = investigate(keyword)
            mastodon.status_reply(status, result, visibility="unlisted")

        elif "구매" in user_text and "/" in user_text:
            user_account = status["account"]["username"]
            item_start = user_text.find("/") + 1
            item = user_text[item_start:]
            result = buy_something(user_account, item)
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
