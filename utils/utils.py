# utils/utils.py

import json

def get_group_set(json_path, index=0):
    with open(json_path, 'r') as f:
        data = json.load(f)
        keys = list(data.keys())
        
        if index >= len(keys):
            raise ValueError(f"Group index {index} out of range")

        key = keys[index]
        values = data[key]

        group_set = {key} | set(map(str, values))  # Convert all to strings
        return group_set
    
def build_node_to_group_index(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)

    node_to_group = {}
    for i, (key, values) in enumerate(data.items()):
        node_to_group[str(key)] = i
        for v in values:
            node_to_group[str(v)] = i

    return node_to_group