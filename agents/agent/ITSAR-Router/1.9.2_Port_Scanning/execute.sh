#!/bin/bash

# Check if all required parameters are provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <scan_id> <folder> <result_path>"
    exit 1
fi

scan_id=$1
folder_path=$2
result_path=$3

# Run the Python script
python3 "$folder_path/test.py" "$scan_id" "$result_path"

# Check if the Python script executed successfully
if [ $? -ne 0 ]; then
    echo "Error executing test.py"
    exit 1
else
    echo "Script executed successfully. Opening result path in file explorer."

    # Open the result_path in the default file explorer
    xdg-open "$result_path"
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
