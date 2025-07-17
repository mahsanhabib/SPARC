import socket
import sys
import random
import time
import json
import csv
import math
import threading
import numpy as np
import fcntl
import hashlib
from collections import defaultdict


# Tries are handled in "mytrie" directory
from mytrie import (
    Trie,
    initialize_trie, 
    update_trie, 
    reconfiguration,
)

# Blockchain is handled in "blockchain" directory
from blockchain import (
    get_merkle_root, 
    create_block,
    Blockchain,
)

# Intra-shard and inter-shard transactions are handled in "networking" directory
from networking import (
    intra_send_transaction,  
    broadcast_tx_to_shard,
    cross_send_transaction,
)

# Other tasks are handled in "utils" directory
from utils import (
    get_group_set, 
    build_node_to_group_index,
    get_local_ip, 
    get_global_ip,
    create_parser,
)

# Import different variables from config file
from config import (
    # Network IPs and Host Settings
    SHARD_IPS,
    VALIDATORS,
    Local_Host,
    Any_Host,

    # Ports
    BASE_PORT,
    BLOCK_RCV_PORT,
    CROSS_SHARD_PORT,
    LEADER_PORT_FOR_BATCH_RCV,
    LEADER_PORT_FOR_ACK_RCV,

    # Transaction and Block Configuration
    BATCH_SIZE,
    TX_PER_BLOCK,
    Transaction_Rate,
    block_creation_interval,
    Cross_shard_Network_Congession_Delay,
    Total_tx,
    epoch_length,
)

# Import starting, initializing functions from "helper" directory
from helper import (
    initialize_environment,
    read_transaction_batch,
    clean_address,
    route_transaction,
    route_transaction_random,
    print_summary,
)


'''
1. Decise to use LOCAL or GLOBAL IP 
2. Make sure "SHARD_IPS" list of the "config.py" file is up-to-date 
3. Otherwise, run "update_config.py" to update it
4. After that the fetching (the following line) is correct
'''

MY_IP = get_local_ip() # Local IP
MY_IP = get_global_ip() # Global IP
OTHER_SHARD_IPS = [ip for ip in SHARD_IPS if ip != MY_IP]  # Exclude MY_IP
NUM_SHARDS = len(OTHER_SHARD_IPS) + 1


stop_flag = False


# Track transactions for each shard
mempool = []
mempool_sup = []  # just for checking
intra_transaction_pool = []
cross_shard_tx_pool = defaultdict(list)  # key: group_index, value: list of txs
batch_counter = defaultdict(lambda: defaultdict(int))

cross_communication = 0
total_latency = 0

cnt_world = 0

cnt_block = 0
cnt_epoch = 0

new_node = 0

trie_check_time = 0
reconf_time = 0

# Create the parser using the separate parser file
parser = create_parser()
args = parser.parse_args()  # Parse the command line arguments

# Access the parsed values
# target_shard = args.target_shard
shard_index = args.shard_index

# Instantiate the blockchain
blockchain = Blockchain()


file_path = "/work/mhabib/GraphSAGE/Feature/12M/Last_2M_Tx.csv"
# file_path = "/work/mhabib/GraphSAGE/Feature/17M/last_2_million_tx (17M).csv"

json_path = "/work/mhabib/GraphSAGE/Partitions/12M/10_shards.json"
# json_path = "/work/mhabib/GraphSAGE/Partitions/17M/10_shards.json"

json_path_id_to_node = "/work/mhabib/GraphSAGE/Feature/12M/ID to Address (12M).json"
# json_path_id_to_node = "/work/mhabib/GraphSAGE/Feature/12M/ID to Address (12M).json"


TPS_per_shard = Transaction_Rate // NUM_SHARDS 
transaction_delay = 1 / TPS_per_shard 

tx_per_shard = Total_tx // NUM_SHARDS 

pool_lock = threading.Lock()


