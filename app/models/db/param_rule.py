# coding: utf-8

import logging

from app.models import db

logger = logging.getLogger(__name__)


class ParamRule(db.Model):
    __tablename__ = 'param_rule'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(length=64))

    # context
    provider_object = db.Column(db.String(length=64), index=True)

    # rule string
    rule = db.Column(db.JSON)

    # action
    is_auto_approval = db.Column(db.Boolean)
    approver = db.Column(db.String(length=128))

    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    @classmethod
    async def get_all_by_provider_object(cls, provider_object, desc=False, limit=None, offset=None):
        filter_ = cls.__table__.c.provider_object == provider_object
        return await cls.get_all(filter_=filter_, desc=desc, limit=limit, offset=offset)

    def match(self, context):
        # TODO:
        return True
