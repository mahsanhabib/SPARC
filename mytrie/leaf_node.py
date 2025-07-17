# mytrie/leaf_node.py

class LeafNode:
    def __init__(self, key, value, epoch):
        self.node_type = "leaf"
        self.key = key
        self.value = value
        self.epoch = epoch

    def __repr__(self):
        return f"LeafNode(key={self.key:x}, value={self.value}, epoch={self.epoch})"