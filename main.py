import asyncio
import threading
import struct
import time
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from bleak import BleakScanner, BleakClient
import datetime  # Added import for datetime

# UUIDs for the LYWSD02 device
TIME_SERVICE_UUID = 'ebe0ccb0-7a0a-4b0c-8a1a-6ff2997da3a6'
TIME_CHAR_UUID = 'ebe0ccb7-7a0a-4b0c-8a1a-6ff2997da3a6'
UNIT_CHAR_UUID = 'ebe0ccbe-7a0a-4b0c-8a1a-6ff2997da3a6'

class LYWSD02SyncApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LYWSD02 Clock Sync")
        self.create_widgets()
        self.all_devices = {}  # Key: MAC or UUID, Value: Device Info
        self.lywsd02_devices = {}
        self.other_devices = {}
        self.scanning = False
        self.client = None
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.start_loop, daemon=True).start()
        self.update_current_time()

    def create_widgets(self):
        # Frame for search bar
        search_frame = ttk.Frame(self.root)
        search_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(search_frame, text="Search Devices:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.filter_devices())
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Add Hyperlink for Instructions
        instructions_label = tk.Label(search_frame, text="Instructions", fg="blue", cursor="hand2", underline=True)
        instructions_label.pack(side="left", padx=5)
        instructions_label.bind("<Button-1>", lambda e: self.show_instructions())

        # Frame for scanning devices
        scan_frame = ttk.LabelFrame(self.root, text="Bluetooth Devices")
        scan_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Scan and Stop Scan buttons
        buttons_frame = ttk.Frame(scan_frame)
        buttons_frame.pack(pady=5)

        self.scan_10s_button = ttk.Button(buttons_frame, text="Scan for 10 Seconds", command=lambda: self.start_scan(duration=10))
        self.scan_10s_button.pack(side="left", padx=5)

        self.scan_continuous_button = ttk.Button(buttons_frame, text="Start Continuous Scan", command=lambda: self.start_scan(duration=None))
        self.scan_continuous_button.pack(side="left", padx=5)

        self.stop_scan_button = ttk.Button(buttons_frame, text="Stop Scanning", command=self.stop_scan, state='disabled')
        self.stop_scan_button.pack(side="left", padx=5)

        # Split the scan_frame into two sections
        devices_container = ttk.Frame(scan_frame)
        devices_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Frame for LYWSD02 Devices
        lywsd02_frame = ttk.LabelFrame(devices_container, text="LYWSD02 Devices")
        lywsd02_frame.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=5)

        self.lywsd02_listbox = tk.Listbox(lywsd02_frame, height=10)
        self.lywsd02_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Frame for Other Devices
        other_frame = ttk.LabelFrame(devices_container, text="Other Bluetooth Devices")
        other_frame.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)

        self.other_listbox = tk.Listbox(other_frame, height=10)
        self.other_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Frame for time settings
        time_frame = ttk.LabelFrame(self.root, text="Time Settings")
        time_frame.pack(fill="x", padx=10, pady=5)

        # Current Time Display
        self.current_time_label = ttk.Label(time_frame, text=f"Current Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.current_time_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=(5, 10))

        # Time Zone Entry
        ttk.Label(time_frame, text="Time Zone (UTC offset):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.time_zone_var = tk.IntVar(value=0)
        self.time_zone_entry = ttk.Entry(time_frame, textvariable=self.time_zone_var, width=5)
        self.time_zone_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(time_frame, text="(Range: -12 to +14)").grid(row=1, column=2, sticky="w")

        # Add 30-Minute Offset Checkbox
        self.offset_30min_var = tk.BooleanVar()
        self.offset_30min_check = ttk.Checkbutton(time_frame, text="Add 30-Minute Offset", variable=self.offset_30min_var)
        self.offset_30min_check.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        # Frame for unit settings
        unit_frame = ttk.LabelFrame(self.root, text="Temperature Unit")
        unit_frame.pack(fill="x", padx=10, pady=5)

        self.unit_var = tk.StringVar(value='C')
        self.unit_c_radio = ttk.Radiobutton(unit_frame, text="Celsius (C)", variable=self.unit_var, value='C')
        self.unit_f_radio = ttk.Radiobutton(unit_frame, text="Fahrenheit (F)", variable=self.unit_var, value='F')
        self.unit_c_radio.pack(anchor='w', padx=5, pady=2)
        self.unit_f_radio.pack(anchor='w', padx=5, pady=2)

        # Update button
        self.update_button = ttk.Button(self.root, text="Update Device", command=self.update_device)
        self.update_button.pack(pady=10)

        # Console/log area
        console_frame = ttk.LabelFrame(self.root, text="Console")
        console_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.console_text = tk.Text(console_frame, height=10, state='disabled')
        self.console_text.pack(fill="both", expand=True, padx=5, pady=5)

    def start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def log(self, message):
        self.console_text.config(state='normal')
        self.console_text.insert(tk.END, f"{message}\n")
        self.console_text.see(tk.END)
        self.console_text.config(state='disabled')

    def start_scan(self, duration=None):
        if not self.scanning:
            self.scanning = True
            self.scan_10s_button.config(state='disabled')
            self.scan_continuous_button.config(state='disabled')
            self.stop_scan_button.config(state='normal')
            if duration:
                self.log(f"Starting scan for {duration} seconds...")
            else:
                self.log("Starting continuous scan...")
            asyncio.run_coroutine_threadsafe(self.perform_scan(duration=duration), self.loop)

    def stop_scan(self):
        if self.scanning:
            self.scanning = False
            self.scan_10s_button.config(state='normal')
            self.scan_continuous_button.config(state='normal')
            self.stop_scan_button.config(state='disabled')
            self.log("Stopped scanning for Bluetooth devices.")

    async def perform_scan(self, duration=None):
        try:
            if duration:
                devices = await BleakScanner.discover(timeout=duration)
                await self.process_devices(devices)
                self.scanning = False
                self.scan_10s_button.config(state='normal')
                self.scan_continuous_button.config(state='normal')
                self.stop_scan_button.config(state='disabled')
                self.log(f"Completed {duration}-second scan.")
            else:
                while self.scanning:
                    devices = await BleakScanner.discover(timeout=5.0)
                    await self.process_devices(devices)
                    await asyncio.sleep(1)  # Small delay to prevent tight loop
        except Exception as e:
            self.log(f"Error during scanning: {e}")
            self.scanning = False
            self.scan_10s_button.config(state='normal')
            self.scan_continuous_button.config(state='normal')
            self.stop_scan_button.config(state='disabled')

    async def process_devices(self, devices):
        for device in devices:
            mac = device.address.upper()
            name = device.name if device.name else "Unknown"

            # Get service UUIDs from advertisement data
            service_uuids = device.metadata.get('uuids', [])
            # service_uuids_str = ", ".join(service_uuids) if service_uuids else "None"  # Removed UUIDs from display

            # Determine if the address is a MAC or UUID based on platform
            # macOS uses UUIDs as addresses, others use MAC addresses
            if sys.platform == "darwin":
                identifier = mac  # On macOS, device.address is a UUID
                address_type = "UUID"
            else:
                identifier = mac  # On Windows/Linux, device.address is a MAC
                address_type = "MAC"

            # Log the discovered device with its type
            self.log(f"Discovered {address_type}: {name} [{mac}]")

            if identifier not in self.all_devices:
                self.all_devices[identifier] = {
                    'name': name,
                    'address': mac,
                    # 'uuids': service_uuids_str  # Removed UUIDs from storage as they are not displayed
                }

                if "LYWSD02" in name:
                    self.lywsd02_devices[identifier] = self.all_devices[identifier]
                    display_text = f"{name} [{mac}]"
                    self.lywsd02_listbox.insert(tk.END, display_text)
                    self.log(f"Discovered LYWSD02 Device: {name} [{mac}]")
                else:
                    self.other_devices[identifier] = self.all_devices[identifier]
                    display_text = f"{name} [{mac}]"
                    self.other_listbox.insert(tk.END, display_text)
                    self.log(f"Discovered Device: {name} [{mac}]")
            else:
                # Device already exists; no need to add again
                pass

    def filter_devices(self):
        query = self.search_var.get().lower()

        # Clear listboxes
        self.lywsd02_listbox.delete(0, tk.END)
        self.other_listbox.delete(0, tk.END)

        # Filter LYWSD02 devices
        for device in self.lywsd02_devices.values():
            name = device['name'].lower()
            mac = device['address'].lower()
            if query in name or query in mac:
                display_text = f"{device['name']} [{device['address']}]"
                self.lywsd02_listbox.insert(tk.END, display_text)

        # Filter Other devices
        for device in self.other_devices.values():
            name = device['name'].lower()
            mac = device['address'].lower()
            if query in name or query in mac:
                display_text = f"{device['name']} [{device['address']}]"
                self.other_listbox.insert(tk.END, display_text)

    def get_selected_device(self):
        # Check LYWSD02 listbox first
        selected_indices = self.lywsd02_listbox.curselection()
        if selected_indices:
            index = selected_indices[0]
            device_info = list(self.lywsd02_devices.values())[index]
            return device_info

        # Check Other devices listbox
        selected_indices = self.other_listbox.curselection()
        if selected_indices:
            index = selected_indices[0]
            device_info = list(self.other_devices.values())[index]
            return device_info

        return None

    def update_device(self):
        device = self.get_selected_device()
        if not device:
            messagebox.showwarning("No Selection", "Please select a device to update.")
            return

        self.log(f"Selected device: {device['name']} [{device['address']}]")
        self.update_button.config(state='disabled')
        # Stop scanning if it's ongoing
        if self.scanning:
            self.scanning = False
            self.scan_10s_button.config(state='normal')
            self.scan_continuous_button.config(state='normal')
            self.stop_scan_button.config(state='disabled')
            self.log("Scanning stopped for device update.")

        asyncio.run_coroutine_threadsafe(self.perform_update(device), self.loop)

    async def perform_update(self, device):
        try:
            self.log("Connecting to device...")
            async with BleakClient(device['address']) as client:
                if not client.is_connected:
                    self.log("Failed to connect to the device.")
                    messagebox.showerror("Connection Error", "Failed to connect to the device.")
                    return
                self.log("Connected to the device.")

                # Sync time
                current_time = int(time.time())
                if self.offset_30min_var.get():
                    current_time += 30 * 60  # Add 30 minutes
                    self.log("Adding 30-minute offset to the current time.")

                time_zone = self.time_zone_var.get()
                if time_zone < -12 or time_zone > 14:
                    self.log("Invalid time zone. Must be between -12 and +14.")
                    messagebox.showerror("Invalid Time Zone", "Time zone must be between -12 and +14.")
                    return

                # Prepare time data (5 bytes)
                data = struct.pack('<I', current_time) + struct.pack('<b', time_zone)
                self.log(f"Writing time data: {data.hex()}")
                await client.write_gatt_char(TIME_CHAR_UUID, data)
                self.log("Time updated successfully.")

                # Update unit
                unit = self.unit_var.get()
                unit_value = 0 if unit == 'C' else 1
                self.log(f"Updating temperature unit to {'Celsius (C)' if unit == 'C' else 'Fahrenheit (F)'}.")
                
                try:
                    # Read current unit
                    unit_data = await client.read_gatt_char(UNIT_CHAR_UUID)
                    old_unit = 'C' if unit_data[0] == 0 else 'F'
                    self.log(f"Current unit: {old_unit}")
                except Exception as e:
                    self.log(f"Failed to read current unit: {e}")
                    old_unit = None

                if old_unit is not None and unit_value != unit_data[0]:
                    # Write new unit
                    await client.write_gatt_char(UNIT_CHAR_UUID, bytes([unit_value]))
                    self.log(f"Unit updated to {'Celsius (C)' if unit_value == 0 else 'Fahrenheit (F)'}.")
                elif old_unit is not None:
                    self.log("Unit is already set to the selected value.")
                else:
                    self.log("Skipping unit update due to read failure.")

                messagebox.showinfo("Success", "Device updated successfully.")
        except Exception as e:
            self.log(f"Error during update: {e}")
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self.update_button.config(state='normal')

    def show_instructions(self):
        instructions = (
            "LYWSD02 Clock Sync Instructions:\n\n"
            "1. **Scan for Devices:**\n"
            "   - Click 'Scan for 10 Seconds' to perform a quick scan.\n"
            "   - Click 'Start Continuous Scan' to continuously scan for devices until stopped.\n\n"
            "2. **Select a Device:**\n"
            "   - Choose your LYWSD02 device from the 'LYWSD02 Devices' list.\n\n"
            "3. **Configure Time Settings:**\n"
            "   - Set your UTC offset in the 'Time Zone' field.\n"
            "   - Optionally, check 'Add 30-Minute Offset' to add an additional 30 minutes to the current time.\n\n"
            "4. **Select Temperature Unit:**\n"
            "   - Choose between Celsius (C) and Fahrenheit (F).\n\n"
            "5. **Update Device:**\n"
            "   - Click 'Update Device' to synchronize time and update temperature unit on your LYWSD02 device.\n\n"
            "6. **Monitor Logs:**\n"
            "   - Use the 'Console' area to monitor scanning and updating processes.\n\n"
            "Ensure that your device is powered on and within range during scanning and updating."
        )
        # Create a new window for instructions
        instructions_window = tk.Toplevel(self.root)
        instructions_window.title("Instructions")
        instructions_window.geometry("500x400")
        instructions_text = tk.Text(instructions_window, wrap='word')
        instructions_text.pack(fill="both", expand=True, padx=10, pady=10)
        instructions_text.insert(tk.END, instructions)
        instructions_text.config(state='disabled')

    def update_current_time(self):
        try:
            # Get the current UTC time
            utc_now = datetime.datetime.utcnow()
            
            # Retrieve the UTC offset from the user input
            tz_offset = self.time_zone_var.get()
            
            # Validate the UTC offset
            if tz_offset < -12 or tz_offset > 14:
                display_offset = "Invalid UTC Offset"
                adjusted_time = utc_now
            else:
                # Check if the 30-minute offset is selected
                offset_minutes = 30 if self.offset_30min_var.get() else 0
                # Create a timedelta object for the offset
                delta = datetime.timedelta(hours=tz_offset, minutes=offset_minutes)
                # Calculate the adjusted time
                adjusted_time = utc_now + delta
                # Format the display string for UTC offset
                sign = "+" if tz_offset >= 0 else "-"
                display_offset = f"UTC{sign}{abs(tz_offset):02}:{offset_minutes:02}"
            
            # Format the adjusted time as a string
            current_time = adjusted_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Update the label with the adjusted time and UTC offset
            self.current_time_label.config(text=f"Current Time: {current_time} ({display_offset})")
        except Exception as e:
            # Handle any unexpected errors
            self.current_time_label.config(text=f"Current Time: Error ({e})")
        
        # Schedule the update to occur every second
        self.root.after(1000, self.update_current_time)
def main():
    root = tk.Tk()
    app = LYWSD02SyncApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
