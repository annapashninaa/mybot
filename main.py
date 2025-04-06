import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, 
    CallbackContext, ConversationHandler
)
from config import TELEGRAM_TOKEN, KINOPOISK_API_KEY
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
KINOPOISK_API_URL = "https://api.kinopoisk.dev/v1.3/movie"

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

def process_title(update: Update, context: CallbackContext) -> int:
    context.user_data['title'] = update.message.text
    update.message.reply_text("Введите жанр (например, комедия):")
    return GENRE

def process_genre(update: Update, context: CallbackContext) -> int:
    context.user_data['genre'] = update.message.text
    update.message.reply_text("Сколько результатов показать? (1-10)")
    return COUNT

def process_count(update: Update, context: CallbackContext) -> int:
    try:
        count = int(update.message.text)
        if not 1 <= count <= 10:
            raise ValueError
    except ValueError:
        update.message.reply_text("Некорректное число. Введите от 1 до 10.")
        return COUNT

    headers = {"X-API-KEY": KINOPOISK_API_KEY}
    params = {
        "query": context.user_data['title'],
        "genre.name": context.user_data['genre'],
        "limit": count
    }

    response = requests.get(KINOPOISK_API_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        movies = response.json().get('docs', [])
        for movie in movies:
            # Сохранение в историю
            SearchHistory.create(
                user=User.get(User.user_id == update.effective_user.id),
                search_date=update.message.date,
                title=movie.get('name', 'Нет названия'),
                description=movie.get('description', 'Нет описания'),
                rating=movie.get('rating', {}).get('kp', 0),
                year=movie.get('year', 0),
                genre=', '.join([g['name'] for g in movie.get('genres', [])]),
                age_rating=movie.get('ageRating', 'Нет данных'),
                poster_url=movie.get('poster', {}).get('url', '')
            )
            
            # Формирование ответа
            message = (
                f"🎬 {movie.get('name', 'Нет названия')}\n"
                f"📅 Год: {movie.get('year', 'Нет данных')}\n"
                f"⭐ Рейтинг: {movie.get('rating', {}).get('kp', 'Нет данных')}\n"
                f"🎭 Жанр: {', '.join([g['name'] for g in movie.get('genres', [])])}\n"
                f"🔞 Возраст: {movie.get('ageRating', 'Нет данных')}+\n"
                f"📝 Описание: {movie.get('description', 'Нет описания')}\n"
                f"🖼 Постер: {movie.get('poster', {}).get('url', '')}"
            )
            update.message.reply_text(message)
    else:
        update.message.reply_text("Ошибка при поиске фильмов. Попробуйте позже.")

    return ConversationHandler.END

def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Ошибка обработки запроса:", exc_info=context.error)
    update.message.reply_text("Произошла ошибка. Попробуйте позже.")

def main():
    updater = Updater(TELEGRAM_TOKEN)
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
        fallbacks=[]
    )
    dispatcher.add_handler(conv_handler)
    
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

