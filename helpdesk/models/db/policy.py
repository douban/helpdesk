import json
import logging
from operator import ne
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

    @property
    def node_next_dict(self):
        nodes = self.definition.get("nodes")
        if not nodes or len(nodes) == 0:
            return None
        node_next = dict()
        for node in nodes:
            node_next[node.get("name")] = node.get("next")
        for node, next in node_next.items():
            if next:
                for next_node in nodes:
                    if next == next_node.get("name"):
                        node_next[node] = next_node
        return node_next

    @property
    def init_node(self):
        nodes = self.definition.get("nodes")
        if not nodes or len(nodes) == 0:
            return None
        node_nexts = [node.get("next") for node in nodes]
        for node in nodes:
            if node.get("name") not in node_nexts:
                return node
        return None

    def next_node(self, node_name):
        link_node_dict = self.node_next_dict
        return link_node_dict.get(node_name)
        

    def is_end_node(self, node_name):
        link_node_dict = self.node_next_dict
        return link_node_dict.get(node_name) == ""

    @property
    def is_auto_approved(self):
        start_node = self.init_node
        return start_node.get("name")=="auto_approve"

    def get_node_approvers(self, node_name):
        nodes = self.definition.get("nodes")
        for node in nodes:
            if node.get("name") == node_name:
                return node.get("approvers").split(",")
        return []


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
    async def get_by_policy_id(cls, policy_id, desc=False, limit=None, offset=None):
        filter_ = cls.__table__.c.policy_id == policy_id
        return await cls.get_all(filter_=filter_, desc=desc, limit=limit, offset=offset)

    def match(self, context):
        try:
            return Rule(self.link_condition).match(context)
        except Exception:
            logger.exception('Failed to match policy: %s, context: %s', self.link_condition, context)
            return False
