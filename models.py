import datetime
import logging
from peewee import *

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Создаём подключение к базе данных SQLite
db = SqliteDatabase('app.db')

class BaseModel(Model):
    class Meta:
        database = db

class SearchHistory(BaseModel):
    user_id = IntegerField()
    query = CharField()
    result = TextField()
    date = DateTimeField(default=datetime.datetime.now)

class UserFavorite(BaseModel):
    chat_id = IntegerField()
    title = CharField()
    url = TextField()
    player_url = TextField()

    class Meta:
        primary_key = False
        indexes = (
            (('chat_id', 'title'), True),
        )

def init_db():
    db.connect()
    db.create_tables([SearchHistory, UserFavorite], safe=True)

def add_history(user_id: int, query: str, result: str):
    SearchHistory.create(user_id=user_id, query=query, result=result)

def get_history(user_id: int):
    query = (
        SearchHistory
        .select()
        .where(SearchHistory.user_id == user_id)
        .order_by(SearchHistory.date.desc())
    )
    return [
        {
            "date": record.date.strftime("%Y-%m-%d %H:%M:%S"),
            "query": record.query,
            "result": record.result
        }
        for record in query
    ]

def add_favorite(chat_id: int, title: str, url: str, player_url: str):
    try:
        UserFavorite.insert(chat_id=chat_id, title=title, url=url, player_url=player_url) \
            .on_conflict_replace().execute()
    except Exception as e:
        logger.error(f"Error adding favorite: {e}")

def get_favorites(chat_id: int):
    query = UserFavorite.select().where(UserFavorite.chat_id == chat_id)
    return list(query.dicts())
