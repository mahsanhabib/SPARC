SHARD_IPS = []


LEADER_PORT_FOR_BATCH_RCV = 5000
LEADER_PORT_FOR_ACK_RCV = 5001
BASE_PORT = 5100  # Starting port number for nodes
BLOCK_RCV_PORT = 6000
CROSS_SHARD_PORT = 6002

VALIDATORS = 50

Local_Host = '127.0.0.1'
Any_Host = '0.0.0.0'

'''
    - only for client.py
'''

TX_PER_BLOCK = 2000  # Transactions per block (hard restriction)

Transaction_Rate = 5000 # in tps

block_creation_interval = 3

BATCH_SIZE = 10

Cross_shard_Network_Congession_Delay = 0.005

Total_tx = 2000000

epoch_length = 100