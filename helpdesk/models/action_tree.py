# coding: utf-8

import logging

from helpdesk.libs.decorators import cached_property_with_ttl
from helpdesk.models.action import Action
from helpdesk.models.provider import get_provider
from helpdesk.config import ACTION_TREE_CONFIG
from helpdesk.models.provider.errors import ResolvePackageError, InitProviderError
from helpdesk.libs.sentry import report

logger = logging.getLogger(__name__)


class ActionTree:
    def __init__(self, tree_config, level=0):
        self.name = None
        self._nexts = []
        self.parent = None
        self.action = None
        self.is_leaf = False
        self.level = level
        self.config = tree_config

        self.build_from_config(tree_config)

    def __str__(self):
        return "ActionTree(%s, level=%s)" % (self.config, self.level)

    __repr__ = __str__

    def build_from_config(self, config):
        assert type(config) is list, "expect %s, got %s: %s" % (
            "list",
            type(config),
            config,
        )
        if not config:
            return
        self.name = config[0]
        if any(not isinstance(c, str) for c in config):
            for subconfig in config[1]:
                subtree = ActionTree(subconfig, level=self.level + 1)
                subtree.parent = self
                self._nexts.append(subtree)
        else:
            # leaf
            provider_object = config[-1]
            if provider_object.endswith("."):
                # pack
                pack_sub_tree_config = self.resolve_pack(*config)
                self.build_from_config(pack_sub_tree_config)
            else:
                # leaf action
                self.action = Action(*config)
                self.is_leaf = True

    def resolve_pack(self, *config):
        name = config[0]
        provider_object = config[-1]
        provider_type = config[-2]
        pack = provider_object[:-1]

        sub_actions = []
        actions = []

        try:
            system_provider = get_provider(provider_type)
            actions = system_provider.get_actions_info(pack=pack)
        except (InitProviderError, ResolvePackageError) as e:
            logger.error(f"Resolve pack {name} error:\n{e.tb}")
            # insert a empty children to failed action tree
            # so we can tolerant provider partially failed
            # and frontend can check children empty to notify user
            report()

        for action in actions:
            sub_actions.append(
                [action.name, action.description, provider_type, action.action_id]
            )
        return [name, sub_actions]

    @cached_property_with_ttl(300)
    def nexts(self):
        # if is pack, re-calc it
        if all(isinstance(c, str) for c in self.config):
            if self.config[-1].endswith("."):
                logger.warn("recalc %s", self)
                self._nexts = []
                pack_sub_tree_config = self.resolve_pack(*self.config)
                self.build_from_config(pack_sub_tree_config)

        return self._nexts

    @property
    def key(self):
        return "{level}-{name}".format(level=self.level, name=self.name)

    def first(self):
        if self.action:
            return self
        if not self._nexts:
            return self
        return self._nexts[0].first()

    def find(self, obj):
        if not obj:
            return None
        if self.action:
            return self if self.action.target_object == obj else None
        for sub in self._nexts:
            ret = sub.find(obj)
            if ret is not None:
                return ret

    def path_to(self, tree_node, pattern="{level}-{name}"):
        if not tree_node:
            return []
        return self.path_to(tree_node.parent, pattern) + [
            pattern.format(**tree_node.__dict__) if pattern else tree_node
        ]

    def get_tree_list(self, node_formatter):
        """
        return nested list with tree structure
        :param node_formatter: func to handle node info, node and local list will be passed as params
        :return: nested list
        """
        local_list = []

        for node in self.nexts:
            if node.is_leaf:
                local_list.append(node_formatter(node, local_list))
                continue
            children_list = node.get_tree_list(node_formatter)
            local_list.append(node_formatter(node, children_list))

        if self.parent is None:
            local_list = node_formatter(self, local_list)
        return local_list

    def get_action_by_target_obj(self, target_object):
        action_tree_leaf = (
            self.find(target_object) if target_object != "" else self.first()
        )
        if not action_tree_leaf:
            return
        return action_tree_leaf.action


action_tree = ActionTree(ACTION_TREE_CONFIG)
