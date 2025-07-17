import json
import hashlib

def hash_string(s):
    """Hashes a UTF-8 string using SHA256."""
    return hashlib.sha256(s.encode()).hexdigest()

def hash_dict(tx):
    """Deterministically hash a dictionary (transaction) using SHA256."""
    serialized = json.dumps(tx, sort_keys=True)  # consistent order
    return hash_string(serialized)

def get_merkle_root(transactions):
    """Generate the Merkle root from a list of transaction dicts."""
    if not transactions:
        return None

    # Step 1: Hash each transaction (dict) to get leaf hashes
    hashes = [hash_dict(tx) for tx in transactions]

    # Step 2: Build the Merkle tree
    while len(hashes) > 1:
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])  # duplicate last if odd number

        new_hashes = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i + 1]
            new_hash = hash_string(combined)
            new_hashes.append(new_hash)
        hashes = new_hashes

    return hashes[0]  # final root