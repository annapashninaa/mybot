import logging
from datetime import datetime

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext, ConversationHandler
)

from config import KINOPOISK_API_KEY
from database.models import User, SearchHistory

logger = logging.getLogger(__name__)

def process_count(update: Update, context: CallbackContext) -> int:
    try:
        count = int(update.message.text)
        if not 1 <= count <= 10:
            raise ValueError
    except ValueError:
        update.message.reply_text("❌ Некорректное число! Введите от 1 до 10.")
        return ConversationHandler.END

    headers = {"X-API-KEY": KINOPOISK_API_KEY}
    params = {
        "name": context.user_data['title'],
        "genres.name": context.user_data['genre'],
        "limit": count,
        "selectFields": ["name", "description", "rating", "year", "genres", "ageRating", "poster"]
    }

    try:
        response = requests.get(context.bot_data['KINOPOISK_API_URL'], headers=headers, params=params)
        response.raise_for_status()

        movies = response.json().get('docs', [])
        if not movies:
            update.message.reply_text("😞 Ничего не найдено!")
            return ConversationHandler.END

        for i, movie in enumerate(movies):
            keyboard = [[
                InlineKeyboardButton("Отметить просмотренным", callback_data=f"watched_{movie['id']}"),
                InlineKeyboardButton("Следующий", callback_data=f"next_{i + 1}")
            ]]

            update.message.reply_photo(
                photo=movie.get('poster', {}).get('url'),
                caption=f"🎬 <b>{movie.get('name', 'Без названия')}</b>\n"
                        f"⭐ Рейтинг: {movie.get('rating', {}).get('kp', 'N/A')}\n"
                        f"📅 Год: {movie.get('year', 'N/A')}\n"
                        f"🎭 Жанры: {', '.join([g['name'] for g in movie.get('genres', [])])}\n"
                        f"🔞 Возраст: {movie.get('ageRating', '0+')}+\n"
                        f"📖 Описание: {movie.get('description', 'Нет описания')}",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

            user = User.get(User.user_id == update.effective_user.id)
            SearchHistory.create(
                user=user,
                search_date=datetime.now(),
                title=movie.get('name', 'Без названия'),
                description=movie.get('description', 'Нет описания'),
                rating=movie.get('rating', {}).get('kp', 0),
                year=movie.get('year', 0),
                genre=', '.join([g['name'] for g in movie.get('genres', [])]),
                age_rating=movie.get('ageRating', '0+'),
                poster_url=movie.get('poster', {}).get('url', '')
            )

            break

    except requests.exceptions.RequestException as e:
        logger.error(f"API error: {e}")
        update.message.reply_text("⚠️ Произошла ошибка при поиске!")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        update.message.reply_text("❌ Произошла ошибка. Повторите запрос позже.")

    return ConversationHandler.END


