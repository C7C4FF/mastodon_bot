from dataclasses import dataclass


@dataclass(frozen=True)
class CommandContext:
    status_id: str
    user_account: str
