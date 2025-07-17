# networking/cross_shard.py

import socket
import json
import time

from blockchain.hashing import get_merkle_root
from config import (
    Any_Host,
    Cross_shard_Network_Congession_Delay,
    LEADER_PORT_FOR_ACK_RCV,
    LEADER_PORT_FOR_BATCH_RCV,
)


def cross_send_transaction(batch, receiver_shard, id, OTHER_SHARD_IPS):
    """Function to simulate a transaction between nodes."""

    '''
        -Listen the ack of the batch from receiver shard leader
    '''

    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((Any_Host, LEADER_PORT_FOR_ACK_RCV))  # Bind to the port for cross-shard communication
    server.settimeout(1)

    # Calculate the Merkle root of the batch
    merkle_root = get_merkle_root(batch)
    # print(merkle_root)
    batch_with_merkle_root = {"B": batch, "MR": merkle_root, "I":id}
    receiver_shard_ip = OTHER_SHARD_IPS[receiver_shard - 1]  # receiver_shard - 1 -> karon OTHER_SHARD_IPS list e nij shard er IP nai

    '''
        - create socket 
        - send the batch to receiver shard leaders
    '''
    
    # Send the batch to the receiver shard leader 
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # Increase send buffer size
        try:
            # Convert the batch to JSON format for sending
            transaction_batch = json.dumps(batch_with_merkle_root)
            '''
                - incorporate some time as network congestion
            '''
            time.sleep(Cross_shard_Network_Congession_Delay)

            client.sendto(transaction_batch.encode(), (receiver_shard_ip, LEADER_PORT_FOR_BATCH_RCV))
            # print(f"Sent batch to Shard {receiver_shard} with Merkle Root: {merkle_root}")


        except Exception as e:
            print(f"Error sending transaction batch: {str(e)}")
    
    attempts = 0
    max_retries = 2
    while attempts < max_retries:
        try:
            # print("=========Batch===========") 
            data, addr = server.recvfrom(1024)  # Receive response
            # print(f"Data: {data}")  
            if data:
                ack_message = data.decode().strip()

                ''' Jodi majority voting (BFT) na chai'''

                if ack_message.startswith("Batch received"):
                    try:
                        batch_id = int(ack_message.split(":")[1].strip())
                        # print(f"ACK received for Batch ID: {batch_id} from {addr}")
                        return True
                    
                    except ValueError:
                        print(f"Invalid batch ID format in message: '{ack_message}'")
                    
                    
                else:
                    print("BLock invalid!")
                    return False  # Invalid block


        except socket.timeout:
            print(f"Batch: Timeout for ACK, attempt {attempts + 1} of {max_retries}")
            attempts += 1
