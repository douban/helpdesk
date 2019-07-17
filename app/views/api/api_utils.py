def action_tree_dict_to_list(action_tree_d, index=0):
    """
    action tree dict data trans to list for frontend render
    :param action_tree_d: action_tree dict
    :return:
    """
    local_list = []
    for key, value in action_tree_d.items():
        index += 1
        if isinstance(value, dict) and 'url' in value:
            value['key'] = index
            local_list.append(value)
            continue

        local_list.append({
            'key': index,
            'title': key,
            'children': action_tree_dict_to_list(value, index*10)
        })
    return local_list
