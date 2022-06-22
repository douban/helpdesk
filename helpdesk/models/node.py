# coding: utf-8

import logging
from datetime import datetime
from time import sleep
from helpdesk.libs.rest import DictSerializableClassMixin

logger = logging.getLogger(__name__)


class Node(DictSerializableClassMixin):
    """
    flow node
    """
    def __init__(self, id, name, desc, approvers, is_auto_approved, rule, pre, next):
        self.id = id
        self.name = name
        self.desc = desc
        self.approvers = approvers
        self.is_auto_approved = is_auto_approved
        self.rule = rule
        self.pre = pre
        self.next = next
    
        
    def __repr__(self):
        return 'Node(%s, %s, %s, %s, %s, %s, %s, %s)' % (self.id, self.name, self.desc, self.approvers, self.is_auto_approved, self.rule, self.pre, self.next)

    __str__ = __repr__

    async def get():
        pass

