import logging
from helpdesk.models import db
from helpdesk.libs.rule import Rule
from sqlalchemy.sql.expression import and_

from helpdesk.config import ADMIN_POLICY
from helpdesk.views.api.schemas import NodeType
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
    async def get_by_ticket_name(cls, ticket_name, without_default=False, desc=False, limit=None, offset=None):
        filter_ = cls.__table__.c.ticket_name == ticket_name
        if without_default:
            without_filter_ = cls.__table__.c.policy_id != ADMIN_POLICY
            filter_ = and_(filter_, without_filter_)
        return await cls.get_all(filter_=filter_, desc=desc, limit=limit, offset=offset)

    @classmethod
    async def get_special_associate(cls, ticket_name, policy_id):
        filter_name = cls.__table__.c.ticket_name == ticket_name
        filter_policy = cls.__table__.c.policy_id == policy_id
        return await cls.get_all(filter_=and_(filter_name, filter_policy))

    @classmethod
    async def default_associate(cls, ticket_name):
        policy_id = ADMIN_POLICY
        exist_default = await cls.get_special_associate(ticket_name=ticket_name, policy_id=policy_id)
        if exist_default:
            return policy_id
        ticket_policy_form = TicketPolicy(
            policy_id=policy_id,
            ticket_name=ticket_name,
            link_condition="[\"=\", 1, 1]"
        )
        ticket_policy_id = await ticket_policy_form.save()
        ticket_policy = await TicketPolicy.get(ticket_policy_id)
        if not ticket_policy:
            logger.exception('Failed to associate default approval flow, ticket: %s', ticket_name)
        return policy_id

    @classmethod
    async def get_by_policy_id(cls, policy_id, desc=False, limit=None, offset=None):
        filter_ = cls.__table__.c.policy_id == policy_id
        return await cls.get_all(filter_=filter_, desc=desc, limit=limit, offset=offset)

    def match(self, context):
        try:
            return Rule(self.link_condition).match(context)
        except Exception:
            logger.exception('Failed to match policy: %s, context: %s', self.link_condition, context)
            return False


class GroupUser(db.Model):
    __tablename__ = 'group_user'
    __table_args__ = {'mysql_charset': 'utf8mb4'}

    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(length=64))
    user_str = db.Column(db.String(length=128))

    @classmethod
    async def get_by_group_name(cls, group_name, desc=False, limit=None, offset=None):
        filter_ = cls.__table__.c.group_name == group_name
        return await cls.get_all(filter_=filter_, desc=desc, limit=limit, offset=offset)
