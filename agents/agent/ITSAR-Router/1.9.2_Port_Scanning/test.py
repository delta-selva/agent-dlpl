import sys
import os
import json
import subprocess
import time
import requests
from tkinter import messagebox
import psutil

def extract_token(config_file):
    """Extracts the token and server URL from the provided JSON configuration file."""
    try:
        with open(config_file, 'r') as file:
            data = json.load(file)
        server_url = data.get("server_url")
        token = data.get("token")
        # print("Token selva:", token)
        return server_url, token
    except Exception as e:
        print("Error occurred: {}".format(e))
        return None, None

def start_packet_capture(capture_file, ip_address):
    """Start packet capture using tcpdump."""
    try:
        capture_process = subprocess.Popen(
            ['sudo', 'tcpdump', '-i', 'any', 'host', ip_address, '-w', capture_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"Starting packet capture on {ip_address}, saving to {capture_file}")
        return capture_process
    except Exception as e:
        print(f"Failed to start packet capture: {e}")
        return None

def stop_packet_capture(capture_process):
    """Stop packet capture."""
    if capture_process:
        capture_process.terminate()
        print("Stopping packet capture.")


def list_nmap_options():
    """List Nmap command options for the user to select."""
    options = [
        "1. Basic TCP scan (nmap -Pn <ip_address>)",
        "2. Full TCP scan (nmap -Pn -p- <ip_address>)",
        "3. UDP scan (nmap -sU <ip_address>)"
    ]
    print("\nAvailable Nmap scan options:")
    for option in options:
        print(option)
    return options

def prompt_for_nmap_option():
    """Prompt the user to select an Nmap command option."""
    options = list_nmap_options()
    while True:
        try:
            choice = int(input(f"Select a scan option (1-{len(options)}): "))
            if 1 <= choice <= len(options):
                return choice
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def run_python_script(scan_id, ip_address, result_path):
    """Main function to execute network checks and manage packet capture."""
    try:
        # Start packet capture
        capture_file = os.path.join(result_path, f"{scan_id}.pcap")
        capture_process = start_packet_capture(capture_file, ip_address)
        time.sleep(5)

        if capture_process:
            print(f"Pinging {ip_address}...")
            ping_result = subprocess.run(['ping', '-c', '5', ip_address], capture_output=True, text=True)
            if ping_result.returncode == 0:
                print("Ping successful. Results:")
                print(ping_result.stdout)
            else:
                print("Ping failed. Error:")
                print(ping_result.stderr)

            # Allow user to select Nmap command
            nmap_choice = prompt_for_nmap_option()

            # Determine Nmap command based on user's choice
            if nmap_choice == 1:
                nmap_command = ['nmap', '-Pn', ip_address]
            elif nmap_choice == 2:
                nmap_command = ['nmap', '-Pn', '-p-', ip_address]
            elif nmap_choice == 3:
                nmap_command = ['nmap', '-sU', ip_address]
            
            # Execute Nmap command
            print(f"Running Nmap scan: {' '.join(nmap_command)}")
            nmap_result = subprocess.run(nmap_command, capture_output=True, text=True)

            # Save Nmap result to a text file
            nmap_output_file = os.path.join(result_path, f"{scan_id}.txt")
            with open(nmap_output_file, 'w') as f:
                if nmap_result.returncode == 0:
                    print("Nmap scan successful. Saving results to text file.")
                    f.write(nmap_result.stdout)
                else:
                    print("Nmap scan failed. Saving error output to text file.")
                    f.write(nmap_result.stderr)

            # Stop packet capture
            stop_packet_capture(capture_process)

            return {"txt_file": nmap_output_file, "pcap_file": capture_file}
        else:
            print("Error: Packet capture process could not be started.")
            return None

    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")
        return None

    except FileNotFoundError:
        print("Error: Python interpreter not found. Please ensure Python is installed.")
        return None
    
def main():
    # Ensure that we received 2 arguments (script name + scan_id)
    if len(sys.argv) != 3:
        print("Usage: python3 test.py <scan_id> <result_path>")
        sys.exit(1)

    # Extract arguments from the command-line
    scan_id = sys.argv[1]
    result_path = sys.argv[2]
    

    ip_address = input("Enter the target DUT IP address: ") 

    result = run_python_script(scan_id, ip_address, result_path)

   

    print(json.dumps(result))  # Output the result as a JSON string

if __name__ == "__main__":
    main()
