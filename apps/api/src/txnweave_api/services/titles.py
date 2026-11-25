"""Display titles (data-model "title", BD24). Shared by saved documents and placeholders.

Any part that isn't known (a blank register, or a placeholder's missing date or store) is left
out together with its " · " separator. Card numbers only ever show their last 4 digits (B13).
"""

from datetime import date


def transaction_title(number: str, on: date | None, store: str | None, register: str | None) -> str:
    parts = [f"Transaction {number}"]
    if on is not None:
        parts.append(on.strftime("%m-%d-%Y"))
    if store:
        parts.append(f"Store {store}")
    if register:
        parts.append(f"Reg {register}")
    return " · ".join(parts)


def gift_card_title(number: str) -> str:
    return f"Gift Card …{number[-4:]}"


def online_order_title(number: str) -> str:
    return f"Online Order {number}"
