'''
Task of update_files.py: 
----------------------------------------------------------------------------------------
1. update the SHARD_IPS of config.py file
    # SHARD_IPS list gets updated by the machine's IP (local/global) if it is not available
    # Change the update_files.py file to use either LOCAL or GLOBAL IP

2. remove all the CTx from the retention table 

'''

import socket
import os
import re
import requests # type: ignore

CONFIG_FILE = "config.py"

def get_local_ip():
    return socket.gethostbyname(socket.gethostname())

def get_global_ip():
    try:
        response = requests.get("https://ifconfig.me", timeout=5)  # Fetch public IP
        return response.text.strip()
    except requests.RequestException:
        print("Error fetching global IP.")

def update_config():
    ip = get_local_ip()
    ip = get_global_ip()

    # Ensure SHARD_IPS exists
    SHARD_IPS = []  

    if os.path.exists(CONFIG_FILE):  # Check if config.py exists
        try:
            with open(CONFIG_FILE, "r") as file:
                content = file.read()
                exec(content, globals())  # Load existing SHARD_IPS
                if 'SHARD_IPS' in globals():
                    SHARD_IPS = globals()['SHARD_IPS']  # Ensure SHARD_IPS is set
        except Exception as e:
            print(f"Error reading {CONFIG_FILE}: {e}")
            return

    # Append new IP if not already in the list
    if ip not in SHARD_IPS:
        SHARD_IPS.append(ip)

        # Read the existing config
        with open(CONFIG_FILE, "r") as file:
            content = file.read()

        # Replace existing SHARD_IPS or add it if missing
        if "SHARD_IPS =" in content:
            content = re.sub(r"SHARD_IPS\s*=\s*\[.*?\]", f"SHARD_IPS = {SHARD_IPS}", content, flags=re.DOTALL)
        else:
            content += f"\nSHARD_IPS = {SHARD_IPS}\n"

        # Write back the updated config without overwriting other settings
        with open(CONFIG_FILE, "w") as file:
            file.write(content)

        print(f"Updated {CONFIG_FILE} with IP: {ip}")
    else:
        print(f"IP {ip} already exists in {CONFIG_FILE}")
 
        

# **Execute only if the script is run directly**
if __name__ == "__main__":
    update_config()  # This will run only when you execute `update_files.py` directly
    