# coding: utf-8

import logging
from datetime import datetime

from sqlalchemy import (Column, Integer, String, JSON,  # NOQA
                        Boolean, DateTime)  # NOQA
from sqlalchemy.sql import select
from sqlalchemy.ext.declarative import declarative_base

from app.libs.db import metadata, get_db
from app.libs.rest import json_unpack

logger = logging.getLogger(__name__)

Base = declarative_base(metadata=metadata)


class Model(Base):
    __abstract__ = True

    def __str__(self):
        attrs = []
        for k in sorted(self.__table__.columns.keys()):
            v = getattr(self, k)
            v = '"%s"' % str(v) if type(v) in (str, datetime) else str(v)
            attrs.append('%s=%s' % (k, v))
        return '%s(%s)' % (self.__class__.__name__, ', '.join(attrs))

    __repr__ = __str__

    @classmethod
    async def get(cls, id_):
        t = cls.__table__
        query = select([t]).where(t.c.id == id_)
        rs = await cls._fetchall(query)
        return cls(**rs[0]) if rs else None

    async def save(self):
        query = self.__table__.insert().values(**self._fields())
        return await self._execute(query)

    @classmethod
    async def _execute(cls, query):
        database = await get_db()
        return await database.execute(query)

    @classmethod
    async def _fetchall(cls, query):
        database = await get_db()
        return await database.fetch_all(query)

    def _fields(self):
        return {k: getattr(self, k) for k in self.__table__.columns.keys()}

    def to_dict(self, show=None, **kw):
        d = self._fields()
        d['_class'] = self.__class__.__name__
        return json_unpack(d)
        # return json_unpack(self)

    def from_dict(self, **kw):
        pass
