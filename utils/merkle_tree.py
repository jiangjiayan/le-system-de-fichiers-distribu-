import hashlib

class MerkleTree:
    def __init__(self, data_blocks):
        self.data_blocks = data_blocks
        self.tree = self.build_merkle_tree(data_blocks)

    def hash(self, data):
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def build_merkle_tree(self, data_blocks):
        tree = [self.hash(block) for block in data_blocks]
        while len(tree) > 1:
            if len(tree) % 2 == 1:
                tree.append(tree[-1])
            tree = [self.hash(tree[i] + tree[i + 1]) for i in range(0, len(tree), 2)]
        return tree[0]

    def get_root(self):
        return self.tree

    def verify_block(self, block, proof):
        current_hash = self.hash(block)
        for sibling in proof:
            if sibling[1] == 'left':
                current_hash = self.hash(sibling[0] + current_hash)
            else:
                current_hash = self.hash(current_hash + sibling[0])
        return current_hash == self.get_root()
