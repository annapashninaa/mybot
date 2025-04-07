import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import models
from api_client import search_movie_async

# Замените на свой токен, полученный у BotFather
TOKEN = "7930707459:AAFZNX7mOmja447jbv-sARsANzRC_Jt3-Sw"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Доступные команды:\n"
        "/help — помощь\n"
        "/history — история запросов\n"
        "/movie_search <название> — поиск фильма/сериала\n"
    )
    await update.message.reply_text(help_text)

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    history = models.get_history(update.effective_user.id)
    if not history:
        await update.message.reply_text("История пуста.")
    else:
        response_lines = [
            f"{item['date']} - {item['query']}:\n{item['result']}" for item in history
        ]
        await update.message.reply_text("\n\n".join(response_lines))

async def movie_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите название фильма или сериала после команды.")
        return
    query = " ".join(context.args)
    result = await search_movie_async(query)
    models.add_history(update.effective_user.id, query, result)
    await update.message.reply_text(result)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.lower()
    if text == "привет":
        await update.message.reply_text("Привет! Напиши /help для списка команд.")
    else:
        await update.message.reply_text("Неизвестная команда. Напиши /help для списка доступных команд.")

async def main() -> None:
    # Инициализация базы данных
    models.init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("movie_search", movie_search))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    await app.run_polling()
