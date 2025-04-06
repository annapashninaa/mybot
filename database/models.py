from peewee import *
from config import DATABASE_NAME

db = SqliteDatabase(DATABASE_NAME)

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    user_id = IntegerField(unique=True)
    username = CharField(null=True)

class SearchHistory(BaseModel):
    user = ForeignKeyField(User, backref='searches')
    search_date = DateTimeField()
    title = CharField()
    description = TextField()
    rating = FloatField()
    year = IntegerField()
    genre = CharField()
    age_rating = CharField()
    poster_url = CharField()

db.connect()
db.create_tables([User, SearchHistory], safe=True)
