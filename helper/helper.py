# transaction/helper.py

import csv
import json
import time
import random
import fcntl

from config import (
    BATCH_SIZE, 
    Transaction_Rate, 
    TX_PER_BLOCK, 
    Total_tx, 
    Cross_shard_Network_Congession_Delay,
)

from mytrie import (
    Trie,
    initialize_trie, 
    update_trie, 
)

from blockchain import (
    create_block,
)

from networking import (
    intra_send_transaction,  
    broadcast_tx_to_shard,
    cross_send_transaction,
)

from utils import (
    get_group_set, 
    build_node_to_group_index,
    get_local_ip, 
    get_global_ip,
)



def initialize_environment(json_path, shard_index, json_path_id_to_node, file_path):
    group0_senders = get_group_set(json_path, index=shard_index)
    node_to_group = build_node_to_group_index(json_path)

    with open(json_path_id_to_node, 'r') as f:
        id_to_address = json.load(f)

    world_trie = Trie()
    world_trie = initialize_trie(world_trie, file_path, id_to_address, epoch=1)

    return group0_senders, node_to_group, id_to_address, world_trie


def read_transaction_batch(reader, tx_rate):
    batch = [next(reader, None) for _ in range(tx_rate)]
    return [tx for tx in batch if tx is not None]


def clean_address(addr):
    return addr[2:].lower() if addr.startswith("0x") or addr.startswith("0X") else addr.lower()

# For SPARC
def route_transaction(
    tx, sender_id, receiver_id, group0_senders, node_to_group,
    cross_shard_tx_pool, intra_transaction_pool, mempool, batch_counter,
    total_transactions, cross_shard_transactions_cnt, cross_communication, pool_lock, OTHER_SHARD_IPS
):
    if str(receiver_id) in group0_senders:
        mempool.append(tx)
        broadcast_tx_to_shard(tx)
        intra_transaction_pool.append(tx)
        total_transactions += 1
    else:
        sender_shard_index = node_to_group.get(str(sender_id))
        receiver_shard_index = node_to_group.get(str(receiver_id))
        if receiver_shard_index is None:
            receiver_shard_index = random.choice(list(set(node_to_group.values())))

        cross_shard_tx_pool[receiver_shard_index].append(tx)
        cross_shard_transactions_cnt += 1
        total_transactions += 1

        if len(cross_shard_tx_pool[receiver_shard_index]) >= BATCH_SIZE - 1 or (
            len(cross_shard_tx_pool[receiver_shard_index]) >= BATCH_SIZE and BATCH_SIZE == 1):
            with pool_lock:
                batch_counter[sender_shard_index][receiver_shard_index] += 1
                batched_tx = cross_shard_tx_pool[receiver_shard_index][:BATCH_SIZE]
                cross_send_transaction(
                    batched_tx, receiver_shard_index,
                    batch_counter[sender_shard_index][receiver_shard_index],
                    OTHER_SHARD_IPS
                )
                mempool.extend(batched_tx)
                cross_shard_tx_pool[receiver_shard_index] = cross_shard_tx_pool[receiver_shard_index][BATCH_SIZE:]
                cross_communication += 1

    return total_transactions, cross_shard_transactions_cnt, cross_communication
 
# Without GraphSAGE   
def route_transaction_random(
    tx, sender_id, receiver_id, NUM_SHARDS, node_to_group,
    cross_shard_tx_pool, intra_transaction_pool, mempool, batch_counter,
    total_transactions, cross_shard_transactions_cnt, cross_communication, pool_lock, OTHER_SHARD_IPS
):
    ideal_cross_shard_ratio = (NUM_SHARDS - 1) / NUM_SHARDS
    
    if random.random() > ideal_cross_shard_ratio:
        mempool.append(tx)
        broadcast_tx_to_shard(tx)
        intra_transaction_pool.append(tx)
        total_transactions += 1
        
    else:
        sender_shard_index = node_to_group.get(str(sender_id))
        receiver_shard_index = node_to_group.get(str(receiver_id))
        if receiver_shard_index is None:
            receiver_shard_index = random.choice(list(set(node_to_group.values())))

        cross_shard_tx_pool[receiver_shard_index].append(tx)
        cross_shard_transactions_cnt += 1
        total_transactions += 1

        if len(cross_shard_tx_pool[receiver_shard_index]) >= BATCH_SIZE - 1 or (
            len(cross_shard_tx_pool[receiver_shard_index]) >= BATCH_SIZE and BATCH_SIZE == 1):
            with pool_lock:
                batch_counter[sender_shard_index][receiver_shard_index] += 1
                batched_tx = cross_shard_tx_pool[receiver_shard_index][:BATCH_SIZE]
                cross_send_transaction(
                    batched_tx, receiver_shard_index,
                    batch_counter[sender_shard_index][receiver_shard_index],
                    OTHER_SHARD_IPS
                )
                mempool.extend(batched_tx)
                cross_shard_tx_pool[receiver_shard_index] = cross_shard_tx_pool[receiver_shard_index][BATCH_SIZE:]
                cross_communication += 1
    
    
    return total_transactions, cross_shard_transactions_cnt, cross_communication


def print_summary(
    start_time, total_transactions, total_latency,
    blockchain, cnt_world, cnt_block,
    cross_shard_transactions_cnt, cross_communication, new_node
):
    end_time = time.time()
    total_time = end_time - start_time

    print(f"Latency: {total_time}")

    shard_tps, block_generated, total_tx = blockchain.calculate_tps(start_time)
    print(f"Average tx latency : {total_latency / total_tx} (Time: {total_latency}, Tx: {total_tx})")
    print(f"----------------------------------------------")
    print(f"World lookup: {cnt_world}")
    print(f"New node: {new_node}")
    print(f"Number of block in this shard: {block_generated}")
    print(f"TPS (processed in blockchain): {shard_tps:.2f}")

    with open("result.txt", "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(f"Batch size : {BATCH_SIZE}, Tx per Block : {TX_PER_BLOCK}, Tx Rate : {Transaction_Rate}, Total Tx : {Total_tx}, CTx delay : {Cross_shard_Network_Congession_Delay}\n")
        f.write(f"Average tx latency : {total_latency / total_tx} (Time: {total_latency}, Tx: {total_tx})\n")
        f.write(f"Number of block in this shard: {block_generated}, Cross Communication: {cross_communication}\n")
        f.write(f"TPS (processed in blockchain): {shard_tps:.2f}\n\n")
        fcntl.flock(f, fcntl.LOCK_UN)

    if total_transactions > 0:
        cross_shard_ratio = cross_shard_transactions_cnt / total_transactions
        print(f"Cross-communication count: {cross_communication} ({cross_communication / total_transactions})")
        print(f"Cross-shard Ratio: {cross_shard_ratio:.2f} ({cross_shard_transactions_cnt}/{total_transactions})")
