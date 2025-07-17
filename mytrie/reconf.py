# mytrie/reconf.py
import random

from config import VALIDATORS

from .leaf_node import LeafNode
from .branch_node import BranchNode
from .trie import Trie



def collect_leaves_by_value(node, path="", validators=None):
    if validators is None:
        validators = []

    if isinstance(node, BranchNode):
        for i in range(16):
            if node.flags[i]:
                child = node.branches[i]
                collect_leaves_by_value(child, path + f"{i:x}", validators)

    elif isinstance(node, LeafNode):
        if node.value > 0:  # Only consider validators with positive stake
            validators.append((path, node.value))  # (key, stake)

    return validators


def select_validators_by_value(trie):
    validators = collect_leaves_by_value(trie.root)

    if not validators:
        raise ValueError("No valid validators with value > 0")

    selected = []
    used_keys = set()

    for _ in range(min(VALIDATORS, len(validators))):
        total_value = sum(v for k, v in validators if k not in used_keys)
        r = random.uniform(0, total_value)
        cumulative = 0
        for k, v in validators:
            if k in used_keys:
                continue
            cumulative += v
            if r <= cumulative:
                selected.append((k, v))
                used_keys.add(k)
                break

    return selected


def reconfiguration(NUM_SHARDS, world_trie):

    selected = select_validators_by_value(world_trie)

    
    
    return 
