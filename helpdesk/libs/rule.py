# coding: utf-8

from rule import Rule  # NOQA
from rule.op import Op, register


@register(aliases=["allin"])
class OnlyContains(Op):
    def calc(self, context, var, *args):
        return all(i in args for i in var)
