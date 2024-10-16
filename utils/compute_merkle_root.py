import sys
from merkle_tree import MerkleTree

def read_file_in_blocks(file_path, block_size=512 * 1024):
    with open(file_path, 'r') as f:
        while True:
            data = f.read(block_size)
            if not data:
                break
            yield data

def compute_merkle_root(file_path):
    data_blocks = list(read_file_in_blocks(file_path))
    merkle_tree = MerkleTree(data_blocks)
    return merkle_tree.get_root()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python compute_merkle_root.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    merkle_root = compute_merkle_root(file_path)
    print(f"Merkle Root: {merkle_root}")
