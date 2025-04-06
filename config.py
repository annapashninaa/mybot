import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_KEY = os.getenv("KINOSEARCH_API_KEY")
DATABASE_NAME = "movie_search.db"
