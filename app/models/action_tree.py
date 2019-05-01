# coding: utf-8

from app.models.action import Action

from app.config import ACTION_TREE_CONFIG


class ActionTree:
    def __init__(self, tree_config):
        self.name = None
        self.nexts = []
        self.parent = None
        self.action = None
        self.is_leaf = False

        self.build_from_config(tree_config)

    # TODO: resolve pack
    def build_from_config(self, config):
        assert type(config) is list
        if not config:
            return
        self.name = config[0]
        if any(not isinstance(c, str) for c in config):
            for subconfig in config[1]:
                subtree = ActionTree(subconfig)
                subtree.parent = self
                self.nexts.append(subtree)
        else:
            # leaf
            self.action = Action(*config)
            self.is_leaf = True

    def first(self):
        if self.action:
            return self
        if not self.nexts:
            return self
        return self.nexts[0].first()

    # TODO: resolve action
    def find(self, obj):
        if not obj:
            return None
        if self.action:
            return self if self.action.target_object == obj else None
        for sub in self.nexts:
            ret = sub.find(obj)
            if ret is not None:
                return ret


action_tree = ActionTree(ACTION_TREE_CONFIG)
