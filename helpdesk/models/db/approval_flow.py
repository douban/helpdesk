import logging
from helpdesk.models import db

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

policys = [
    Policy(id=1, name="test", display="test", definition="", created_by="qxy", created_at="", updated_at="", updated_by="")
    # ...
]


class TicketFlow(db.Model):
    __tablename__ = 'ticket_flow'
    __table_args__ = {'mysql_charset': 'utf8mb4'}

    id = db.Column(db.Integer, primary_key=True)
    policy_id = db.Column(db.Integer)
    ticket_name = db.Column(db.String(length=64))