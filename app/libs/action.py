# -*- coding: utf-8 -*-

from starlette.authentication import has_required_scope

from app.config import NO_AUTH_TARGET_OBJECTS, PROVIDER
from app.models.provider import get_provider


def get_action_by_target_obj(action_tree, target_object):
    """
    :param action_tree: app.models.action_tree.action_tree
    :param target_object: str | st2 pack.action
    :return: app.models.action.Action obj
    """
    action_tree_leaf = action_tree.find(target_object) if target_object != '' else action_tree.first()
    if not action_tree_leaf:
        return
    return action_tree_leaf.action


def get_provider_by_action(request, action):
    if not has_required_scope(request, ['authenticated']):
        return get_provider(PROVIDER) if action.target_object in NO_AUTH_TARGET_OBJECTS else None
    return request.user.provider
