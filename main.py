import os
import re
from dotenv import load_dotenv

load_dotenv()

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
)

from src.logging import log_command


@log_command
async def suggest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_chat is None:
        return

    user_message = update.message.text
    if not user_message:
        return

    for line in user_message.splitlines()[1:]:
        try:
            match = re.match(r"^([a-zA-Z]{5}): ([012]{5})$", line)
            if not match:
                raise ValueError(f"Invalid format: {line}")
            guess, raw_result = match.groups()
            result = [
                "⬜️" if square == "0" else "🟩" if square == "1" else "🟨"
                for square in raw_result
            ]
        except Exception:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Failed to parse line: {line}",
            )
            raise

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"You guessed {guess}: {''.join(result)}",
        )


def main():
    bot_token = os.getenv("TELEGRAM_TOKEN")
    if not bot_token:
        raise ValueError("Telegram bot token not found")

    application = ApplicationBuilder().token(bot_token).build()
    application.add_handler(CommandHandler("suggest", suggest_handler))

    application.run_polling()


if __name__ == "__main__":
    main()
