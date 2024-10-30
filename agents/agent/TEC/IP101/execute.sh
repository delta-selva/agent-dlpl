#!/bin/bash

# Check if all required parameters are provided
if [ "$#" -ne 5 ]; then
    echo "Usage: $0 <scan_id> <folder> <result_path> <interface> <target_ip>"
    exit 1
fi

scan_id=$1
folder_path=$2 
result_path=$3
interface=$4
target_ip=$5

# Print out what we are running for debugging
# echo "Running script: python3 $interface $target_ip"

# Run the Python script and capture output
python3 "$folder_path/test.py" "$scan_id" "$result_path" "$interface" "$target_ip"

# Check if the Python script executed successfully
if [ $? -ne 0 ]; then
    echo "Error executing test.py: $output"
    exit 1
else
    echo "$output"  # Print the output (this should contain the JSON)
fi

# Now run the second Python script (report.py) for .docx creation
python3 "$folder_path/report.py" "$scan_id" "$result_path" "$folder_path"

# Check if the second Python script executed successfully
if [ $? -ne 0 ]; then
    echo "Error executing report.py"
    exit 1
else
    echo "report.py executed successfully"
fi
