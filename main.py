import os
import re
from dotenv import load_dotenv

load_dotenv()

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
    CommandHandler,
)

from src.exceptions import BotException
from src.logging import log_command
from src.session import sessions
from src.strategy import *


@log_command
async def suggest_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        update.message is None
        or update.message.text is None
        or update.effective_chat is None
        or update.effective_user is None
    ):
        return

    # Parse the guesses from the command (e.g., "/suggest TRAIN: 01020")
    lines = update.message.text.splitlines()
    if len(lines) < 2:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=("Usage: /suggest\nSLATE: 01020"),
        )
        return

    session = sessions.get(update.effective_user.id, update.effective_chat.id)

    # Register new guesses
    for line in lines[1:]:
        line = line.strip()
        match = re.match(r"^([a-zA-Z]{5}): ([012]{5})$", line)
        if not match:
            raise BotException(f"Invalid format: {line}")

        guess, raw_result = match.groups()
        session.add_guess(guess, raw_result)

    # Check for win
    if session.is_won():
        guess_count = len(session.guesses)
        sessions.reset(update.effective_user.id, update.effective_chat.id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🎉 You won in {guess_count}/6 guesses!",
        )
        return

    # Check for game over
    if session.is_complete():
        sessions.reset(update.effective_user.id, update.effective_chat.id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Game over! You've used all 6 guesses. Use /newgame to start again.",
        )
        return

    # Build history display
    history_lines = []
    for g in session.guesses:
        result_display = "".join(
            "⬜️" if c == "0" else "🟩" if c == "1" else "🟨" for c in g.result
        )
        history_lines.append(f"{result_display}  {g.word}")

    suggestions = session.strategy.execute(guesses=session.guesses, n=3)
    suggestions_text = ", ".join(suggestions)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="\n".join(history_lines) + f"\n\nTry: {suggestions_text}",
    )


@log_command
async def strategy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_chat is None:
        return

    keyboard = [
        [
            InlineKeyboardButton("Entropy (Fast)", callback_data="strategy_entropy"),
            InlineKeyboardButton("Minimax (Smart)", callback_data="strategy_minimax"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Select a strategy:",
        reply_markup=reply_markup,
    )


async def strategy_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if (
        query is None
        or query.data is None
        or update.effective_user is None
        or update.effective_chat is None
    ):
        return

    await query.answer()

    session = sessions.get(update.effective_user.id, update.effective_chat.id)

    if query.data == "strategy_entropy":
        session.strategy = EntropyStrategy()
    elif query.data == "strategy_minimax":
        session.strategy = MinimaxStrategy()
    else:
        raise BotException(f"Unknown strategy: {query.data}")

    await query.edit_message_text(
        text=(
            f"You selected: {session.strategy.name}\n" f"Your session has been updated."
        )
    )


@log_command
async def newgame_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        update.message is None
        or update.effective_chat is None
        or update.effective_user is None
    ):
        return

    session = sessions.get(update.effective_user.id, update.effective_chat.id)
    previous_count = len(session.guesses)
    session.reset()

    if previous_count > 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                f"New game started! (Previous game cleared at {previous_count}/6 guesses)\n"
                f"Current Strategy: {session.strategy.name}"
            ),
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"New game started!\nCurrent Strategy: {session.strategy.name}",
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler for all uncaught exceptions."""

    if isinstance(context.error, BotException):
        message = f"An error occurred: {context.error}"
    else:
        message = "An unexpected error occurred. Please try again."

    if update and isinstance(update, Update) and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message,
        )


def main():
    print("Beginning bot intialization...")

    print("Fetching token...")
    bot_token = os.getenv("TELEGRAM_TOKEN")
    if not bot_token:
        raise ValueError("Telegram bot token not found")
    print("Token successfully fetched.")

    print("Registering handlers...")
    application = ApplicationBuilder().token(bot_token).build()
    application.add_handler(CommandHandler("suggest", suggest_handler))
    application.add_handler(CommandHandler("newgame", newgame_handler))
    application.add_handler(CommandHandler("strategy", strategy_handler))
    application.add_handler(
        CallbackQueryHandler(strategy_callback_handler, pattern="^strategy_")
    )
    application.add_error_handler(error_handler)
    print("Handlers successfully registered.")

    print("Bot successfully initialized.")

    try:
        print("Starting bot...")
        application.run_polling()
    finally:
        print("Bot successfully shutdown.")


if __name__ == "__main__":
    main()
