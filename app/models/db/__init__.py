# coding: utf-8

from datetime import datetime

from sqlalchemy import (Column, Integer, String, JSON,  # NOQA
                        Boolean, DateTime)  # NOQA

from sqlalchemy.ext.declarative import declarative_base

from app.libs.db import metadata, get_db
from app.libs.rest import json_unpack


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

    async def save(self):
        query = self.__table__.insert().values(**self.fields())
        return await self.execute(query)

    async def execute(self, query):
        database = await get_db()
        return await database.execute(query)

    def fields(self):
        return {k: getattr(self, k) for k in self.__table__.columns.keys()}

    def to_dict(self, show=None, **kw):
        # return json_unpack(self)
        return json_unpack(self.fields())

    def from_dict(self, **kw):
        pass
