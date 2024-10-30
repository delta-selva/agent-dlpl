#!/bin/bash

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Installing..."
    sudo apt-get update
    sudo apt-get install -y python3
else
    echo "Python 3 is already installed."
fi

# Check for pip (Python package installer)
if ! command -v pip3 &> /dev/null; then
    echo "pip is not installed. Installing..."
    sudo apt-get install -y python3-pip
else
    echo "pip is already installed."
fi

# Check for psutil and install if not present
if ! python3 -c "import psutil" &> /dev/null; then
    echo "psutil is not installed. Installing..."
    pip3 install psutil
else
    echo "psutil is already installed."
fi

# List of required packages
required_packages=(
    "wireshark-common"
    "python3"
)

# Update package lists
sudo apt-get update

# Function to check if a package is installed
is_package_installed() {
    dpkg -s "$1" &> /dev/null
}

# Loop through required packages
for package in "${required_packages[@]}"; do
    if ! is_package_installed "$package"; then
        echo "$package is not installed. Installing..."
        sudo apt-get install -y "$package"
    else
        echo "$package is already installed."
    fi
done

# Additional configuration for Wireshark (optional)
sudo dpkg-reconfigure wireshark-common
sudo adduser "$USER" wireshark

echo "Script execution completed."
