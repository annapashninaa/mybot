import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = '7930707459:AAFZNX7mOmja447jbv-sARsANzRC_Jt3-Sw'
API_KEY = 'VAA2NSE-FRM4Z8G-JYP6R1Q-K754NWZ'
BASE_URL = 'https://api.kinopoisk.dev/v1.3'


#поиска фильма по названию
def search_movie(movie_name: str) -> str:
    url = f"{BASE_URL}/movies/search"
    params = {
        'token': 'VAA2NSE-FRM4Z8G-JYP6R1Q-K754NWZ',
        'name': movie_name
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        results = data.get('docs', [])
        if results:
            movie = results[0]
            title = movie.get('name')
            rating = movie.get('rating', {}).get('kp')
            return f"Название: {title}\nРейтинг: {rating}"
        else:
            return "Фильм не найден."
    else:
        return f"Произошла ошибка при обращении к API. Код ошибки: {response.status_code}"


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Здравствуйте! Я бот для поиска фильмов. Напишите название фильма, и я расскажу о нем.")



async def handle_message(update: Update, context: CallbackContext) -> None:
    movie_name = update.message.text
    response_message = search_movie(movie_name)
    await update.message.reply_text(response_message)



def main() -> None:
    updater = Updater(TELEGRAM_TOKEN)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__': 
    main()
