# coding: utf-8

import sqlalchemy
from sqlalchemy import true, and_
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


def extract_filter_from_query_params(query_params=None, model=None, exclude_keys=None):
    if not hasattr(query_params, 'items'):
        raise ValueError('query_params has no items method')
    if not model:
        raise ValueError('Model must be set')
    if exclude_keys is None:
        exclude_keys = ['page', 'pagesize', 'order_by', 'desc']
        # initialize filter by iterating keys in query_params
    filter_ = true()
    for (key, value) in query_params.items():
        if key.lower() in exclude_keys:
            continue
        try:
            if key.endswith('__icontains'):
                key = key.split('__icontains')[0]
                filter_ = and_(filter_, model.__table__.c[key].icontains(value))
            elif key.endswith('__in'):
                key = key.split('__in')[0]
                value = value.split(',')
                filter_ = and_(filter_, model.__table__.c[key].in_(value))
            else:
                filter_ = and_(filter_, model.__table__.c[key] == value)
        except KeyError:
            # ignore inexisted keys
            pass
    return filter_
