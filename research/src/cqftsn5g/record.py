import pandas as pd

# Define the paths to your scalar and vector files
scalar_file_path = "results/UDPDL-numUEs=1-#0.sca"
vector_file_path = "results/UDPDL-numUEs=1-#0.vec"

# Load the scalar and vector files into pandas DataFrames
scalar_df = pd.read_csv(scalar_file_path, sep="\t", comment="#", header=None)
vector_df = pd.read_csv(vector_file_path, sep="\t", comment="#", header=None)

# Define column names for better readability (adjust according to your result file structure)
scalar_df.columns = ["run", "module", "name", "value"]
vector_df.columns = ["run", "module", "name", "index", "time", "value"]

# Filter the DataFrame to find specific metrics (e.g., packet byte lengths)
packet_sizes = scalar_df[scalar_df["name"].str.contains("packetByteLength")]

# Print or analyze the filtered DataFrame
print(packet_sizes)

# Example: Calculate the average packet size
average_packet_size = packet_sizes["value"].astype(float).mean()
print(f"Average Packet Size: {average_packet_size} bytes")
