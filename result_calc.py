import re
from datetime import datetime

# Read the first line from result.txt (Batch size info)
with open("result.txt", "r") as file:
    first_line = file.readline().strip()  # The first line from result.txt
    first_line = first_line.replace("2000000", "2 million")

# Read the rest of the log data
with open("result.txt", "r") as file:
    log = file.read()
    

# Extract TPS and average latency values
tps_values = [float(x) for x in re.findall(r"TPS \(processed in blockchain\): ([\d.]+)", log)]
latency_values = [float(x) for x in re.findall(r"Average tx latency\s*:\s*([\d.]+)", log)]

time_tx_pairs = re.findall(r"Time\s*:\s*([\d.]+),\s*Tx\s*:\s*(\d+)", log)
total_time = sum(float(t) for t, _ in time_tx_pairs)
total_tx = sum(int(tx) for _, tx in time_tx_pairs)


# Compute averages
avg_tps = sum(tps_values) 
avg_latency = sum(latency_values) / len(latency_values) if latency_values else 0

# Get current timestamp
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Prepare result string
result_str = (
    f"----- {len(tps_values)} shards ------\n"
    f"Average TPS: {avg_tps:.2f}\n"
    f"Average Tx Latency: {total_time / total_tx} or {avg_latency:.4f} seconds\n\n"
)

# Check if the first line (Batch size info) is already in the summary file
with open("summary.txt", "r") as summary_file:
    summary_content = summary_file.read()


result_str = f"{first_line}\n" + result_str

# Append the result to summary.txt
with open("summary.txt", "a") as outfile:
    outfile.write(result_str)

# Print to console (optional)
print(result_str)
