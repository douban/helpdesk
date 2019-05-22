# coding: utf-8

import logging
from datetime import datetime

from app.models import db
from app.models.provider import get_provider
from app.config import SYSTEM_USER

logger = logging.getLogger(__name__)


class Ticket(db.Model):
    __tablename__ = 'ticket'

    id = db.Column(db.Integer, primary_key=True)
    provider_type = db.Column(db.String(length=16))
    provider_object = db.Column(db.String(length=64))
    params = db.Column(db.JSON)
    extra_params = db.Column(db.JSON)
    submitter = db.Column(db.String(length=32))
    reason = db.Column(db.String(length=128))

    # is_approved default is None, it will become True when approved,
    #   become False when rejected
    is_approved = db.Column(db.Boolean)
    confirmed_by = db.Column(db.String(length=32))

    annotation = db.Column(db.JSON)
    created_at = db.Column(db.DateTime)
    confirmed_at = db.Column(db.DateTime)
    executed_at = db.Column(db.DateTime)

    def approve(self, by_user=None, auto=False):
        if auto:
            if not self.annotation:
                self.annotation = {}
            self.annotation['auto_approved'] = True
            self.confirmed_by = SYSTEM_USER
        else:
            self.confirmed_by = by_user

        self.is_approved = True
        self.confirmed_at = datetime.now()

    def reject(self, by_user):
        self.confirmed_by = by_user
        self.is_approved = False
        self.confirmed_at = datetime.now()

    # TODO: open a new view to get ticket, approve and execute it
    def execute(self):
        system_provider = get_provider(self.provider_type)
        token, msg = system_provider.authenticate(self.submitter)
        logger.debug('get token: %s, msg: %s', token, msg)

        provider = get_provider(self.provider_type, token=token, user=self.submitter)

        logger.info('run action %s, params: %s', self.provider_object, self.params)
        execution, msg = provider.run_action(self.provider_object, self.params)
        if not execution:
            return execution, msg
        return execution, 'Success. <a href="%s" target="_blank">result</a>' % (execution['web_url'],)
