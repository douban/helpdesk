import logging
from helpdesk.models import db
from helpdesk.libs.rule import Rule

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

    @property
    def init_node(self):
        nodes = self.definition.get("nodes")
        if not nodes or len(nodes) == 0:
            return None
        return nodes[0]

    def next_node(self, node_name):
        nodes = self.definition.get("nodes")
        for index, node in enumerate(nodes):
            if node.get("name") == node_name:
                return nodes[index+1] if (index != len(nodes)-1) else None
        

    def is_end_node(self, node_name):
        nodes = self.definition.get("nodes")
        for index, node in enumerate(nodes):
            if node.get("name") == node_name:
                return index == len(nodes)-1

    def is_auto_approved(self):
        return len(self.definition.get("nodes")) == 1 and self.init_node.get("node_type")  == NodeType.CC.value

    def is_cc_node(self, node_name):
        for node in self.definition.get("nodes"):
            if node.get("name") == node_name and node.get("node_type") == NodeType.CC.value:
                return True
        return False

    def get_node_approvers(self, node_name):
        nodes = self.definition.get("nodes")
        for node in nodes:
            if node.get("name") == node_name:
                return node.get("approvers")
        return ""


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

    @classmethod
    async def default_associate(cls, ticket_name):
        policy_id = ADMIN_POLICY
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