def start_transactions():
    """Simulate sending random transactions between nodes."""
    
    global intra_transaction_pool, cross_shard_tx_pool, mempool, cross_communication
    global cnt_block, cnt_epoch, total_latency, new_node
    global cnt_world, trie_check_time, reconf_time
    
    total_transactions = 0
    cross_shard_transactions_cnt = 0
    
    Tx_Read = 0
    tx_id = 0
    epoch = 1
    
    group0_senders, node_to_group, id_to_address, world_trie = initialize_environment(json_path, shard_index, json_path_id_to_node, file_path)
    
    start_time = time.time()
    last_block_creation_time = start_time  # Track the last block creation time
    
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header if present
    
        while Tx_Read < Total_tx:
            ss = time.time()
            
            batch = read_transaction_batch(reader, Transaction_Rate)

            if not batch:
                break  # Stop if there are no more transactions

            for tx in batch:
                try:
                    sender_id = str(tx[0]).strip()
                    receiver_id= str(tx[1]).strip()
                    amount = float(tx[2])
                    
                    # Look up addresses
                    sender = id_to_address.get(sender_id, "0x1770f97777679d8994770352e8c8e3b432fac526")
                    receiver = id_to_address.get(receiver_id, "0x68474eef4d5d66ed985c151ef0b1291d06b7dfd7")
                    
                    sender = clean_address(sender)
                    receiver = clean_address(receiver)
                    
                except:
                    continue
                
                # print(f"Sender address: {sender_address}")
                # print(f"Receiver address: {receiver_address}")
                
                # print(sender_id, receiver_id, amount)
                
                # sender must be stored in previously
                if str(sender_id) in group0_senders: 
                    
                    # tx = f'sender_id: {sender_id}, receiver_id: {receiver_id}, amount: {amount}'
                    tx_id += 1
                    tx = {
                            "i": tx_id,   # i = id
                            "s": sender_id,  # s = sender_id
                            "r": receiver_id, # r = receiver_id
                            "a": amount,   # a = amount
                            "t":time.time()  # t = timestamp
                        }
                    
                    # update the state of world trie
                    cnt_world, new_node, check_time = update_trie(world_trie, sender, receiver, amount, epoch, cnt_world, new_node)
                    
                    total_transactions, cross_shard_transactions_cnt, cross_communication = route_transaction(
                        tx, sender_id, receiver_id, group0_senders, node_to_group,
                        cross_shard_tx_pool, intra_transaction_pool, mempool, batch_counter,
                        total_transactions, cross_shard_transactions_cnt, cross_communication, pool_lock, OTHER_SHARD_IPS
                    )
                    
                    # total_transactions, cross_shard_transactions_cnt, cross_communication = route_transaction_random(
                    #     tx, sender_id, receiver_id, NUM_SHARDS, node_to_group,
                    #     cross_shard_tx_pool, intra_transaction_pool, mempool, batch_counter,
                    #     total_transactions, cross_shard_transactions_cnt, cross_communication, pool_lock, OTHER_SHARD_IPS
                    # )


            # Check if it's time to create a block based on the interval
            current_time = time.time()
            if current_time - last_block_creation_time >= block_creation_interval:
                
                # Time to create a block
                if len(mempool) >= 1:
                    last_block_creation_time = current_time  # Update the last block creation time
                    latency = create_block(mempool, blockchain)
                    total_latency += latency
                    # print(len(mempool))
                    
                    cnt_block += 1
                    
                    # update the tries
                    if cnt_block % epoch_length == 0:
                        st = time.time()
                        
                        reconfiguration(NUM_SHARDS, world_trie)
                        
                        reconf_time += time.time() - st
                        
                        cnt_epoch += 1
                        epoch += 1

                    
                '''
                    - Calculate Buffer Table size after this interval
                '''
    
                # RT_byte = sys.getsizeof(cross_shard_tx_pool)
                total_buffer_len = 0
                for group_index, tx_list in cross_shard_tx_pool.items():
                    total_buffer_len += len(tx_list)
                
                print(f"Buffer tables size (all shards): {total_buffer_len}")
    
                # print(f"Buffer table size: {len(cross_shard_tx_pool)}, in {RT_byte/1:.2f} B")
                print(f"Mempool size: {len(mempool) + total_buffer_len}")
                
                with open("result_pool.txt", "a") as f:
                    fcntl.flock(f, fcntl.LOCK_EX)  # exclusive lock
                    f.write(f"Shard: {group_index}, Buffered Txs: {total_buffer_len}, Mempool: {len(mempool) + total_buffer_len}\n")
                    fcntl.flock(f, fcntl.LOCK_UN)  # release lock
                    
            
            trie_check_time += check_time
            
            Tx_Read += Transaction_Rate
            elapsed = time.time() - ss
            remaining_time = 1.0 - elapsed
            if remaining_time > 0:
                time.sleep(remaining_time)
                
    
    while len(mempool) >= 1:  # Ensure we have enough transactions
        # Check if it's time to create a block based on the interval
        current_time = time.time()
        if current_time - last_block_creation_time >= block_creation_interval:
            last_block_creation_time = current_time  # Update the last block creation time
            latency = create_block(mempool, blockchain)  # shard_id = 0 karon nijer shard e block create korbe
            total_latency += latency
            # print(f"Mempool size: {len(mempool)}")
            # time.sleep(1)
    
    
    # Final stats printing
    print_summary(
        start_time=start_time,
        total_transactions=total_transactions,
        total_latency=total_latency,
        blockchain=blockchain,
        cnt_world=cnt_world,
        cnt_block=cnt_block,
        cross_shard_transactions_cnt=cross_shard_transactions_cnt,
        cross_communication=cross_communication, 
        new_node=new_node
    )
    
    print(f"Total trie checking time : {trie_check_time}")
    print(f"Reconfiguration time: {reconf_time}")

    # Stop the receiver after transactions are done
    global stop_flag
    stop_flag = True

    print(f"Stop Flag is : {stop_flag}")
    # print(cross_shard_tx_pool)


if __name__ == "__main__":
    
    st = time.time()
    
    # start_transactions()

    # Start the thread to process transactions
    transaction_thread = threading.Thread(target=start_transactions, daemon=True)
    transaction_thread.start()


    # Keep the main thread alive to let threads run
    transaction_thread.join()
    # receive_thread.join()
    
    et = time.time()
    
    # print(f"Transaction latency: {et-st}")
    