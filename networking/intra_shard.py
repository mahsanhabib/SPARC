# networking/intra_shard.py

import socket
import json
from config import BASE_PORT, VALIDATORS, Local_Host

def intra_send_transaction(transaction, validator):
    """Function to simulate a transaction between nodes."""

    validator_port = BASE_PORT + validator

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        try:
            transaction = {"Tx": transaction}
            transaction = json.dumps(transaction)
            client.sendto(transaction.encode(), (Local_Host, validator_port))
            # print(f'Tx: {sender} -> {receiver}: {amount} | Shard: {Local_Host}, Port: {validator_port} ')
        
        except Exception as e:
            print(f'Error sending transaction: {str(e)}')

def broadcast_tx_to_shard(tx):
    """Broadcast transaction to all nodes in the sender's shard."""
    for validator in range(VALIDATORS):
        intra_send_transaction(tx, validator) # jehetu intra shard tx tai 2 ta shard no e same