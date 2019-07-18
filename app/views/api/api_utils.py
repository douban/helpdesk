# -*- coding: utf-8 -*-


def action_tree_dict_to_list(action_tree_d, index=0):
    """
    action tree dict data trans to list for frontend render
    :param action_tree_d: action_tree dict
    :param index: key as element id
    :return: nested list with children field
    "action_tree": [
      {
        "key": 1,
        "title": "功能导航",
        "children": [
          {
            "key": 11,
            "title": "账号相关",
            "children": [
              {
                "title": "申请服务器账号/重置密码",
                "desc": "申请 ssh 登录服务器的账号，或者重置密码",
                "url": "douban_helpdesk.apply_server",
                "name": "douban_helpdesk.apply_server",
                "key": 111
              },
              ...
            ]
          }
        ],
      }
    }
    """
    local_list = []
    is_leaf_value_func = lambda v: isinstance(v, dict) and 'url' in v
    for key, value in action_tree_d.items():
        index += 1
        if is_leaf_value_func(value):
            value['key'] = index
            local_list.append(value)
            continue

        local_list.append({
            'key': index,
            'title': key,
            'children': action_tree_dict_to_list(value, index*10)
        })
    if is_leaf_value_func(value):
        local_list.reverse()
    return local_list


def dump_action_tree_to_dict(action_tree):
    """
    dump action to a nested dict
    :param action_tree: app.models.action_tree.action_tree
    :return:
    {
        "功能导航": {
            "账号相关": {
                "申请服务器账号/重置密码": {
                    "title": "申请服务器账号/重置密码",
                    "desc": "申请 ssh 登录服务器的账号，或者重置密码",
                    "url": "douban_helpdesk.apply_server",
                    "name": "douban_helpdesk.apply_server"
                },
                ...
            },
            ...
        }
    }
    """
    result = {}

    def node_handler(node):
        if not node.is_leaf:
            return
        
        # 找到到主节点的路径
        path = []
        tmp_node = node
        while tmp_node.parent is not None:
            path.append(tmp_node.parent.name)
            tmp_node = tmp_node.parent

        # 保存节点结构到字典
        path.reverse()
        r = result
        for p in path:
            if p not in r:
                r[p] = {}
            r = r[p]
        r[node.name] = {
            'title': node.action.name,
            'desc': node.action.desc,
            'url': node.action.target_object,
            'name': node.action.target_object
        }
    dfs_action_tree(action_tree, node_handler)
    return result


def dfs_action_tree(action_tree, node_handler):
    """深度优先遍历action tree节点"""
    stack = [action_tree]
    while stack:
        node = stack.pop()
        node_handler(node)
        for sub_node in node.nexts:
            stack.append(sub_node)
