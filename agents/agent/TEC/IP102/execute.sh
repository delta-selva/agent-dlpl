#!/bin/bash

# Check if all required parameters are provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <scan_id> <folder> <result_path>"
    exit 1
fi

scan_id=$1
folder_path=$2
result_path=$3

# Print out what we are running for debugging
# echo "Running script: python3 $folder_path/test.py $scan_id $result_path"

# Run the Python script and capture output
python3 "$folder_path/test.py" "$scan_id" "$result_path" # Capture output and errors

# Check if the Python script executed successfully
if [ $? -ne 0 ]; then
    echo "Error executing test.py: $output"
    exit 1
else
    echo "$output"  # Print the output (this should contain the JSON)
fi

python3 "$folder_path/IP102_report_execute.py" "$scan_id" "$result_path" "$folder_path"

# Check if the second Python script executed successfully
if [ $? -ne 0 ]; then
    echo "Error executing report.py"
    exit 1
else
    echo "report.py executed successfully"
fi
