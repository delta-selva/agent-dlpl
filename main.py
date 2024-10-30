import requests
import json
import gi
import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox,simpledialog
import zipfile
from PIL import Image, ImageTk 
import base64
import psutil
import sys
import tkinter.simpledialog

# GTK for terminal
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Vte, GLib, Gdk,GObject
import threading

class SimpleApp:    
    """Main Tkinter App that embeds GTK terminal"""
    config_file = 'client.conf.json'

    def __init__(self, root):
        self.root = root
        self.root.title(" ")
        self.root.configure(bg='#dfebf4')

        style = ttk.Style()
        style.configure('Custom.TButton', background='#145893', foreground='white', padding=10, borderwidth=0)
        style.map('Custom.TButton', background=[('active', '#0d5da3')]) 

        # Treeview Styles
        style.configure("Custom.Treeview", background="white", foreground="black")
        style.configure("Custom.Treeview.Heading", background="#145893", foreground="white", font=("Arial", 12, "bold"))

     
        # Set hover color for Treeview heading 
        style.map("Custom.Treeview.Heading", background=[('active', '#0d5da3')])  

        # Set hover color for Treeview rows
        style.map("Custom.Treeview", 
                  background=[('active', '#add8e6'), ('selected', '#add8e6')], 
                  foreground=[('active', 'black'), ('selected', 'black')]) 


        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}")
        self.root.resizable(True, True)

        self.input_frame = None
        self.details_frame = None
        self.dut_details = []
        self.agent_name = ""
        self.config_data = {}
        self.terminal_frame = None
        self.subtypes_dict = {}

        if self.load_configuration():
            self.get_eut_configuration(self.config_data["server_url"], self.config_data["token"])
        else:
            self.show_connection_window()
    
    def load_configuration(self):
        """Load server configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as file:
                try:
                    self.config_data = json.load(file)
                    if "server_url" in self.config_data and "token" in self.config_data:
                        return True
                except json.JSONDecodeError:
                    print("Warning: Configuration file is empty or corrupted.")
        return False

    def show_connection_window(self):
        """Show window for server connection"""
        if self.input_frame is not None:
            self.input_frame.destroy()

        # Create the main input frame centered in the window
        self.input_frame = tk.Frame(self.root, bg='#ffffff', padx=20, pady=20)
        self.input_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=600, height=250)

        # Server URL Label and Entry
        tk.Label(self.input_frame, text="Server URL:", bg='#ffffff', fg='#a6a6a6', font=("Arial", 14)).grid(row=0, column=0, sticky='w', padx=(20, 10), pady=(30, 5))
        self.url_entry = tk.Entry(self.input_frame, width=35, font=("Arial", 14))  
        self.url_entry.grid(row=0, column=1, padx=(10, 20), pady=(30, 5))  

        # API Key Label and Entry
        tk.Label(self.input_frame, text="API Key:", bg='#ffffff', fg='#a6a6a6', font=("Arial", 14)).grid(row=1, column=0, sticky='w', padx=(20, 10), pady=(15, 5))
        self.api_key_entry = tk.Entry(self.input_frame, show="*", width=35, font=("Arial", 14)) 
        self.api_key_entry.grid(row=1, column=1, padx=(10, 20), pady=(15, 5))

        # Connect Button with adjusted alignment
        # Center the button within the frame
        tk.Button(self.input_frame, text="Connect", command=self.connect_to_server, bg='#145893', fg='white', font=("Arial", 14), width=10, height=2).grid(row=2, column=0, columnspan=2, pady=20)

    def connect_to_server(self):
        """Connect to server and validate API key"""
        base_url = self.url_entry.get().strip()
        api_key = self.api_key_entry.get().strip()

        if not base_url:
            messagebox.showerror("Input Error", "Please enter the server URL.")
            return

        if not api_key:
            messagebox.showerror("Input Error", "Please enter an API key.")
            return

        try:
            if not base_url.endswith('/'):
                base_url += '/'
            validate_url = base_url + 'validate_key'
            
            request_data = {"api_key": api_key}

            # Try to connect to the server with API key (First-time connection)
            response = requests.post(validate_url, json=request_data)

            if response.status_code == 200:
                data = response.json()
                token = data.get("token")
                if token:
                    # After successful validation, save the configuration and fetch EUT config
                    self.save_configuration(base_url, token)
                    self.get_eut_configuration(base_url, token)
                else:
                    messagebox.showerror("Validation Error", "Server did not return a token.")
            elif response.status_code == 403:
                messagebox.showerror("Validation Error", "This API key has already been validated.")
            else:
                messagebox.showerror("Validation Error", f"Server returned status code {response.status_code}: {response.text}")

        except requests.RequestException as e:
            messagebox.showerror("Connection Error", f"Request error occurred: {e}")

    def save_configuration(self, base_url, token):
        """Save server URL and token to config file"""
        config = {
            "server_url": base_url,
            "token": token
        }

        with open(self.config_file, 'w') as file:
            json.dump(config, file)
        

    def get_eut_configuration(self, base_url, token):
        """Retrieve EUT configuration"""
        try:
            config_url = base_url + 'get_eut_configuration'
            request_data = {"token": token}

            response = requests.post(config_url, json=request_data)
            
            if response.status_code == 200:
                response_data = response.json()
                # print("159:response_data:", response_data)
                self.dut_details = response_data.get("data", [])
                # print("self.dut_details:",self.dut_details)
                self.agent_name = response_data.get("agent_name", "N/A")

                # After fetching EUT configuration, display the index page first
                self.index(base_url)
            else:
                if os.path.exists(self.config_file):
                    messagebox.showerror("Data Retrieval Error", f"Server returned status code {response.status_code}: {response.text}")
                else:
                    print("First-time connection, no error shown.")

        except requests.RequestException as e:
            messagebox.showerror("Connection Error", f"Request error occurred: {e}")

    def index(self, base_url):
        """Show the initial window with the file management system and sidebar."""
        try:
            self.base_url = base_url  
            self.selected_interface = None 
            self.target_ip = None 
            # Destroy previous frames if they exist
            if hasattr(self, 'input_frame') and self.input_frame is not None:
                self.input_frame.destroy()

            if hasattr(self, 'details_frame') and self.details_frame is not None:
                self.details_frame.destroy()

            if hasattr(self, 'menu_frame') and self.menu_frame is not None:
                self.menu_frame.destroy()  

            # Create a frame for the main content (on the right)
            self.input_frame = tk.Frame(self.root, bg=self.root['bg'], padx=20, pady=20)
            self.input_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

            self.show_dut_details(base_url)  

            # Custom menu bar using a frame
            self.menu_frame = tk.Frame(self.root, bg='#145893')  
            self.menu_frame.pack(side=tk.TOP, fill=tk.X)

            # File menu button
            file_menu_button = tk.Menubutton(self.menu_frame, text="File", bg='#145893', fg='white', font=("Arial", 12), 
                                            activebackground='#add8e6', activeforeground='black')
            file_menu_button.pack(side=tk.LEFT, padx=10)

            file_menu = tk.Menu(file_menu_button, tearoff=0, bg='#145893', fg='white', activebackground='#add8e6', activeforeground='black')

            # Test Case submenu
            self.test_case_menu = tk.Menu(file_menu, tearoff=0, bg='#145893', fg='white', activebackground='#add8e6', activeforeground='black')
            file_menu.add_cascade(label="Test Case", menu=self.test_case_menu)

            self.refresh_test_case_menu()  

            # Add separator and "Exit" command
            file_menu.add_separator()
            file_menu.add_command(label="Exit", command=self.root.quit)

            file_menu_button.config(menu=file_menu)

            # View menu
            view_menu_button = tk.Menubutton(self.menu_frame, text="View", bg='#145893', fg='white', font=("Arial", 12), 
                                            activebackground='#add8e6', activeforeground='black')
            view_menu_button.pack(side=tk.LEFT, padx=10)

            view_menu = tk.Menu(view_menu_button, tearoff=0, bg='#145893', fg='white', activebackground='#add8e6', activeforeground='black')
            view_menu.add_command(label="Full Screen", command=self.toggle_full_screen)
            view_menu_button.config(menu=view_menu)

            # New Interface menu
            interface_menu_button = tk.Menubutton(self.menu_frame, text="Interface", bg='#145893', fg='white', font=("Arial", 12),
                                                activebackground='#add8e6', activeforeground='black')
            interface_menu_button.pack(side=tk.LEFT, padx=10)

            interface_menu = tk.Menu(interface_menu_button, tearoff=0, bg='#145893', fg='white', activebackground='#add8e6', activeforeground='black')

            # Automatically list available network interfaces
            interfaces = self.list_interfaces()  

            # Populate the interface menu with the available options
            for iface in interfaces:
                interface_menu.add_command(label=iface, command=lambda i=iface: self.select_interface(i))

            interface_menu_button.config(menu=interface_menu)

            # New Target menu
            target_menu_button = tk.Button(self.menu_frame, text="Target", bg='#145893', fg='white', font=("Arial", 12),
                                activebackground='#add8e6', activeforeground='black', 
                                command=self.input_target_ip, bd=0, highlightthickness=0)
            target_menu_button.pack(side=tk.LEFT, padx=10)

            # Dynamically position agent name on the right side
            agent_label = tk.Label(self.menu_frame, text=f"Agent: {self.agent_name}", bg='#145893', fg='white', font=("Arial", 12))
            agent_label.pack(side=tk.RIGHT, padx=20)

        except Exception as e:
            print(f"Error in index: {e}")

    def input_target_ip(self):
        """Prompt the user to input a new target IP address."""
        ip_address = tkinter.simpledialog.askstring("Input New Target IP", "Enter the target IP address:")
        self.handle_target_ip(ip_address)  

    def handle_target_ip(self, ip_address):
        if ip_address:
            self.target_ip = ip_address
            print(f"Target IP set to: {self.target_ip}")

    def list_interfaces(self):
        """List available network interfaces for the user to select."""
        interfaces = psutil.net_if_addrs().keys()
        interfaces = list(interfaces)
        if not interfaces:
            print("No network interfaces found.")
            sys.exit(1)

        return interfaces

    def select_interface(self, interface):
        self.selected_interface = interface
        # print(f"Selected interface: {self.selected_interface}")


    def list_files_in_folder(self, folder_path):
            # print("folder_path:",folder_path)
            """List all files and folders in the specified folder."""
            if not os.path.exists(folder_path):
                return []

            try:
                items = os.listdir(folder_path)
                return items
            except Exception as e:
                messagebox.showerror("Error", f"Failed to list items: {e}")
                return []

    def refresh_test_case_menu(self):
        """Refresh the test case submenu with the list of files and folders."""
        self.test_case_menu.delete(0, 'end') 

        # Add "Create New Folder" option
        self.test_case_menu.add_command(label="Create New Folder", command=self.create_new_folder)

        # Set the test case folder path
        test_case_folder = os.path.join(".", "agents", self.agent_name)
        # print(test_case_folder, "253")
        
        # Get the list of items in the folder
        items = self.list_files_in_folder(test_case_folder)

        if items:
            for item in items:
                item_path = os.path.join(test_case_folder, item)
                if os.path.isdir(item_path):
                    # Add the folder name to the menu
                    self.test_case_menu.add_command(label=item, command=lambda i=item: self.open_folder(i))  
                else:
                    # Add menu items for files without any prefix
                    self.test_case_menu.add_command(label=item, command=lambda i=item: self.open_test_case_file(i))  
        else:
            self.test_case_menu.add_command(label="No items available", state="disabled")


    def show_context_menu(self, event, context_menu):
        """Display the context menu at the cursor position."""
        context_menu.post(event.x_root, event.y_root)

    def open_test_case_file(self, file_name):
        """Open the selected test case file."""
        test_case_folder = os.path.join(".", "agents", self.agent_name)
        file_path = os.path.join(test_case_folder, file_name)
        messagebox.showinfo("Open File", f"Opening: {file_path}")

    def open_folder(self, folder_name):
        """Open the selected folder and list its contents on a new page."""
        try:
            folder_path = os.path.join(".", "agents", self.agent_name, folder_name)

            # Get the list of items in the folder
            items = self.list_files_in_testcase(folder_path)
            
            # Show the folder contents on a new page
            self.show_folder_contents_page(folder_name, items)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")

        
    def show_folder_contents_page(self, folder_name, items):
        """Display the contents of the selected folder in a new window using a table."""
        try:
            # Destroy previous frames if they exist
            if hasattr(self, 'details_frame') and self.details_frame is not None:
                self.details_frame.destroy()

            # Create a new frame to display folder contents
            self.details_frame = tk.Frame(self.root, bg='#ffffff', padx=20, pady=20)
            self.details_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=800, height=600)

            # Create Treeview (table) with column definitions
            self.tree = ttk.Treeview(self.details_frame, columns=("File Name",), show='headings', height=10, style="Custom.Treeview")
            self.tree.heading("File Name", text=f"Test Cases in {folder_name}") 
            self.tree.column("File Name", width=600, anchor='w')

            # Insert file names into the Treeview
            if items:
                for item in items:
                    self.tree.insert("", tk.END, values=(item,))

            # Add Treeview to the grid
            self.tree.grid(row=1, column=0, padx=20, pady=(80, 10))
            self.details_frame.grid_columnconfigure(0, weight=1)

            # Create delete button (initially disabled)
            self.delete_button = ttk.Button(self.details_frame, text="Delete Selected", command=lambda: self.delete_selected_file(folder_name), style='Custom.TButton')
            self.delete_button["state"] = "disabled"

            # Position the button at the bottom-right corner
            self.delete_button.place(relx=1.0, rely=1.0, anchor='se', x=-20, y=-20)

            # Bind the selection event to enable the delete button
            self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

            # Load back icon and create back button
            back_icon = Image.open("static/assets/img/back_icon.png")

            back_icon = back_icon.resize((40, 40), Image.LANCZOS)
            back_icon = ImageTk.PhotoImage(back_icon)

            back_label = tk.Label(self.details_frame, image=back_icon, bg='#ffffff')
            back_label.image = back_icon  # Keep reference to avoid garbage collection
            back_label.place(x=10, y=10)

            # Bind click event to navigate back to the index method
            back_label.bind("<Button-1>", lambda e: self.index(self.base_url))

            # Test Case upload button
            self.upload_button = ttk.Button(self.details_frame, text="Upload Test Case", style='Custom.TButton',
                                            command=lambda: self.upload_file_to_agent_folder(folder_name))
            self.upload_button.place(relx=1.0, y=10, anchor='ne')

        except Exception as e:
            print(f"Error displaying folder contents: {e}")

    def on_tree_select(self, event):
        """Enable the delete button when an item is selected."""
        selected_item = self.tree.selection()
        if selected_item:
            self.delete_button["state"] = "normal"  # Enable the delete button
        else:
            self.delete_button["state"] = "disabled"  # Disable if nothing is selected
  
    def delete_selected_file(self, folder_name):
        """Delete the selected files or directories from the Treeview within the specified folder."""
        selected_items = self.tree.selection()  # Get all selected items
        
        if selected_items:
            folder_path = os.path.join(".", "agents", self.agent_name, folder_name)
            
            for selected_item in selected_items:
                item_text = self.tree.item(selected_item)["values"][0]  
                file_path = os.path.join(folder_path, item_text)  

                if os.path.exists(file_path):
                    try:
                        if os.path.isdir(file_path):
                            shutil.rmtree(file_path) 
                        else:
                            os.remove(file_path)  
                    except Exception as e:
                        print(f"Error deleting item {file_path}: {e}")
                else:
                    print(f"File or directory {file_path} does not exist.")
            
            # Refresh the Treeview after all deletions
            items = self.list_files_in_testcase(folder_path)  
            self.show_folder_contents_page(folder_name, items)  


    def list_files_in_testcase(self, folder_path):
        """List all files and folders in the specified folder."""
        if not os.path.exists(folder_path):
            messagebox.showerror("Directory Error", f"The folder does not exist: {folder_path}")
            return []

        try:
            items = os.listdir(folder_path)
            return items
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list items: {e}")
            return []


    def open_folder_file(self, file_name):
        """Open the selected test case file."""
        # Assuming the file is in the currently opened folder
        current_folder_path = os.path.join(".", "agents", self.agent_name)
        file_path = os.path.join(current_folder_path, file_name)
        
        # Replace this with the actual logic for opening a file
        if os.path.isfile(file_path):
            messagebox.showinfo("Open File", f"Opening: {file_path}")
            # Add your file opening logic here, e.g., with `os.startfile(file_path)` or other methods
        else:
            messagebox.showerror("File Error", f"The file does not exist: {file_path}")

        
    def delete_folder(self, folder_name):
        """Delete the selected folder."""
        folder_path = os.path.join(".", "agents", self.agent_name, folder_name)
        if os.path.exists(folder_path):
            os.rmdir(folder_path)
            messagebox.showinfo("Folder Deleted", f"Deleted: {folder_path}")
        self.refresh_test_case_menu()

    def create_new_folder(self):
        """Create a new folder."""
        folder_name = simpledialog.askstring("New Folder", "Enter folder name:")
        if folder_name:
            folder_path = os.path.join(".", "agents", self.agent_name, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            self.refresh_test_case_menu()

    def create_new_file(self):
        """Create a new file."""
        file_name = simpledialog.askstring("New File", "Enter file name:")
        if file_name:
            file_path = os.path.join(".", "agents", self.agent_name, file_name)
            open(file_path, 'w').close() 
            self.refresh_test_case_menu()


    def toggle_full_screen(self):
        """Toggle full-screen mode"""
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))


    def show_dut_details(self, base_url):
        """Show DUT and test case selection"""
        try:
            self.base_url = base_url 

            if hasattr(self, 'input_frame') and self.input_frame is not None:
                self.input_frame.destroy()

            # Destroy previous details frame if it exists
            if hasattr(self, 'details_frame') and self.details_frame is not None:
                self.details_frame.destroy()

            # Create details frame
            self.details_frame = tk.Frame(self.root, bg='#ffffff', padx=20, pady=20)
            self.details_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=800, height=400)
            
            # Add space at the top of the frame
            self.details_frame.grid_rowconfigure(0, minsize=100)  

            # Select project (optional UI, but we won't filter files by project name)
            dut_options = [dut['project_name'] for dut in self.dut_details]
            tk.Label(self.details_frame, text="Project Name:", bg='#ffffff', fg='#000000', font=("Arial", 14)).grid(row=1, column=0, sticky='w', padx=(80, 10), pady=(10, 5))
            self.dut_combobox = ttk.Combobox(self.details_frame, values=dut_options, width=50)
            self.dut_combobox.grid(row=1, column=1, padx=(10, 50), pady=(10, 5))

            # Select Test Case (list files from all folders under agent)
            tk.Label(self.details_frame, text="Test Case:", bg='#ffffff', fg='#000000', font=("Arial", 14)).grid(row=2, column=0, sticky='w', padx=(80, 10), pady=(10, 5))
            self.test_case_combobox = ttk.Combobox(self.details_frame, width=50)
            self.test_case_combobox.grid(row=2, column=1, padx=(10, 50), pady=(10, 5))

            # Get all test cases without filtering by project name
            test_cases = self.get_all_subfolders()
            self.test_case_combobox['values'] = test_cases

            # Submit button in center with top space
            self.details_frame.grid_rowconfigure(4, minsize=50)  # Add extra space before the button
            self.run_button = ttk.Button(self.details_frame, text="Submit", command=self.submit_and_display_test_case, style='Custom.TButton')

            # Add left-side space and center the button
            self.run_button.grid(row=5, column=0, columnspan=2, pady=20, padx=(100, 10)) 
            
        except Exception as e:
            print(f"Error in show_dut_details: {e}")

 
    def get_all_subfolders(self):
        """Get only the immediate subfolder names from all first-level directories."""
        agent_folder = os.path.join('./agents', self.agent_name)
        all_subfolders = []

        # Walk through the agent's directory
        for root, dirs, files in os.walk(agent_folder):
            for folder in dirs:
                # Get the full path of each first-level folder
                folder_path = os.path.join(agent_folder, folder)

                # Get the subfolders inside each first-level folder
                subfolders = next(os.walk(folder_path))[1]  # Only get the directory names
                
                # Add all subfolder names to the list
                all_subfolders.extend(subfolders)

            break  # Stop after the first-level folders are processed

        return all_subfolders


    def get_folder_contents(self, folder_name):
        """Get a list of files in the specified folder."""
        agent_folder = os.path.join('./agents', self.agent_name, folder_name)

        if os.path.exists(agent_folder):
            return os.listdir(agent_folder)  # List all files in the folder
        else:
            return []  # Return empty list if folder doesn't exist

    def upload_file_to_agent_folder(self, folder_name):
        """Handle file upload, store it in the agent's specific folder, and extract the zip file."""

        # Open file dialog to select a zip file
        file_path = filedialog.askopenfilename(
            title="Select a ZIP file to upload",
            filetypes=[("ZIP files", "*.zip")]
        )

       

        # Check if the selected file is a zip file
        if not file_path.endswith('.zip'):
            messagebox.showerror("File Error", "Please select a valid ZIP file.")
            return

        # Define the directory to save the file (Agent folder within the folder_name)
        agent_folder = os.path.join('./agents', self.agent_name, folder_name)

        # Create the agent folder if it doesn't exist
        if not os.path.exists(agent_folder):
            os.makedirs(agent_folder)

        # Get the destination path to save the ZIP file
        destination_path = os.path.join(agent_folder, os.path.basename(file_path))

        # Copy the selected file to the agent folder
        try:
            shutil.copy(file_path, destination_path)
           
        except Exception as e:
            messagebox.showerror("File Error", f"Failed to upload file: {e}")
            return

        # Extract the zip file in the agent folder
        try:
            # Extract the contents of the ZIP file directly into the folder_name folder
            with zipfile.ZipFile(destination_path, 'r') as zip_ref:
                zip_ref.extractall(agent_folder)  # Extracting to the agent folder within the folder_name

            # messagebox.showinfo("Success", f"File extracted successfully to {agent_folder}")
            
            # Optionally, remove the ZIP file after extraction
            os.remove(destination_path)

            # Refresh the folder contents after extraction
            updated_items = self.get_folder_contents(folder_name)
            self.show_folder_contents_page(folder_name, updated_items)

        except zipfile.BadZipFile:
            messagebox.showerror("Extraction Error", "The selected file is not a valid ZIP archive.")
        except Exception as e:
            messagebox.showerror("Extraction Error", f"Failed to extract the file: {e}")


    def submit_and_display_test_case(self):
        """Display test case details and open GTK terminal"""
        selected_dut = self.dut_combobox.get()
        selected_test_case = self.test_case_combobox.get()

        if not selected_dut or not selected_test_case:
            messagebox.showerror("Input Error", "Please select a DUT and a Test Case.")
            return
            # print(f"Selected DUT: {selected_dut}, Project Type: {selected_project_type}, Test Case: {selected_test_case}")

        # Use the stored base_url
        base_url = getattr(self, 'base_url', None)
        if base_url is None:
            messagebox.showerror("Configuration Error", "Server URL is missing from configuration.")
            return

        self.send_selection_to_server(base_url, selected_dut, selected_test_case)

        # Launch the GTK terminal window
        if self.details_frame is not None:
            self.details_frame.destroy()

        self.root.withdraw()


    def get_client_uid(self):
        """Fetch the client UID from the configuration file."""
        try:
            with open(self.config_file, 'r') as file:
                config = json.load(file)
                return config.get('token')
        except FileNotFoundError:
            print(f"Error: The configuration file {self.config_file} was not found.")
            return None
        except json.JSONDecodeError:
            print("Error: Failed to decode JSON from the configuration file.")
            return None

           
    def send_selection_to_server(self, base_url, selected_dut, selected_test_case):
        """Send the user's DUT, project type, and test case selection to the server and get scan_id."""
        # Prepare data for the request
        data = {
            'project': selected_dut,
            'test_case': selected_test_case
        }

        try:
            response = requests.post(base_url + '/create_scan_id', json=data)
            response.raise_for_status()

            response_data = response.json()

            scan_id = response_data.get('scan_id')
            repo_dir = response_data.get('repo_dir')
            username = response_data.get('ssh_username')
            password = response_data.get('ssh_password')
            project_type = response_data.get('project_type')
            dut_details = response_data.get('dut_details') 
            # print("DUT Details:", dut_details) 

            if scan_id and project_type:
                # Create folder paths
                folder_path = os.path.join(".", "agents", self.agent_name, project_type, selected_test_case)
                # print(f"Generated folder path: {folder_path}")

                # Generate result path
                result_path = os.path.join(".", "tmp", scan_id)  # Ensure this path is correct
                # print(f"Generated result path: {result_path}")
                img_dir = os.path.join(result_path, "img")
                dut_conf_dir = os.path.join(result_path, "dut_conf") 
                json_file_path = os.path.join(dut_conf_dir, "dut_details.json")

                # Ensure the result path exists
                os.makedirs(result_path, exist_ok=True)  
                os.makedirs(img_dir, exist_ok=True)
                os.makedirs(dut_conf_dir, exist_ok=True)

                # Extract only the required fields from the dut_details
                filtered_dut_details = {
                    "placeholders": {
                    "customer": dut_details.get("customer"),
                    "ModelNo": dut_details.get("model_no"),
                    "ProductName": dut_details.get("product_name"),
                    "manufacturer": dut_details.get("manufacturer"),
                    "serial_no": dut_details.get("serial_no"),
                    "software_version": dut_details.get("software_version"),
                    "product_no": dut_details.get("product_no"),
                    "hardware_version": dut_details.get("hardware_version")
                    },
                    "images": [
                        {
                            "word": "Picture1",
                            "image_path": os.path.join(img_dir, "front_img.png") 
                        },
                        {
                            "word": "Picture2",
                            "image_path": os.path.join(img_dir, "side_img.png") 
                        },
                        {
                            "word": "Picture3",
                            "image_path": os.path.join(img_dir, "port_img.png") 
                        }
                    ]
                }

                # Save the filtered DUT details to JSON inside the tmp folder
                with open(json_file_path, 'w') as json_file:
                    json.dump(filtered_dut_details, json_file, indent=4)
                # print(f"DUT details saved to {json_file_path}")

                # Save images to the img directory
                if dut_details.get("front_img"):
                    front_img_data = base64.b64decode(dut_details["front_img"])
                    with open(os.path.join(img_dir, "front_img.png"), 'wb') as front_img_file:
                        front_img_file.write(front_img_data)
                    # print("Front image saved.")

                if dut_details.get("side_img"):
                    side_img_data = base64.b64decode(dut_details["side_img"])
                    with open(os.path.join(img_dir, "side_img.png"), 'wb') as side_img_file:
                        side_img_file.write(side_img_data)
                    # print("Side image saved.")

                if dut_details.get("port_img"):
                    port_img_data = base64.b64decode(dut_details["port_img"])
                    with open(os.path.join(img_dir, "port_img.png"), 'wb') as port_img_file:
                        port_img_file.write(port_img_data)
                    # print("Port image saved.")

                # Start a new thread to open the terminal window and pass the folder
                terminal_thread = threading.Thread(target=self.open_terminal_window, args=(
                    scan_id, repo_dir, username, password, base_url, folder_path, result_path, self.agent_name))
                terminal_thread.start()
            else:
                print("Error: Server response did not include required fields.")

        except requests.HTTPError as e:
            print(f"Error: Unable to reach server {base_url}. Exception: {e}")

            # Show an error message with OK button using tkinter's messagebox
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            messagebox.showerror("Test Case Error", "Test case doesn't exist in this project. Please provide the correct test case.")

            # After user clicks OK, show DUT details
            self.show_dut_details()
        except requests.RequestException as e:
            print(f"Error: Unable to reach server {base_url}. Exception: {e}")

  
    def open_terminal_window(self, scan_id, repo_dir, username, password, base_url, folder_path, result_path, agent_name):
        """Open the terminal window."""

        self.root.withdraw()  # Hide the main window

        def on_terminal_close(*args):
            """Handle actions when the GTK terminal window closes."""
            self.root.deiconify()  # Show the main application window again
            Gtk.main_quit()
            # print("Terminal closed.")

        def run_gtk_terminal():
            # Create and show the terminal window directly
            terminal_window = TerminalApp(scan_id, repo_dir, username, password, base_url, folder_path, result_path, agent_name, on_terminal_close, interface=self.selected_interface, target_ip=self.target_ip)
            Gtk.main() # Ensure the terminal is visible
        threading.Thread(target=run_gtk_terminal, daemon=True).start()

        # Call this to update the DUT details as needed.
        self.show_dut_details(self.base_url)  # Refresh DUT details

