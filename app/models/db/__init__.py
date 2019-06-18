# coding: utf-8

import logging
from datetime import datetime

from sqlalchemy import (Column, Integer, String, JSON,  # NOQA
                        Boolean, DateTime)  # NOQA
from sqlalchemy.sql import select, func
from sqlalchemy.ext.declarative import declarative_base

from app.libs.db import metadata, get_db
from app.libs.rest import json_unpack, DictSerializableClassMixin

logger = logging.getLogger(__name__)

Base = declarative_base(metadata=metadata)


class Model(DictSerializableClassMixin, Base):
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
        if id_ is None:
            return None
        t = cls.__table__
        query = select([t]).where(t.c.id == id_)
        rs = await cls._fetchall(query)
        return cls(**rs[0]) if rs else None

    @classmethod
    async def get_all(cls, ids=None, filter_=None, desc=False, limit=None, offset=None):
        # logger.debug('%s.get_all(ids=%s, filter_=%s, desc=%s, limit=%s, offset=%s', cls.__name__, ids, filter_, desc, limit, offset)
        t = cls.__table__
        query = select([t])
        if ids:
            # see https://docs.sqlalchemy.org/en/13/core/sqlelement.html?highlight=in_#sqlalchemy.sql.expression.ColumnElement.in_
            query = query.where(t.c.id.in_(ids))
        elif filter_ is not None:
            query = query.where(filter_)
        if desc:
            query = query.order_by(t.c.id.desc())
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        rs = await cls._fetchall(query)
        return [cls(**r) for r in rs] if rs else []

    @classmethod
    async def count(cls, filter_=None):
        query = select([func.count()]).select_from(cls.__table__)
        if filter_ is not None:
            query = query.where(filter_)
        rs = await cls._fetchall(query)
        return rs[0][0] if rs and rs[0] else None

    async def save(self):
        kw = self._fields()
        obj = await self.get(self.id)
        logger.debug('Saving %s, checking if obj exists: %s', self, obj)
        if obj:
            if 'updated_at' in kw:
                kw['updated_at'] = datetime.now()
            return await self.update(**kw)

        if 'created_at' in kw and kw['created_at'] is None:
            kw['created_at'] = datetime.now()
        query = self.__table__.insert().values(**kw)
        id_ = await self._execute(query)
        self.id = id_
        return id_

    async def update(self, **kw):
        '''try to return last modified row id
        see also https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor.lastrowid
        '''
        t = self.__table__
        kw.pop('id', None)
        query = t.update().where(t.c.id == self.id).values(**kw)
        return await self._execute(query) or self.id

    @classmethod
    async def delete(cls, id_):
        if id_ is None:
            return None
        t = cls.__table__
        query = t.delete().where(t.c.id == id_)
        return await cls._execute(query) or id_

    @classmethod
    async def delete_all(cls, ids=None, filter_=None):
        t = cls.__table__
        query = t.delete()
        if ids:
            # see https://docs.sqlalchemy.org/en/13/core/sqlelement.html?highlight=in_#sqlalchemy.sql.expression.ColumnElement.in_
            query = query.where(t.c.id.in_(ids))
        elif filter_ is not None:
            query = query.where(filter_)
        return await cls._execute(query)

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
        if show:
            d = self
        else:
            d = self._fields()
        d = json_unpack(d)
        d['_class'] = self.__class__.__name__
        return d

    def from_dict(self, **kw):
        pass
