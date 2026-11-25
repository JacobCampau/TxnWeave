"""App errors with the API's error body (api.md "Endpoints").

Services raise AppError; main.py turns it into
{"detail": {"code": "<code>", "message": "<text>", ...extra}} with the given status code.
"""

from typing import Any


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = {"code": code, "message": message, **extra}


def not_found(what: str) -> AppError:
    return AppError(404, "not_found", f"{what} was not found.")
