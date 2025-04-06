import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, 
    CallbackContext, ConversationHandler
)
from config import TOKEN, TMDB_API_KEY
from database.models import User, SearchHistory
import requests

# Настройки логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
TITLE, GENRE, COUNT = range(3)

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    User.get_or_create(user_id=user.id, defaults={'username': user.username})
    update.message.reply_text(
        f"Привет, {user.first_name}! Я бот для поиска фильмов.\n"
        "Используй /help для списка команд"
    )

def help_command(update: Update, context: CallbackContext) -> None:
    commands = [
        "/movie_search - Поиск по названию",
        "/movie_by_rating - Поиск по рейтингу",
        "/low_budget_movie - Фильмы с низким бюджетом",
        "/high_budget_movie - Фильмы с высоким бюджетом",
        "/history - История поиска"
    ]
    update.message.reply_text("\n".join(commands))

def movie_search(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Введите название фильма:")
    return TITLE

def process_search(update: Update, context: CallbackContext) -> None:
    # Реализация поиска через TMDB API
    pass

def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Ошибка обработки запроса:", exc_info=context.error)
    update.message.reply_text("Произошла ошибка. Попробуйте позже.")

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Регистрация обработчиков команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # ConversationHandler для поиска
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('movie_search', movie_search)],
        states={
            TITLE: [MessageHandler(Filters.text & ~Filters.command, process_title)],
            GENRE: [MessageHandler(Filters.text & ~Filters.command, process_genre)],
            COUNT: [MessageHandler(Filters.text & ~Filters.command, process_count)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conv_handler)
    
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
