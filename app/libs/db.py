# coding: utf-8

import sqlalchemy
from databases import Database

from app.config import DATABASE_URL


name_convention = {
  "ix": 'idx_%(column_0_label)s',
  "uq": "uk_%(table_name)s_%(column_0_name)s",
  "ck": "ck_%(table_name)s_%(column_0_name)s",
  "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
  "pk": "pk_%(table_name)s"
}

engine = sqlalchemy.create_engine(DATABASE_URL, convert_unicode=True)
metadata = sqlalchemy.MetaData(naming_convention=name_convention)

_database = None


async def get_db():
    # see https://www.starlette.io/database/#queries
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


def get_sync_conn():
    # see https://docs.sqlalchemy.org/en/13/core/tutorial.html#executing
    return engine.connect()


def init_db():
    from sqlalchemy_utils import database_exists, create_database
    if not database_exists(DATABASE_URL):
        create_database(DATABASE_URL)

    metadata.create_all(bind=engine)
