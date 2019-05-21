# coding: utf-8

import sqlalchemy
from databases import Database

from app.config import DATABASE_URL

metadata = sqlalchemy.MetaData()

_database = None


async def get_db():
    global _database
    if not _database:
        _database = Database(DATABASE_URL)
        # Establish the connection pool
        await _database.connect()
    return _database


async def close_db():
    global _database
    # Close all connection in the connection pool
    await _database.disconnect()
    _database = None


def init_db():
    from sqlalchemy_utils import database_exists, create_database
    if not database_exists(DATABASE_URL):
        create_database(DATABASE_URL)

    engine = sqlalchemy.create_engine(DATABASE_URL, convert_unicode=True)
    metadata.create_all(bind=engine)
