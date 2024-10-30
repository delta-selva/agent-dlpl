import sys
import os
import json
import subprocess
import time
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

def start_packet_capture(interface, capture_file):
    try:
        # Start capturing packets on the specified interface using tcpdump
        capture_command = ['tcpdump', '-i', interface, '-w', capture_file]
        capture_process = subprocess.Popen(capture_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"Packet capture started on interface {interface}.")
        
        # Sleep for a short time to ensure tcpdump starts capturing
        time.sleep(2)
        
        return capture_process
    
    except Exception as e:
        print(f"Error starting packet capture: {e}")
        return None

def stop_packet_capture(capture_process):
    """Stops the packet capture process."""
    capture_process.terminate()
    capture_process.wait(timeout=2)
    print("Packet capture stopped.")

def run_python_script(scan_id, argum, interface, result_path):
    """Main function to execute network checks and manage packet capture."""
    try:
        # Start packet capture
        capture_file = os.path.join(result_path, f"{scan_id}.pcap")  # Save PCAP in the report path
        capture_process = start_packet_capture(interface, capture_file)
        time.sleep(5)  # Allow time for capturing packets

        if capture_process:
            # Execute ping command to the target IP address
            print(f"Pinging {argum[0]}...")
            ping_result1 = subprocess.run(['ping', '-c', '5', argum[0]], capture_output=True, text=True)
            ping_result2 = subprocess.run(['ping6', '-c', '5', argum[1]], capture_output=True, text=True)
            
            if ping_result1.returncode == 0 and ping_result2.returncode == 0:
                result = {
                    "status": "PASS",
                    "message": "IPv4 and IPv6 both are alive"
                }
            
            else:
                if ping_result1.returncode == 0:
                    if ping_result1.returncode == 0:
                        result = {
                        "status": "PASS",
                        "message": "Both IPv4 and IPv6 are Up"
                        }
                    else:
                        result = {
                        "status": "FAIL",
                        "message": "IPv4 address is live, But IPv6 is down"
                        }
                else:  
                    if ping_result2.returncode == 0:
                        result = {
                            "status": "FAIL",
                            "message": "IPv4 is down and IPv6 are UP"
                        }
                    else:
                        result = {
                        "status": "FAIL",
                        "message": "Both IPv4 and IPv6 are Down"
                        }
                    
            # Save the JSON output in the report path
            output_file = os.path.join(result_path, f"{scan_id}.json")  # Save JSON in the report path
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=4)
            # Stop packet capture
            stop_packet_capture(capture_process)

            # Return the paths of the output files
            return {"json_file": output_file, "pcap_file": capture_file}
        else:
            print("Error: Packet capture process could not be started.")
            return None

    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")
        return None

    except FileNotFoundError:
        print("Error: Python interpreter not found. Please ensure Python is installed.")
        return None    

def list_interfaces():
    """List available network interfaces for the user to select."""
    interfaces = psutil.net_if_addrs().keys()
    interfaces = list(interfaces)
    if not interfaces:
        print("No network interfaces found.")
        sys.exit(1)

    print("Available network interfaces:")
    for idx, iface in enumerate(interfaces, start=1):
        print(f"{idx}. {iface}")

    return interfaces

def prompt_for_interface(interfaces):
    """Prompt the user to select a network interface."""
    while True:
        try:
            choice = int(input(f"Please select a network interface (1-{len(interfaces)}): ")) - 1
            if 0 <= choice < len(interfaces):
                return interfaces[choice]
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def main():
    # Ensure that we received 2 arguments (script name + scan_id)
    if len(sys.argv) != 3:
        print("Usage: python3 test.py <scan_id> <result_path>")
        sys.exit(1)

    # Extract arguments from the command-line
    scan_id = sys.argv[1]
    result_path = sys.argv[2]

    interfaces = list_interfaces()  # Define this function elsewhere
    interface = prompt_for_interface(interfaces)  # Define this function elsewhere

    ipv4_address = input("Enter the target IPv4 address: ")
    ipv6_address = input("Enter the target IPv6 address: ")
    argum = [ipv4_address, ipv6_address]

    result = run_python_script(scan_id, argum, interface,result_path)
    print(result)
    print(json.dumps(result))  # Output the result as a JSON string
if __name__ == "__main__":
    main()

