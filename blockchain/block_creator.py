# blockchain/block_creator.py

from config import TX_PER_BLOCK

def create_block(tx_pool, blockchain):
    """Leader creates a block with the collected transactions."""
    
    # print(intra_shard_txs)

    if len(tx_pool) >= TX_PER_BLOCK:
        # Create block with exactly TX_PER_BLOCK transactions
        block_transactions = tx_pool[:TX_PER_BLOCK]
        block, latency = blockchain.create_block(block_transactions)
        print(f"Block created with {len(block['transactions'])} transactions at height {block['block_height']}.")
        
        # self.tx_tot += len(block["transactions"])
        # print(tx_tot)

        # Remove the transactions that were included in the block
        del tx_pool[:TX_PER_BLOCK]
        # print(len(tx_pool))
    
    else:
        # Create block with exactly TX_PER_BLOCK transactions 
        block_transactions = tx_pool[:]
        block, latency = blockchain.create_block(block_transactions)
        print(f"Block created with {len(block['transactions'])} transactions at height {block['block_height']}.")
        
        # Remove the transactions that were included in the block
        # print(len(tx_pool))
        tx_pool.clear()  # Clear the list to reflect the transaction removal

        # print(f"Shard {shard_id}: Not enough transactions to create a block. Waiting for more transactions.")
        
    return latency
