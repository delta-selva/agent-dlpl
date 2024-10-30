import sys
import os
import json
import subprocess
import time
import requests
from tkinter import messagebox
from tkinter import Tk
import psutil
from PIL import ImageGrab 
screenshot_counter = 0

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

def start_packet_capture(interface, capture_file, ip_address):
    print(f"Starting packet capture for IP: {ip_address} on interface: {interface}...")
    capture_process = subprocess.Popen(['sudo', 'tcpdump', '-i', interface, 'host', ip_address, '-w', capture_file])
    return capture_process

def stop_packet_capture(capture_process):
    capture_process.terminate()

def run_python_script(scan_id, ip_address, interface, result_path, window):
    try:
       
        capture_file = os.path.join(result_path, f"{scan_id}.pcap")
        capture_process = start_packet_capture(interface, capture_file, ip_address)
        time.sleep(5)
        screenshot_path_1 = capture_frame_screenshot(scan_id, result_path, window)
        if capture_process:
            print(f"Pinging {ip_address}...")
            ping_result = subprocess.run(['ping', '-c', '5', ip_address], capture_output=True, text=True)

            if ping_result.returncode == 0:
                print("Ping successful. Results:")
                print(ping_result.stdout)
            else:
                print("Ping failed. Error:")
                print(ping_result.stderr)

            result = {"ip_address": ip_address, "ping_result": ping_result.stdout}

            output_file = os.path.join(result_path, f"{scan_id}.json")
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=4)


            screenshot_path_2 = capture_frame_screenshot(scan_id, result_path, window)

            result["screenshot"] = screenshot_path_1
            result["final_screenshot"] = screenshot_path_2

            stop_packet_capture(capture_process)

            return {"json_file": output_file, "pcap_file": capture_file, "screenshot_file": screenshot_path_1, "final_screenshot": screenshot_path_2}
        else:
            print("Error: Packet capture process could not be started.")
            return None

    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")
        return None

    except FileNotFoundError:
        print("Error: Python interpreter not found. Please ensure Python is installed.")
        return None

def capture_frame_screenshot(scan_id, result_path, window):
  
    time.sleep(0.5)

 
    x = window.winfo_x()
    y = window.winfo_y()

    
    global screenshot_counter 
    screenshot_counter += 1

    x_offset = 300  
    y_offset = 150  
    height_offset = 150  

    area = (x + x_offset, y + y_offset, x + x_offset + 1400, y + y_offset + 600 + height_offset)

    
    screenshot_path = os.path.join(result_path, f"image_{screenshot_counter}.png")

    screenshot = ImageGrab.grab(bbox=area)
    screenshot.save(screenshot_path)  
    # print(f"Screenshot saved at {screenshot_path}")
    return screenshot_path


def main():
    if len(sys.argv) != 5:
        print("Usage: python3 test.py <scan_id> <result_path>")
        sys.exit(1)

    scan_id = sys.argv[1]
    result_path = sys.argv[2]
    interface = sys.argv[3]
    target_ip = sys.argv[4]

    window = Tk()
    window.geometry("800x600")
  

    result = run_python_script(scan_id, target_ip, interface,result_path, window)

    print(json.dumps(result))  

if __name__ == "__main__":
    main()
