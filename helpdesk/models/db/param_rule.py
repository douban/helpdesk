# coding: utf-8

import logging

from helpdesk.libs.rule import Rule
from helpdesk.models import db

logger = logging.getLogger(__name__)


class ParamRule(db.Model):
    __tablename__ = "param_rule"
    __table_args__ = {"mysql_charset": "utf8mb4"}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(length=64))

    # context
    provider_object = db.Column(db.String(length=64), index=True)

    # rule string
    rule = db.Column(db.String(length=1024))

    # action
    is_auto_approval = db.Column(db.Boolean)
    approver = db.Column(db.String(length=128))

    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    @classmethod
    async def get_all_by_provider_object(
        cls, provider_object, desc=False, limit=None, offset=None
    ):
        filter_ = cls.__table__.c.provider_object == provider_object
        return await cls.get_all(filter_=filter_, desc=desc, limit=limit, offset=offset)

    def match(self, context):
        try:
            return Rule(self.rule).match(context)
        except Exception:
            logger.exception(
                "Failed to match ParamRule: %s, context: %s", self.rule, context
            )
            return False
