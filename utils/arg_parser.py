import argparse

def create_parser():
    """Create and return the argument parser."""
    parser = argparse.ArgumentParser(description="Transaction Processing Script")
    # parser.add_argument('--target_shard', type=int, default=1, help='Machine-specific target_shard value')
    parser.add_argument('--shard_index', type=int, default=1, help='Specify shard index number for choosing nodes from the "x_shards.json" file')
    
    return parser
