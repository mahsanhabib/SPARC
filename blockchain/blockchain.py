import socket
import json
import time
import hashlib


# === Internal Utilities (from current package) === 
from .hashing import hash_string, hash_dict, get_merkle_root


# === Configuration Constants (Project-level configuration imports) ===
from config import (
    BASE_PORT,
    BLOCK_RCV_PORT,
    VALIDATORS,
    Local_Host,
)


# Blockchain data structure for each shard
class Blockchain:
    def __init__(self):
        self.blocks = []  # List to hold all blocks
        self.block_height = 0  # Block height (incremented for each new block)
        self.tx_tot = 0   # Store the total number of transactions

    def intra_send_block(self, block, validator):
        '''
            - send the block to all the validator of the shard
        '''
        
        """Function to simulate a transaction between nodes."""
        validator_port = BASE_PORT + validator
    

        '''
            - block send using UDP
        '''

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
            client.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # Increase send buffer size
            try:
                block_data = f'Block: sent for broading'
                block_data = {"Block": block_data}
                block_data = json.dumps(block_data)
                block_data = str(block_data).encode()  # Convert block to bytes for transmission
                client.sendto(block_data, (Local_Host, validator_port))
                # print(f"Block sent successfully!")
            
            except Exception as e:
                print(f"Error sending block to Shard {Local_Host}: {e}")

        # '''
        #     - block send using TCP
        # '''

        # # TCP uses a connection, so we use socket.SOCK_STREAM
        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        #     client.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # Increase send buffer size
        #     try:
        #         # Connect to the validator's IP and port
        #         client.connect((Local_Host, validator_port))

        #         # Serialize the block to a string, then encode it to bytes
        #         block_data = f'Block: sent for broadcasting'
        #         block_data = block_data.encode()  # Convert block data to bytes for transmission

        #         # Send data
        #         client.sendall(block_data)
        
        #     except Exception as e:
        #         print(f"Error sending block to Shard {Local_Host}: {e}")

    def broadcast_block_to_shard(self, block):
        
        '''
            - Age thekei (block ack pawar) listening suru korbo
            - Try to listen the ack of the block from validators
        '''
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.bind((Local_Host, BLOCK_RCV_PORT))  # Bind to the port for cross-shard communication
        server.settimeout(1)

        '''
            - Broadcast the block to all the validators
        '''

        """Broadcast transaction to all validators in the sender's shard."""
        for validator in range(VALIDATORS):
            self.intra_send_block(block, validator)



        MAJORITY_THRESHOLD = VALIDATORS // 3
        votes = 0
        attempts = 0
        max_retries = 2
        while attempts < max_retries:
            try:
                # print("========================") 
                data, addr = server.recvfrom(1024)  # Receive response
                # print(f"@@@@@@ {data}")  
                if data:
                    ack_message = data.decode().strip()

                    ''' Jodi majority voting (BFT) na chai'''

                    # if ack_message == "Block received":
                    #     return True  # Valid block, append it
                    
                    # else:
                    #     return False  # Invalid block, reject it

                    ''' Jodi majority voting (BFT) chai'''

                    if ack_message == "Block received":
                        votes += 1
                        # print(f"Vote received from {addr}")
                    
                    if votes >= MAJORITY_THRESHOLD:  # Check for majority
                        print("### Block successfully accepted by majority ###")
                        return True

            except socket.timeout:
                print(f"Block : Timeout for acknowledgment, attempt {attempts + 1} of {max_retries}")
                attempts += 1
        
        print("Max retries reached, block not received")
        return False


    def create_block(self, transactions):
        """Create a new block with transactions."""
        
        total_latency = 0

        start_time = time.time()

         # Get the hash of the previous block, if available
        prev_block_hash = self.blocks[-1]["block_hash"] if self.blocks else None

        block = {
            "transactions": transactions,
            "block_height": self.block_height,
            "prev_block_hash": prev_block_hash,
            "timestamp": start_time
        }

         # Calculate the block hash (you can adjust this based on your hashing algorithm)
        block_string = str(block["transactions"]) + str(block["block_height"]) + str(block["prev_block_hash"]) + str(block["timestamp"])
        block["block_hash"] = hashlib.sha256(block_string.encode()).hexdigest()

        '''
            1. Broadcast block to its all nodes
            2. Collect the response from them
            3. Append the block based on BFT consensus algo
        '''
        if self.broadcast_block_to_shard(block):
            self.blocks.append(block)  # Append block to the blockchain
            
            # determine each tx latency in the block
            for tx in transactions:
                tx_arrival_time = tx["t"]
                tx_latency = start_time - tx_arrival_time
                total_latency += tx_latency
            
            self.block_height += 1
            self.tx_tot += len(block["transactions"])
            print("Intra Shard : Block Added")
            return block, total_latency
        
        
        # self.blocks.append(block)
        # self.block_height += 1
        return block, total_latency

    def calculate_tps(self, st):
        """Calculate the TPS of the transactions stored in the blockchain."""
        if not self.blocks:
            return 0  # No blocks, hence no TPS
        
        # print(len(self.blocks))
        total_transactions = sum(len(block['transactions']) for block in self.blocks)
        
        
        
        # Calculate the time span of the first and last transactions in the blockchain
        start_time = self.blocks[0]['timestamp']
        end_time = self.blocks[-1]['timestamp']
        total_time = end_time - st
        
        # TPS = Total Transactions / Total Time
        tps = total_transactions / total_time if total_time > 0 else 0
        return tps, self.block_height, total_transactions