class TerminalApp(Gtk.Window):
    """GTK-based embedded terminal"""
    def __init__(self, scan_id, repo_dir, username, password, base_url, folder_path, result_path,agent_name, on_terminal_close, interface, target_ip):
        super().__init__(title=" ")

        self.scan_id = scan_id
        self.password = password
        self.username = username
        
        self.repo_dir = repo_dir
        self.folder_path = folder_path
        self.result_path = result_path
        self.base_url = base_url
        self.agent_name=agent_name
        self.on_terminal_close = on_terminal_close
        self.interface = interface
        self.target_ip = target_ip
        # print("interface ,target_ip:",self.interface, self.target_ip  )
        
        # # Ensure the folder path exists before proceeding
        # if not os.path.exists(self.folder_path):
        #     print(f"Directory {self.folder_path} does not exist.")
        #     Gtk.main_quit()  # Exit the application if the directory does not exist
        #     return

        # # print("result_path & scan id", scan_id)
        # # Set window to full screen
        display = Gdk.Display.get_default()
        
        monitor = display.get_monitor(0)  # Get the first monitor
        geometry = monitor.get_geometry() 
        screen_width = geometry.width
        screen_height = geometry.height

        self.load_css()
        self.set_default_size(screen_width, screen_height)

        # Create a HeaderBar with a Close Button
        header = Gtk.HeaderBar(title=" ")
        # print("header:",header)
        header.set_show_close_button(True)  # Enable the close button in the header
        self.set_titlebar(header)

        # Main vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        # print("vbox:",vbox)
        vbox.set_halign(Gtk.Align.CENTER)
        vbox.set_valign(Gtk.Align.CENTER)
        vbox.set_hexpand(True)
        vbox.set_vexpand(True)
        self.add(vbox)

        # Frame to contain the terminal and label
        frame = Gtk.Frame()
        # print("frame:",frame)
        frame.set_border_width(10)
        frame.set_size_request(800, 600)  # Set the size of the frame
        vbox.pack_start(frame, True, True, 0)

        # Vertical box inside the frame
        frame_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        frame.add(frame_vbox)

        # Add a label and a close button to the frame inside an EventBox
        event_box = Gtk.EventBox()
        event_box.get_style_context().add_class('label-bg')
        frame_vbox.pack_start(event_box, False, False, 0)

        # Create a horizontal box (hbox) to contain both label and close button
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox.set_halign(Gtk.Align.FILL)  # Align the hbox to the center horizontally
        event_box.add(hbox)

        # Add the label to the hbox
        label = Gtk.Label(label=" ")
        label.set_halign(Gtk.Align.START)
        hbox.pack_start(label, False, False, 0)

        spacer = Gtk.Label()  # An empty label as a spacer
        hbox.pack_start(spacer, True, True, 0)
        
        # Add the Close button to the hbox
        # Create a button
        close_button = Gtk.Button()

        # Create an image with a close icon
        close_icon = Gtk.Image.new_from_icon_name("window-close", Gtk.IconSize.BUTTON)

        # Set the image to the button
        close_button.set_image(close_icon)

        # Connect the button click event to the exit function
        close_button.connect("clicked", self.on_process_exit)

        # Add styling if needed
        close_button.get_style_context().add_class('close-button')

        # Pack the button into the hbox
        hbox.pack_start(close_button, False, False, 0)


        # Create the terminal widget
        self.terminal = Vte.Terminal()
        self.terminal.set_size(80, 24)
        self.load_css()
       

        # Launch bash and execute commands
        self.terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            None,
            ["/bin/bash", "-c", self.get_bash_commands()],
            None,
            GLib.SpawnFlags.DEFAULT,
            None,
            self.folder_path,
        )
        self.terminal.connect("child-exited", self.on_process_exit)

        # Create a scrolled window to hold the terminal
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        scrolled_window.set_hexpand(True)
        scrolled_window.add(self.terminal)

        # Add the scrolled window to the frame's vertical box
        frame_vbox.pack_start(scrolled_window, True, True, 0)

        self.connect("destroy", self.on_terminal_close)
        self.show_all()

    def load_css(self):
        """Load and apply CSS style."""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path('static/assets/css/style.css')
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
    def get_bash_commands(self):
        """Generate a generalized bash script to execute inside the terminal for any test case."""
        return f"""
          
            # Construct the full path to the execute.sh script
            execute_script="{os.path.join(self.folder_path, 'execute.sh')}"

            # echo "execute_script path: $execute_script"

            # Check if execute.sh exists at the specified location
            if [ ! -f "$execute_script" ]; then
                echo "Error: execute.sh script not found at $execute_script"
                echo "Please verify the path and try again."
            else
                # Give execute permission to execute.sh
                chmod +x "$execute_script"

                # Run the execute script and capture output
                $execute_script "{self.scan_id}" "{self.folder_path}" "{self.result_path}" "{self.interface}" "{self.target_ip}"

                # Check if the script executed successfully
                if [ $? -ne 0 ]; then
                    echo "Error: The test script failed to run."
                  
               
                else
                    echo "Test script executed successfully."
                    # Send the results to the server
                    report_path="{self.result_path}"
                    username="{self.username}"
                    password="{self.password}"
                    repo_dir="{self.repo_dir}"
                fi
            fi
        
            # Wait indefinitely for manual terminal closure
            echo "Press any key to close the terminal..."
            read -n 1 -s -r -p ""
        """


    def on_process_exit(self, *args):
        """Close the terminal when the process ends and handle output."""
        self.destroy()  # Close the terminal window

        # Upload files via HTTP along with the repo_dir
        self.upload_files_via_http(self.result_path, self.repo_dir)

        # Prepare data to upload
        data_to_upload = {
            "agent_name": self.agent_name,
            "scan_id": self.scan_id,
        }
        # print("data_to_upload:", data_to_upload)

        # Call the method to upload metadata or results
        self.upload_results(data_to_upload)
        self.on_terminal_close()  # Call the callback function


    def upload_files_via_http(self, result_path, repo_dir):
        """Upload files from the result_path directory to the server via HTTP along with repo_dir."""
        url = f"{self.base_url}/upload_files"  # Server endpoint to upload files
        
        try:
            # Get all files from the result_path
            files_to_upload = []
            for filename in os.listdir(result_path):
                file_path = os.path.join(result_path, filename)
                if os.path.isfile(file_path):
                    files_to_upload.append(('files', (filename, open(file_path, 'rb'))))
            
            if files_to_upload:
                # print(f"Uploading {len(files_to_upload)} files to {url}")
                
                # Include repo_dir in the data
                data = {
                    'repo_dir': repo_dir  # Add repo_dir to the form data
                }

                # Make a POST request to upload the files and repo_dir
                response = requests.post(url, files=files_to_upload, data=data)
                response.raise_for_status()  # Check for HTTP errors

                # print("Files and repo_dir successfully uploaded to the server:", response.json())
            else:
                print("No files found in result_path to upload.")
        
        except requests.RequestException as e:
            print(f"Error uploading files to server {url}: {e}")
        

    def upload_results(self, data):
        """Send the metadata or result JSON output to the server at the /upload endpoint."""
        try:
            response = requests.post(f"{self.base_url}/upload", json=data)
            response.raise_for_status()  # Check for HTTP errors

            print("Data successfully sent to the server:", response.json())
        except requests.RequestException as e:
            print(f"Error sending data to server {self.base_url}/upload: {e}")


# Main application execution
if __name__ == "__main__":
    root = tk.Tk() 
    app = SimpleApp(root) 
    root.mainloop()
