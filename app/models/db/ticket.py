# coding: utf-8

import logging
from datetime import datetime

from app.models import db
from app.models.provider import get_provider
from app.config import SYSTEM_USER, ST2_EXECUTION_RESULT_URL_PATTERN

logger = logging.getLogger(__name__)


class Ticket(db.Model):
    __tablename__ = 'ticket'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(length=64))
    provider_type = db.Column(db.String(length=16))
    provider_object = db.Column(db.String(length=64))
    params = db.Column(db.JSON)
    extra_params = db.Column(db.JSON)
    submitter = db.Column(db.String(length=32), index=True)
    cc = db.Column(db.String(length=64))
    reason = db.Column(db.String(length=128))

    # is_approved default is None, it will become True when approved,
    #   become False when rejected
    is_approved = db.Column(db.Boolean)
    confirmed_by = db.Column(db.String(length=32))
    confirmed_at = db.Column(db.DateTime)

    # TODO: if this provider_object is bound to an approver rule
    #   then do the rule and store the state to the annotation

    annotation = db.Column(db.JSON)
    created_at = db.Column(db.DateTime)
    executed_at = db.Column(db.DateTime)

    @classmethod
    def get_all_by_submitter(cls, submitter, desc=False, limit=None, offset=None):
        filter_ = cls.__table__.c.submitter == submitter
        return cls.get_all(filter_=filter_, desc=desc, limit=limit, offset=offset)

    @property
    def ccs(self):
        return self.cc.split(',') if self.cc else []

    def can_view(self, user):
        return user.is_admin or user.name == self.submitter or user.name in self.ccs

    def annotate(self, dict_=None, **kw):
        d = dict_ or {}
        d.update(kw)
        self.annotation = self.annotation or {}
        self.annotation.update(d)

    @property
    def is_confirmed(self):
        return self.confirmed_by or self.is_approved is not None

    @property
    def execution_result_url(self):
        if not self.annotation:
            return None
        return self.annotation.get('execution', {}).get('result_url')

    def check_confirmed(self):
        if self.is_confirmed:
            op = 'approved' if self.is_approved else 'rejected'
            msg = 'already %s by %s' % (op, self.confirmed_by)
            return True, msg
        return False, 'not confirmed yet'

    def approve(self, by_user=None, auto=False):
        is_confirmed, msg = self.check_confirmed()
        if is_confirmed:
            return False, msg

        if auto:
            self.annotate(auto_approved=True)
            self.confirmed_by = SYSTEM_USER
        else:
            self.confirmed_by = by_user

        self.is_approved = True
        self.confirmed_at = datetime.now()
        return True, 'Success'

    def reject(self, by_user):
        is_confirmed, msg = self.check_confirmed()
        if is_confirmed:
            return False, msg

        self.confirmed_by = by_user
        self.is_approved = False
        self.confirmed_at = datetime.now()
        return True, 'Success'

    def execute(self, provider=None, is_admin=False):
        system_provider = get_provider(self.provider_type)

        logger.info('run action %s, params: %s', self.provider_object, self.params)
        # admin use self provider, otherwise use system_provider
        if is_admin:
            if not provider:
                token, msg = system_provider.authenticate(self.submitter)
                logger.debug('get token: %s, msg: %s', token, msg)
                token = token['token']
                provider = get_provider(self.provider_type, token=token, user=self.submitter)
            execution, msg = provider.run_action(self.provider_object, self.params)
        else:
            execution, msg = system_provider.run_action(self.provider_object, self.params)
        if not execution:
            return execution, msg

        self.executed_at = datetime.now()
        self.annotate(execution=dict(id=execution['id'], result_url=ST2_EXECUTION_RESULT_URL_PATTERN.format(execution_id=execution['id'])))

        # we don't save the ticket here, we leave it outside
        return execution, 'Success. <a href="%s" target="_blank">result</a>' % (execution['web_url'],)
