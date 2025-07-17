# mytrie/branch_node.py

class BranchNode:
    def __init__(self, epoch):
        self.node_type = "branch"
        self.branches = [None] * 16
        self.flags = [False] * 16
        self.epoch = epoch

    def __repr__(self):
        result = f"BranchNode(epoch={self.epoch})\n"
        for i in range(16):
            if self.flags[i]:
                result += f"  [{i:x}] → {self.branches[i]}\n"
        return result
