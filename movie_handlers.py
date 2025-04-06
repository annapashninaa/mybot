from telegram import Update
from telegram.ext import CallbackContext
import requests
from config import TMDB_API_KEY
from database.models import SearchHistory

def process_title(update: Update, context: CallbackContext) -> int:
    context.user_data['title'] = update.message.text
    update.message.reply_text("Введите жанр (например, комедия):")
    return GENRE

def process_genre(update: Update, context: CallbackContext) -> int:
    context.user_data['genre'] = update.message.text
    update.message.reply_text("Сколько результатов показать? (1-10)")
    return COUNT

def process_count(update: Update, context: CallbackContext) -> int:
    # Реализация поиска через TMDB API
    params = {
        'api_key': TMDB_API_KEY,
        'query': context.user_data['title'],
        'language': 'ru-RU'
    }
    response = requests.get('https://api.themoviedb.org/3/search/movie', params=params)
    
    # Обработка результатов и сохранение в БД
    return ConversationHandler.END
