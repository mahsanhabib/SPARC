# mytrie/trie.py

from .leaf_node import LeafNode
from .branch_node import BranchNode

class Trie:
    def __init__(self, epoch=0):
        self.root = BranchNode(epoch)

    def insert(self, key: str, value, epoch: int):
        node = self.root
        nibbles = [int(c, 16) for c in key]

        # print(nibbles)

        for i, nibble in enumerate(nibbles):
            # Update the epoch of the current branch node
            if isinstance(node, BranchNode):
                node.epoch = max(node.epoch, epoch)
                
            if i == len(nibbles) - 1:
                # Last nibble → insert leaf
                node.branches[nibble] = LeafNode(nibble, value, epoch)
                node.flags[nibble] = True
            else:
                # Intermediate nibble → ensure branch
                if not node.flags[nibble]:
                    node.branches[nibble] = BranchNode(epoch)
                    node.flags[nibble] = True

                child = node.branches[nibble]
                if isinstance(child, LeafNode):
                    raise ValueError(f"Conflict: expected branch, found leaf at nibble {nibble:x}")
                node = child

    def get(self, key_hex: str, epoch: int):
        node = self.root
        nibbles = [int(c, 16) for c in key_hex]

        for i, nibble in enumerate(nibbles):
            if not node.flags[nibble]:
                return None  # No such path

            node = node.branches[nibble]

            if i == len(nibbles) - 1:
                if isinstance(node, LeafNode):
                    node.epoch = epoch  # Update epoch on access
                    return node.value
                else:
                    return None  # Found a branch at the last nibble – should be leaf

            if not isinstance(node, BranchNode):
                return None  # Structure violation

        return None  # Should not reach here
    
    def prune_by_branch_epoch(self, node=None, parent=None, idx=None, current_epoch=0):
        if node is None:
            node = self.root

        if isinstance(node, BranchNode):

            # If this branch is old, prune it and skip its children
            if node.epoch < current_epoch and parent is not None and idx is not None:
                parent.flags[idx] = False
                parent.branches[idx] = None  # Mark as pruned
                # print("pruned success")
                return # Do not recurse into children

            # Otherwise, check children
            for i in range(16):
                if node.flags[i]:
                    child = node.branches[i]
                    self.prune_by_branch_epoch(child, node, i, current_epoch)
                    
        elif isinstance(node, LeafNode):
            if node.epoch < current_epoch and parent is not None and idx is not None:
                # print(f"Pruning leaf at epoch {node.epoch} (cut from parent at index {idx})")
                parent.flags[idx] = False
                parent.branches[idx] = None


    def print_trie(self, node=None, depth=0, path=""):
        if node is None:
            node = self.root

        indent = "  " * depth

        if isinstance(node, BranchNode):
            # Only print this branch if it has at least one True flag
            if any(node.flags):
                print(f"{indent}{path or 'root'}: Branch(epoch={node.epoch})")
                for i in range(16):
                    if node.flags[i]:
                        child = node.branches[i]
                        self.print_trie(child, depth + 1, path + f"{i:x}")
            
            if node.flags.count(True) == 0 and all(b == None or b is None for b in node.branches):
                print(f"{indent}{node}{path or 'root'}: Empty Branch(epoch={node.epoch})")


        elif isinstance(node, LeafNode):
            print(f"{indent}{path}: Leaf(key={node.key:x}, value={node.value}, epoch={node.epoch})")
        # Do not print unknown or pruned nodes

    def size(self, node=None):
        if node is None:
            node = self.root
        count = 0
        if isinstance(node, BranchNode):
            for i in range(16):
                if node.flags[i]:
                    child = node.branches[i]
                    count += self.size(child)
        elif isinstance(node, LeafNode):
            count += 1  # count this leaf node
        return count

    def get_for_merge(self, key_hex: str):
        node = self.root
        nibbles = [int(c, 16) for c in key_hex]

        for i, nibble in enumerate(nibbles):
            if not node.flags[nibble]:
                return None  # No such path

            node = node.branches[nibble]

            if i == len(nibbles) - 1:
                if isinstance(node, LeafNode):
                    return node.value
                else:
                    return None  # Found a branch at the last nibble – should be leaf

            if not isinstance(node, BranchNode):
                return None  # Structure violation

        return None  # Should not reach here