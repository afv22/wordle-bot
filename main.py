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
from src.session import sessions


@log_command
async def suggest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        update.message is None
        or update.message.text is None
        or update.effective_chat is None
        or update.effective_user is None
    ):
        return

    # Parse the guess from the command (e.g., "/suggest TRAIN: 01020")
    lines = update.message.text.splitlines()
    if len(lines) < 2:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=("Usage: /suggest\nWORD: 01020"),
        )
        return

    line = lines[1].strip()
    match = re.match(r"^([a-zA-Z]{5}): ([012]{5})$", line)
    if not match:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Invalid format: {line}\nExpected: WORD: 01020",
        )
        raise ValueError(f"Invalid format: {line}")

    guess, raw_result = match.groups()

    # Get or create session and add the guess
    session = sessions.get(update.effective_user.id, update.effective_chat.id)
    session.add_guess(guess, raw_result)

    # Check for win
    if session.is_won():
        guess_count = len(session.guesses)
        sessions.clear(update.effective_user.id, update.effective_chat.id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🎉 You won in {guess_count}/6 guesses!",
        )
        return

    # Check for game over
    if session.is_complete():
        sessions.clear(update.effective_user.id, update.effective_chat.id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Game over! You've used all 6 guesses. Use /newgame to start again.",
        )
        return

    # TODO: Replace with actual word suggestion logic
    result_display = [
        "⬜️" if c == "0" else "🟩" if c == "1" else "🟨" for c in raw_result
    ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"{guess.upper()}: {''.join(result_display)} ({len(session.guesses)}/6)\n\nTry: SLATE",
    )


@log_command
async def newgame_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        update.message is None
        or update.effective_chat is None
        or update.effective_user is None
    ):
        return

    previous_count = sessions.clear(update.effective_user.id, update.effective_chat.id)

    if previous_count > 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"New game started! (Previous game cleared at {previous_count}/6 guesses)",
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="New game started!",
        )


def main():
    bot_token = os.getenv("TELEGRAM_TOKEN")
    if not bot_token:
        raise ValueError("Telegram bot token not found")

    application = ApplicationBuilder().token(bot_token).build()
    application.add_handler(CommandHandler("suggest", suggest_handler))
    application.add_handler(CommandHandler("newgame", newgame_handler))

    application.run_polling()


if __name__ == "__main__":
    main()
