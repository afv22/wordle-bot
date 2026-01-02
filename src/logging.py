import json
import logging
import os
from pathlib import Path
import time
import uuid
from functools import wraps
from typing import Any, Callable

from telegram import Update
from telegram.ext import ContextTypes

from src.exceptions import BotException


class StructuredLogger:
    """JSON structured logger for consistent, parseable log output."""

    def __init__(self, name: str, log_dir: Path):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            handler = logging.FileHandler(log_dir / "bot.log")
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)

    def _log(self, level: str, message: str, **kwargs: Any) -> None:
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "level": level,
            "message": message,
            **kwargs,
        }
        log_method = getattr(self.logger, level.lower())
        log_method(json.dumps(log_entry))

    def info(self, message: str, **kwargs: Any) -> None:
        self._log("INFO", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._log("ERROR", message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        self._log("DEBUG", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._log("WARNING", message, **kwargs)


logger = StructuredLogger("wordle_bot", Path(os.getenv("LOG_DIR", "./logs")))


def log_command(func: Callable) -> Callable:
    """Decorator to log command handler execution with context."""

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        user = update.effective_user
        chat = update.effective_chat
        user_info = {
            "user_id": user.id if user else None,
            "username": user.username if user else None,
        }
        chat_info = {
            "chat_id": chat.id if chat else None,
            "chat_type": chat.type if chat else None,
        }

        try:
            result = await func(update, context)
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "command_executed",
                request_id=request_id,
                command=func.__name__,
                user=user_info,
                chat=chat_info,
                execution_time_ms=round(execution_time_ms, 2),
                status="success",
            )
            return result

        except Exception as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000

            logger.error(
                "command_executed",
                request_id=request_id,
                command=func.__name__,
                user=user_info,
                chat=chat_info,
                execution_time_ms=round(execution_time_ms, 2),
                status="error",
                error_type=type(e).__name__,
                error_message=str(e),
            )

    return wrapper
