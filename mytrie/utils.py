# mytrie/utils.py

import csv
import time

from .trie import Trie
from .leaf_node import LeafNode
from .branch_node import BranchNode


    
def initialize_trie(world_trie, file_path, id_to_address, epoch=1):
    
    cnt = 0
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header if present
        
        ln = 0
        
        
        for tx in reader:
            ln += 1
            
            if ln > 1000:
                break
            
            try:
                sender_id = str(tx[0]).strip()
                receiver_id = str(tx[1]).strip()
                value = float(tx[2])
                
                # Look up addresses
                sender = id_to_address.get(sender_id, "0x1770f97777679d8994770352e8c8e3b432fac526")
                receiver = id_to_address.get(receiver_id, "0x68474eef4d5d66ed985c151ef0b1291d06b7dfd7")
                
    
                if sender.startswith("0x") or sender.startswith("0X"):
                    # print(sender)
                    sender = sender[2:]
                sender = sender.lower()
                
                
    
                if receiver.startswith("0x") or receiver.startswith("0X"):
                    receiver = receiver[2:]
                receiver = receiver.lower()
                
            except:
                continue
            
            

            # Get current balances
            sender_balance = world_trie.get(sender, epoch) or 0
            receiver_balance = world_trie.get(receiver, epoch) or 0

            # Update balances
            world_trie.insert(sender, sender_balance - value, epoch)
            world_trie.insert(receiver, receiver_balance + value, epoch)
            
    
    return world_trie            

def update_trie(world_trie, sender, receiver, value, epoch, cnt_world, new_node):
    def get_balance(address):
        nonlocal cnt_world, new_node

        balance = world_trie.get(address, epoch)
        if balance is not None:
            cnt_world += 1
            return balance

        if balance is None:
            new_node += 1
            return 0

        return balance

    # Fetch sender and receiver balances efficiently
    st = time.time()
    sender_balance = get_balance(sender)
    receiver_balance = get_balance(receiver)
    et = time.time()

    # Update world_trie with new balances
    world_trie.insert(sender, sender_balance - value, epoch)
    world_trie.insert(receiver, receiver_balance + value, epoch)

    return cnt_world, new_node, et - st



# def update_val_trie(val_trie, world_trie, sender, receiver, value, epoch, cnt_val, cnt_world, new_node):
    
#     # Check if sender exist in the validator trie
#     sender_balance = val_trie.get(sender, epoch)
#     if sender_balance is not None:
#         # print(f"Sender {sender} exists in the validator trie.")
#         cnt_val += 1

#     else:
#         # Fallback to world trie if not found in validator trie
#         sender_balance = world_trie.get(sender, epoch)
#         cnt_world += 1
#         time.sleep(.005)
        
#         if sender_balance is None:
#             new_node += 1
#             sender_balance = 0


#     # Check if receiver exists in the validator trie
#     receiver_balance = val_trie.get(receiver, epoch)
#     if receiver_balance is not None:
#         # print(f"Receiver {receiver} exists in the validator trie.")
#         cnt_val += 1


#     else:
#         # Fallback to world trie if not found in validator trie
#         receiver_balance = world_trie.get(receiver, epoch)
#         # receiver_balance = 0
#         cnt_world += 1
#         time.sleep(.005)
        
#         if receiver_balance is None:
#             new_node += 1
#             receiver_balance = 0



#     # Update balances
#     val_trie.insert(sender, sender_balance - value, epoch)
#     val_trie.insert(receiver, receiver_balance + value, epoch)

#     return val_trie, cnt_val, cnt_world, new_node