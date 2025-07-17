import socket
import threading
import time
import hashlib
import json

from utils import (
    get_local_ip, 
    get_global_ip,
)

from config import (
    SHARD_IPS,
    LEADER_PORT_FOR_BATCH_RCV,
    LEADER_PORT_FOR_ACK_RCV,
    BASE_PORT,
    BLOCK_RCV_PORT,
    CROSS_SHARD_PORT,
    VALIDATORS,
    Local_Host,
    Any_Host,
)

from blockchain import (
    hash_string, 
    hash_dict,
    get_merkle_root,
)

MY_IP = get_local_ip() # Local IP
MY_IP = get_global_ip() # Global IP
OTHER_SHARD_IPS = [ip for ip in SHARD_IPS if ip != MY_IP]  # Exclude MY_IP


cross_shard_tx_count = 0

# List to store cross-shard transactions
cross_shard_transactions = []

lock = threading.Lock()


def verify_transaction_batch(batch):
    """Verify the batch of transactions by checking the Merkle root."""
    
    # Extract the Merkle root from the received batch
    received_merkle_root = batch.get('MR')  
    transactions = batch.get('B')
    
    if not received_merkle_root or not transactions:
        print("Invalid batch: Missing transactions or Merkle root.")
        return False
    
    # Recompute the Merkle root from the transactions
    recomputed_merkle_root = get_merkle_root(transactions)
    
    # print(recomputed_merkle_root)
    
    # Compare the recomputed Merkle root with the received Merkle root
    if recomputed_merkle_root == received_merkle_root:
        print("Batch verification successful. Merkle roots match.")
        return True
    else:
        print("Batch verification failed. Merkle roots do not match.")
        return False

def node_server(validator):
    global cross_shard_tx_count
    validator_port = BASE_PORT + validator

    '''
        - server for receiving intra_shar tx and block
    '''

    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        server.bind((Any_Host, validator_port))  # Bind each server to a unique port
        print(f'Validator {validator} listening on {Any_Host}:{validator_port}')

    except OSError as e:
        print(f"Error binding to port {validator_port}: {e}")
        return

    while True:
        try:
            data, addr = server.recvfrom(1024)
            # print(data)
            if data:
                data_str = data.decode()
                data_json = json.loads(data_str)
                '''
                jodi Tx (either intra or cross) receive kore tahole, response pathanor kicu nai
                '''
                if"Tx:" in data_json:
                    sender_ip = addr[0]
                    sender_shard_id = OTHER_SHARD_IPS.index(sender_ip) if sender_ip in OTHER_SHARD_IPS else -1
                    # print(data_str)

                    '''
                    Target: Other shard er tx gula process korbe
                    --------------------------------------------
                    condition: sender_shard_id != -1
                    ei condition deya jeno unknown kono shard asle handle kore (in case)
                    '''
                    
                    if sender_shard_id != -1:  
                        transaction = data.decode()  # Get the transaction data
                        with lock:
                            cross_shard_tx_count += 1
                            cross_shard_transactions.append(transaction)  # Store the transaction
                        # print(f'Node {node_id} received CTx from Shard {sender_shard_id}: {data.decode()}')
                
                # jodi block (cross-shard er jonne broadcast) receive kore tahole response pathabe 
                elif "Block" in data_json:
                    sender_ip = addr[0]
                    ack = "Block received"
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
                        try:
                            client.sendto(ack.encode(), (Local_Host, BLOCK_RCV_PORT))
                            print(f"Sent block ack from Server - {Local_Host}: {BLOCK_RCV_PORT}")

                        except Exception as e:
                            print(f"Error sending block to Shard : {e}")

            else:
                print("Data is not valid!")

        except Exception as e:
            print(f'Error on Node {validator}: {str(e)}')
            break

    server.close()
    print(f'Validator Node {validator} shutting down.')

def batch_handling():
        
    '''
        - another server for receiving the batch from cross shard
    '''

    server_cross = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        server_cross.bind((Any_Host, LEADER_PORT_FOR_BATCH_RCV))  # Bind each server to a unique port
        print(f'Leader listening on {Any_Host}:{LEADER_PORT_FOR_BATCH_RCV}')

    except OSError as e:
        print(f"Error binding to (Leader) port {LEADER_PORT_FOR_BATCH_RCV}: {e}")
        return
    
    
    while True:
        try:
            data, addr = server_cross.recvfrom(1024)
            # print(data)
            if addr[0] == MY_IP:
                continue

            if data:
                data_str = data.decode()
                
                try:
                    # print(data_str)
                    data_json = json.loads(data_str)
                    
                    if "B" in data_json:
                        # print("Batch Received!!")
                        if verify_transaction_batch(data_json):
                            print("Batch Valid!")

                            sender_ip = addr[0]
                            batch_id = data_json.get('I') # I = ID
                            ack = f"Batch received: {batch_id}"

                            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
                                try:
                                    client.sendto(ack.encode(), (sender_ip, LEADER_PORT_FOR_ACK_RCV))
                                    print(f"Sent batch ack from Server - {sender_ip}: {LEADER_PORT_FOR_ACK_RCV}")

                                except Exception as e:
                                    print(f"Error sending batch to Shard : {e}" )
                
                except json.JSONDecodeError as e:
                    print(f"Error decodin JSON: {e}")

            else:
                print("Data is not valid!")

        except Exception as e:
            print(f'Error on Leader Node: {str(e)}')
            break

    server_cross.close()
    print(f'Leader node shutting down.')



def start_nodes():
    threads = []
    for validator in range(VALIDATORS):
        thread = threading.Thread(target=node_server, args=(validator,))
        thread.daemon = True
        thread.start()
        threads.append(thread)

    # Start sending cross-shard tx count
    threading.Thread(target=batch_handling, daemon=True).start()

    time.sleep(2)

    try:
        while True:
            time.sleep(5)
            with lock:
                print(f'Total Cross-Shard Transactions so far: {cross_shard_tx_count}')
    except KeyboardInterrupt:
        print("Stopping servers...")

    for thread in threads:
        thread.join()
    print("All nodes stopped.")

if __name__ == "__main__":
    start_nodes()