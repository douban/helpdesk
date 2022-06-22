import logging
from helpdesk.models import db
from helpdesk.libs.rule import Rule

logger = logging.getLogger(__name__)


class Policy(db.Model):
    __tablename__ = 'policy'
    __table_args__ = {'mysql_charset': 'utf8mb4'}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(length=64))
    display = db.Column(db.String(length=128))
    definition = db.Column(db.JSON)

    created_by = db.Column(db.String(length=32))
    created_at = db.Column(db.DateTime)
    updated_by = db.Column(db.String(length=32))
    updated_at = db.Column(db.DateTime)


class TicketPolicy(db.Model):
    __tablename__ = 'ticket_policy'
    __table_args__ = {'mysql_charset': 'utf8mb4'}

    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer)
    ticket_name = db.Column(db.String(length=64))
    link_condition = db.Column(db.String(length=1024))

    @classmethod
    async def get_by_ticket_name(cls, ticket_name, desc=False, limit=None, offset=None):
        filter_ = cls.__table__.c.ticket_name == ticket_name
        return await cls.get_all(filter_=filter_, desc=desc, limit=limit, offset=offset)

    def match(self, context):
        try:
            return Rule(self.link_condition).match(context)
        except Exception:
            logger.exception('Failed to match policy: %s, context: %s', self.link_condition, context)
            return False
