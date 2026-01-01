import os
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

load_dotenv()


async def suggest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_chat is None:
        return

    user_message = update.message.text
    if not user_message:
        return

    for line in user_message.splitlines()[1:]:
        try:
            guess, raw_result = line.split(": ")
            result = [
                "⬜️" if square == "0" else "🟩" if square == "1" else "🟨"
                for square in raw_result
            ]
        except:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Failed to parse line: {line}",
            )
            return

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"You guessed {guess}: {''.join(result)}",
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_chat is None:
        return

    user_message = update.message.text
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"You said: {user_message}",
    )


def main():
    bot_token = os.getenv("TELEGRAM_TOKEN")
    if not bot_token:
        raise ValueError("Telegram bot token not found")

    application = ApplicationBuilder().token(bot_token).build()
    application.add_handler(CommandHandler("suggest", suggest))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    application.run_polling()


if __name__ == "__main__":
    main()
