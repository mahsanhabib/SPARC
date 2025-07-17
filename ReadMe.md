# SPRARC


To run the SPARC successfully:
------------------------------------
    1. Decise to use LOCAL or GLOBAL IP 
    2. Make sure "SHARD_IPS" list of the "config.py" file is up-to-date (SHARD_IPS should contain the ip address of all shards/machines)
    3. Otherwise, run "update_config.py" to update it
    4. We need two terminals to run two different python files (You can use "tmux")
    5. Run "python server.py" to each machine/shard
    6. Run "python client.py --shard_index 0/1/...." to each shard/machine
    7. Upon completion of all shards - Run "python result_calc.py" to calculate the result


Data will be made available upon request.
