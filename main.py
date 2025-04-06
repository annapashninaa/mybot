import logging
from datetime import datetime

import requests
from peewee import fn
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler,  filters as Filters,
    CallbackContext, ConversationHandler, CallbackQueryHandler
)


from config import TELEGRAM_TOKEN, KINOPOISK_API_KEY
from database.models import User, SearchHistory

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
TITLE, GENRE, COUNT, BUDGET_TYPE, DATE_SELECT = range(5)
KINOPOISK_API_URL = "https://api.kinopoisk.dev/v1.3/movie"


def start(update: Update, context: CallbackContext) -> None:
    user, created = User.get_or_create(
        user_id=update.effective_user.id,
        defaults={'username': update.effective_user.username}
    )
    update.message.reply_text(
        f"🎬 Привет, {update.effective_user.first_name}!\n"
        "Я помогу найти фильмы по твоим запросам.\n"
        "Доступные команды:\n"
        "/movie_search - Поиск фильма\n"
        "/movie_by_rating - Фильмы по рейтингу\n"
        "/low_budget_movie - Низкобюджетные фильмы\n"
        "/high_budget_movie - Высокобюджетные фильмы\n"
        "/history - История поиска"
    )


# Функции для обработки movie_search (поиск по названию)
def movie_search(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("📝 Введите название фильма:")
    return TITLE


def process_title(update: Update, context: CallbackContext) -> int:
    context.user_data['title'] = update.message.text
    update.message.reply_text("🎭 Введите жанр (например, комедия):")
    return GENRE


def process_genre(update: Update, context: CallbackContext) -> int:
    context.user_data['genre'] = update.message.text.lower()
    update.message.reply_text("🔢 Сколько результатов показать? (1-10)")
    return COUNT


def process_count(update: Update, context: CallbackContext) -> int:
    try:
        count = int(update.message.text)
        if not 1 <= count <= 10:
            raise ValueError
    except ValueError:
        update.message.reply_text("❌ Некорректное число! Введите от 1 до 10.")
        return COUNT

    headers = {"X-API-KEY": KINOPOISK_API_KEY}
    params = {
        "name": context.user_data['title'],
        "genres.name": context.user_data['genre'],
        "limit": count,
        "selectFields": ["name", "description", "rating", "year", "genres", "ageRating", "poster"]
    }

    try:
        response = requests.get(KINOPOISK_API_URL, headers=headers, params=params)
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

            SearchHistory.create(
                user=User.get(User.user_id == update.effective_user.id),
                search_date=datetime.now(),
                title=movie.get('name', 'Без названия'),
                description=movie.get('description', 'Нет описания'),
                rating=movie.get('rating', {}).get('kp', 0),
                year=movie.get('year', 0),
                genre=', '.join([g['name'] for g in movie.get('genres', [])]),
                age_rating=movie.get('ageRating', '0+'),
                poster_url=movie.get('poster', {}).get('url', '')
            )
            break  # Показываем только первый результат для пагинации

    except requests.exceptions.HTTPError as e:
        logger.error(f"API error: {e}")
        update.message.reply_text("⚠️ Произошла ошибка при поиске!")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        update.message.reply_text("❌ Произошла ошибка. Повторите запрос позже.")

    return ConversationHandler.END


def low_budget_movie(update: Update, context: CallbackContext) -> None:
    context.user_data['budget_type'] = 'low'
    search_movies_by_budget(update, context)


def high_budget_movie(update: Update, context: CallbackContext) -> None:
    context.user_data['budget_type'] = 'high'
    search_movies_by_budget(update, context)


def search_movies_by_budget(update: Update, context: CallbackContext):
    headers = {"X-API-KEY": KINOPOISK_API_KEY}
    params = {
        "limit": 5,
        "sortField": "budget.value",
        "sortType": "1" if context.user_data.get('budget_type') == 'low' else "-1",
        "selectFields": ["name", "description", "rating", "year", "genres", "ageRating", "poster", "budget"]
    }

    try:
        response = requests.get(KINOPOISK_API_URL, headers=headers, params=params)
        response.raise_for_status()

        movies = response.json().get('docs', [])
        if not movies:
            update.message.reply_text("😞 Ничего не найдено!")
            return

        for movie in movies:
            budget_value = movie.get('budget', {}).get('value', 'N/A')
            budget_currency = movie.get('budget', {}).get('currency', '')

            message = (
                f"🎬 <b>{movie.get('name', 'Без названия')}</b>\n"
                f"💰 Бюджет: {budget_value} {budget_currency}\n"
                f"⭐ Рейтинг: {movie.get('rating', {}).get('kp', 'N/A')}\n"
                f"📅 Год: {movie.get('year', 'N/A')}\n"
                f"🎭 Жанры: {', '.join([g['name'] for g in movie.get('genres', [])])}\n"
                f"🔞 Возраст: {movie.get('ageRating', '0+')}+\n"
                f"📖 Описание: {movie.get('description', 'Нет описания')}"
            )

            update.message.reply_photo(
                photo=movie.get('poster', {}).get('url'),
                caption=message,
                parse_mode='HTML'
            )
    except requests.exceptions.HTTPError as e:
        logger.error(f"API error: {e}")
        update.message.reply_text("⚠️ Произошла ошибка при поиске!")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        update.message.reply_text("❌ Произошла ошибка. Повторите запрос позже.")


def history(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("📅 Введите дату для просмотра истории в формате ГГГГ-ММ-ДД:")
    return DATE_SELECT


def process_date(update: Update, context: CallbackContext) -> int:
    try:
        selected_date = datetime.strptime(update.message.text, '%Y-%m-%d').date()
    except ValueError:
        update.message.reply_text("❌ Некорректный формат даты. Используйте ГГГГ-ММ-ДД.")
        return ConversationHandler.END

    user = User.get(User.user_id == update.effective_user.id)
    history_entries = SearchHistory.select().where(
        (SearchHistory.user == user) & (fn.DATE(SearchHistory.search_date) == selected_date)
    ).limit(10)

    if not history_entries:
        update.message.reply_text("📂 История поиска за эту дату пуста!")
        return ConversationHandler.END

    for entry in history_entries:
        update.message.reply_photo(
            photo=entry.poster_url,
            caption=f"📅 {entry.search_date.strftime('%d.%m.%Y %H:%M')}\n"
                    f"🎬 {entry.title}\n"
                    f"⭐ Рейтинг: {entry.rating}\n"
                    f"📅 Год: {entry.year}\n"
                    f"🎭 Жанры: {entry.genre}",
            parse_mode='HTML'
        )

    return ConversationHandler.END


def handle_callback_query(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data.startswith("watched_"):
        movie_id = query.data.split("_")[1]
        user = User.get(User.user_id == query.effective_user.id)
        try:
            movie = SearchHistory.get(
                (SearchHistory.user == user) & (SearchHistory.title == movie_id)
            )
            movie.watched = True
            movie.save()
            query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ Просмотрено!")
        except SearchHistory.DoesNotExist:
            logger.warning(f"Movie with ID {movie_id} not found in history for user {user.user_id}")
            query.edit_message_text("Фильм не найден в истории.")
    elif query.data.startswith("next_"):
        index = int(query.data.split("_")[1])
        # Здесь можно реализовать логику показа следующего результата из context.user_data
        query.edit_message_text(f"Показан результат {index}.")  # Заглушка


def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Ошибка:", exc_info=context.error)
    update.message.reply_text("❌ Произошла ошибка. Повторите запрос позже.")


def main():
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    # Обработчики для movie_search
    search_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('movie_search', movie_search)],
        states={
            TITLE: [MessageHandler(Filters.text & ~Filters.command, process_title)],
            GENRE: [MessageHandler(Filters.text & ~Filters.command, process_genre)],
            COUNT: [MessageHandler(Filters.text & ~Filters.command, process_count)]
        },
        fallbacks=[]
    )
    dispatcher.add_handler(search_conv_handler)

    # Обработчики для history
    history_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('history', history)],
        states={
            DATE_SELECT: [MessageHandler(Filters.text & ~Filters.command, process_date)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]  # Добавлен обработчик cancel
    )
    dispatcher.add_handler(history_conv_handler)

    # Обработчики для budget
    dispatcher.add_handler(CommandHandler("low_budget_movie", low_budget_movie))
    dispatcher.add_handler(CommandHandler("high_budget_movie", high_budget_movie))

    # Обработчик для callback-запросов
    dispatcher.add_handler(CallbackQueryHandler(handle_callback_query))

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Действие отменено.")
    return ConversationHandler.END


if __name__ == '__main__':
    main()

